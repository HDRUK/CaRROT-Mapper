import os
from collections import defaultdict
from typing import Any, Dict, List

from django.db.models.query import QuerySet
from shared_code import blob_parser, helpers, omop_helpers
from shared_code.logger import logger
from shared_code.models import (
    ScanReportConceptContentType,
    ScanReportFieldDict,
    ScanReportValueDict,
)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shared_code.django_settings")
import django

django.setup()

from shared.data.models import (
    ScanReportConcept,
    ScanReportField,
    ScanReportTable,
    ScanReportValue,
)
from shared.data.omop import Concept
from shared_code import db

from .reuse import reuse_existing_field_concepts, reuse_existing_value_concepts


def _create_concepts(
    table_values: List[ScanReportValueDict],
) -> List[ScanReportConcept]:
    """
    Generate Concept entries ready for POSTing from a list of values.

    Args:
        table_values (List[Dict[str, Any]]): List of values to create concepts from.

    Returns:
        List[Dict[str, Any]]: List of Concept dictionaries.
    """
    concepts: List[ScanReportConcept] = []
    for concept in table_values:
        if concept["concept_id"] != -1:
            if isinstance(concept["concept_id"], list):
                for concept_id in concept["concept_id"]:
                    concept_instance = db.create_concept(
                        concept_id, concept["id"], ScanReportConceptContentType.VALUE
                    )
                    if concept_instance is not None:
                        concepts.append(concept_instance)
            else:
                if (
                    concept_instance := db.create_concept(
                        concept["concept_id"],
                        concept["id"],
                        ScanReportConceptContentType.VALUE,
                    )
                ) is not None:
                    concepts.append(concept_instance)

    return concepts


def _handle_concepts(
    entries_grouped_by_vocab: defaultdict[str | None, List[ScanReportValueDict]]
) -> None:
    """
    For each vocab, set "concept_id" and "standard_concept" in each entry in the vocab.
    Transforms the defaultdict inplace.

    For the case when vocab is None, set it to defaults.

    For other cases, get the concepts from the vocab via /omop/conceptsfilter under
    pagination.
    Then match these back to the originating values, setting "concept_id" and
    "standard_concept" in each case.
    Finally, we need to fix all entries where "standard_concept" != "S" using
    `find_standard_concept_batch()`. This may result in more than one standard
    concept for a single nonstandard concept, and so "concept_id" may be either an
    int or str, or a list of such.

    Args:
        entries_grouped_by_vocab: (defaultdict[str, List[Dict[str, Any]]]): Entries grouped by Vocab.

    Returns:
        None
    """
    for vocab, value in entries_grouped_by_vocab.items():
        if vocab is None:
            # Set to defaults, and skip all the remaining processing that a vocab would require
            _set_defaults_for_none_vocab(value)
        else:
            _process_concepts_for_vocab(vocab, value)


def _set_defaults_for_none_vocab(entries: List[ScanReportValueDict]) -> None:
    """
    Set default values for entries with none vocabulary.

    Args:
        entries (List[Dict[str, Any]]): A list of dictionaries representing the entries.

    Returns:
        None

    """
    for entry in entries:
        entry["concept_id"] = -1
        entry["standard_concept"] = None


def _process_concepts_for_vocab(vocab: str, entries: List[ScanReportValueDict]) -> None:
    """
    Process concepts for a specific vocabulary.

    Args:
        vocab (str): The vocabulary to process concepts for.
        entries (List[Dict[str, Any]]): A list of dictionaries representing the entries.

    Returns:
        None

    """
    logger.info(f"begin {vocab}")
    concept_vocab_content = _get_concepts_for_vocab(vocab, entries)

    logger.debug(
        f"Attempting to match {len(concept_vocab_content)} concepts to "
        f"{len(entries)} SRValues"
    )
    _match_concepts_to_entries(entries, concept_vocab_content)
    logger.debug("finished matching")
    _batch_process_non_standard_concepts(entries)


def _get_concepts_for_vocab(
    vocab: str, entries: List[ScanReportValueDict]
) -> List[Concept]:
    """
    Fetch concepts for a specific vocabulary.

    Args:
        vocab (str): The vocabulary to fetch concepts for.
        paginated_values (List[List[str]]): A paginated list of values.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries representing the fetched concepts.

    """
    concept_vocab_response: List[Concept] = []
    for i in entries:
        concepts = Concept.objects.filter(
            concept_code__in=i["value"], vocabulary_id__in=vocab
        ).all()
        concept_vocab_response.extend(concepts)
    return concept_vocab_response


def _match_concepts_to_entries(
    entries: List[ScanReportValueDict], concept_vocab_content: List[Concept]
) -> None:
    """
    Match concepts to entries.

    Remarks:
        Loop over all returned concepts, and match their concept_code and vocabulary_id with
        the full_value in the entries, and set the latter's
        concept_id and standard_concept with those values

    Args:
        entries (List[Dict[str, Any]]): A list of dictionaries representing the entries.
        concept_vocab_content (List[Dict[str, Any]]): A list of dictionaries representing the concept vocabulary content.

    Returns:
        None

    """
    for entry in entries:
        entry["concept_id"] = -1
        entry["standard_concept"] = None
        for returned_concept in concept_vocab_content:
            if str(entry["value"]) == str(returned_concept.concept_code):
                entry["concept_id"] = str(returned_concept.concept_id)
                entry["standard_concept"] = str(returned_concept.standard_concept)
                # exit inner loop early if we find a concept for this entry
                break


def _batch_process_non_standard_concepts(entries: List[ScanReportValueDict]) -> None:
    """
    Batch process non-standard concepts.

    Args:
        entries (List[Dict[str, Any]]): A list of dictionaries representing the entries.

    Returns:
        None
    """
    nonstandard_entries = [
        entry
        for entry in entries
        if entry["concept_id"] != -1 and entry["standard_concept"] != "S"
    ]
    logger.debug(
        f"finished selecting nonstandard concepts - selected "
        f"{len(nonstandard_entries)}"
    )
    batched_standard_concepts_map = omop_helpers.find_standard_concept_batch(
        nonstandard_entries
    )
    _update_entries_with_standard_concepts(entries, batched_standard_concepts_map)


def _update_entries_with_standard_concepts(
    entries: List[ScanReportValueDict], standard_concepts_map: Dict[str, Any]
) -> None:
    """
    Update entries with standard concepts.

    Remarks:
        batched_standard_concepts_map maps from an original concept id to
        a list of associated standard concepts. Use each item to update the
        relevant entry from entries[vocab].

    Args:
        entries (List[Dict[str, Any]]): A list of dictionaries representing the entries.
        standard_concepts_map (Dict[str, Any]): A dictionary mapping non-standard concepts to standard concepts.

    Returns:
        None

    Raises:
        RuntimeWarning: If the relevant entry's concept ID is None.
    """
    for nonstandard_concept, standard_concepts in standard_concepts_map.items():
        relevant_entry = helpers.get_by_concept_id(entries, nonstandard_concept)
        if relevant_entry is None:
            """
            This is the case where pairs_for_use contains an entry that
            doesn't have a counterpart in entries, so this
            should error or warn
            """
            raise RuntimeWarning
        elif isinstance(relevant_entry["concept_id"], (int, str)):
            relevant_entry["concept_id"] = standard_concepts


def _handle_table(table: ScanReportTable, vocab: Dict[str, Dict[str, str]]) -> None:
    """
    Handles Concept Creation on a table.

    Remarks:
        Works by transforming table_values, then generating concepts from them.

    Args:
        table (Dict[str, Any]): Table object to create for.
        vocab (Dict[str, Dict[str, str]]): Vocab dictionary.

    Returns:
        None
    """
    sr_values = ScanReportValue.objects.filter(
        scan_report_field__scan_report_table=table.pk
    ).all()
    table_values = convert_to_typed_dict(sr_values)

    sr_fields = ScanReportField.objects.filter(scan_report_table=table.pk).all()
    table_fields = convert(sr_fields)

    # Add vocab id to each entry from the vocab dict
    helpers.add_vocabulary_id_to_entries(table_values, vocab, table_fields, table.name)

    # group table_values by their vocabulary_id, for example:
    # ['LOINC': [ {'id': 512, 'value': '46457-8', ... 'vocabulary_id': 'LOINC' }]],
    entries_grouped_by_vocab = defaultdict(list)
    for entry in table_values:
        entries_grouped_by_vocab[entry["vocabulary_id"]].append(entry)

    _handle_concepts(entries_grouped_by_vocab)
    logger.debug("finished standard concepts lookup")

    # Remember that entries_grouped_by_vocab is just a view into table values
    # so changes to entries_grouped_by_vocab above are reflected when we access table_values.
    concepts = _create_concepts(table_values)

    # Bulk create Concepts
    logger.info(f"Creating {len(concepts)} concepts for table {table.name}")

    ScanReportConcept.objects.bulk_create(concepts)

    logger.info("Create concepts all finished")

    # handle reuse of concepts
    reuse_existing_field_concepts(table_fields)
    reuse_existing_value_concepts(table_values)


def main(msg: Dict[str, str]):
    """
    Processes a queue message.
    Unwraps the message content
    Gets the vocab_dictionary
    Runs the create concepts processes.

    Args:
        msg (Dict[str, str]): The message received from the orchestrator.
    """
    data_dictionary_blob = msg.pop("data_dictionary_blob")
    table_id = msg.pop("table_id")

    # get the table
    table = ScanReportTable.objects.get(pk=table_id)

    # get the vocab dictionary
    _, vocab_dictionary = blob_parser.get_data_dictionary(data_dictionary_blob)

    if vocab_dictionary is None:
        raise ValueError("vocab_dictionary is None.")
    else:
        _handle_table(table, vocab_dictionary)


def convert_to_typed_dict(
    table_values: QuerySet[ScanReportValue],
) -> List[ScanReportValueDict]:
    return [
        {
            "id": value.pk,
            "scan_report_field": value.scan_report_field,
            "value": value.value,
            "frequency": value.frequency,
            "concept_id": value.conceptID,
            "value_description": value.value_description,
        }
        for value in table_values
    ]


def convert(fields: QuerySet[ScanReportField]) -> List[ScanReportFieldDict]:
    return [{"id": field.pk, "name": field.name} for field in fields]
