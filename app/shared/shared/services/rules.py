from typing import List, Optional

from shared.data.models import (
    MappingRule,
    OmopField,
    OmopTable,
    ScanReport,
    ScanReportConcept,
    ScanReportField,
    ScanReportTable,
    ScanReportValue,
)

# allowed tables
m_allowed_tables = [
    "person",
    "measurement",
    "condition_occurrence",
    "observation",
    "drug_exposure",
    "procedure_occurrence",
    "specimen",
]

# look up of date-events in all the allowed (destination) tables
m_date_field_mapper = {
    "person": ["birth_datetime"],
    "condition_occurrence": ["condition_start_datetime", "condition_end_datetime"],
    "measurement": ["measurement_datetime"],
    "observation": ["observation_datetime"],
    "drug_exposure": ["drug_exposure_start_datetime", "drug_exposure_end_datetime"],
    "procedure_occurrence": ["procedure_datetime"],
    "specimen": ["specimen_datetime"],
}


def delete_mapping_rules(table_id: int) -> None:
    """
    Delete existing mapping rules related to a Scan Report Table.

    Args:
        table_id (int): The Id of the ScanReportTable to delete the rules for.

    Returns:
        None
    """
    rules = MappingRule.objects.all().filter(source_field__scan_report_table=table_id)

    rules.delete()


def find_existing_concepts(table_id: int) -> List[ScanReportConcept]:
    """
    Get ScanReportConcepts associated to a table.

    Args:
        table_id (int): Id of the ScanReportTable to filter by.

    Returns:
        A list of ScanReportConcept attached to the Table Id.
    """

    values = (
        ScanReportValue.objects.all()
        .filter(scan_report_field__scan_report_table=table_id)
        .filter(concepts__isnull=False)
        .distinct()
        .order_by("id")
    )

    # find ScanReportField associated to this table_id
    # that have at least one concept added to them
    fields = (
        ScanReportField.objects.all()
        .filter(scan_report_table=table_id)
        .filter(concepts__isnull=False)
        .distinct()
        .order_by("id")
    )

    # retrieve all value concepts
    all_concepts = [concept for obj in values for concept in obj.concepts.all()]
    # retrieve all field concepts
    all_concepts += [concept for obj in fields for concept in obj.concepts.all()]
    return all_concepts


def validate_person_id_and_date(source_table: ScanReportTable):
    """
    Check that the person_id and date_event is set on the table

    Args:
        source_table (ScanReportTable): The ScanReportTable to validate

    Returns:
        bool: True if both person_id and date_event are both set on the Table.
    """
    person_id_source_field = source_table.person_id

    if person_id_source_field is None:
        return False

    date_event_source_field = source_table.date_event
    return date_event_source_field is not None


def get_omop_field(destination_field: str, destination_table: Optional[str] = None):
    """
    Get the destination_field object, given a field name, and/or the table.

    Args:
      - destination_field (str) : the name of the destination field
      - [optional] destination_table (str) : the name of destination table, if known

    Returns:
      - OmopField : the destination field object
    """

    # if we haven't specified the table name
    if destination_table is None:
        # look up the field from the "allowed_tables"
        omop_field = OmopField.objects.filter(field=destination_field)

        if len(omop_field) > 1:
            return omop_field.filter(table__table__in=m_allowed_tables)[0]
        elif len(omop_field) == 0:
            return None
        else:
            return omop_field[0]

    else:
        # otherwise, if we know which table the field is in, use this to find the field
        omop_field = OmopField.objects.filter(table__table=destination_table).get(
            field=destination_field
        )
    return omop_field


def get_person_id_rule(
    scan_report: ScanReport,
    scan_report_concept: ScanReportConcept,
    source_table: ScanReportTable,
    destination_table: OmopTable,
) -> MappingRule:
    """
    Get the rule for person_id, given

    Args:
        - scan_report (ScanReport):
        - scan_report_concept (ScanReportConcept):
        - source_table (ScanReportTable):
        - destination_table (OmopTable):

    Returns:
        - MappingRule:
    """
    # look up what source_field for this table contains the person id
    person_id_source_field = source_table.person_id

    # get the associated OmopField Object (aka destination_table::person_id)
    person_id_omop_field = OmopField.objects.get(
        table=destination_table, field="person_id"
    )

    # create a new 1-1 rule
    rule_domain_person_id, created = MappingRule.objects.update_or_create(
        scan_report=scan_report,
        omop_field=person_id_omop_field,
        source_field=person_id_source_field,
        concept=scan_report_concept,
        approved=True,
    )
    # return the rule mapping
    return rule_domain_person_id


def get_date_rules(scan_report, scan_report_concept, source_table, destination_table):
    # !todo - need some checks for this
    date_event_source_field = source_table.date_event

    date_omop_fields = m_date_field_mapper[destination_table.table]
    # loop over all returned
    # most will return just one date event
    # in the case of condition_occurrence, it returns start and end
    date_rules = []
    for date_omop_field in date_omop_fields:
        # get the actual omop field object
        date_event_omop_field = OmopField.objects.get(
            table=destination_table, field=date_omop_field
        )

        # create a new 1-1 rule
        rule_domain_date_event, created = MappingRule.objects.update_or_create(
            scan_report=scan_report,
            omop_field=date_event_omop_field,
            source_field=date_event_source_field,
            concept=scan_report_concept,
            approved=True,
        )

        date_rules.append(rule_domain_date_event)

    return date_rules


def find_destination_table(concept: ScanReportConcept) -> Optional[OmopTable]:
    """
    Get the destination table for a given ScanReportConcept

    Args:
        concept (ScanReportConcept): The Concept to get the table for.

    Returns:
        destination_table (OmopTable): The destination table for the concept.
    """
    domain = concept.domain_id.lower()
    # get the omop field for the source_concept_id for this domain
    omop_field = get_omop_field(f"{domain}_source_concept_id")
    if omop_field is None:
        return None
    # start looking up what table we're looking at
    destination_table = omop_field.table

    if destination_table.table not in m_allowed_tables:
        return None
    return destination_table


def save_mapping_rules(concept: ScanReportConcept) -> bool:
    """
    Save mapping rules from a given ScanReportConcept

    function to save the rules
    Args:
       - concept (ScanReportConcept) : object containing the Concept and Link to source_value
    """
    content_object = concept.content_object
    if isinstance(content_object, ScanReportValue):
        scan_report_value = content_object
        source_field = scan_report_value.scan_report_field
    else:
        source_field = content_object

    scan_report = source_field.scan_report_table.scan_report

    concept = concept.concept

    # start looking up what table we're looking at
    destination_table = find_destination_table(concept)
    if destination_table is None:
        return False

    # get the omop field for the source_concept_id for this domain
    domain = concept.domain_id.lower()
    omop_field = get_omop_field(f"{domain}_source_concept_id")

    # obtain the source table
    source_table = source_field.scan_report_table

    # check whether the person_id and date events for this table are valid
    # if not, we dont want to create any rules for this concept
    if not validate_person_id_and_date(source_table):
        return False

    # create a person_id rule
    person_id_rule = get_person_id_rule(
        scan_report, concept, source_table, destination_table
    )
    rules = [person_id_rule]
    # create(potentially multiple) date_rules
    date_rules = get_date_rules(scan_report, concept, source_table, destination_table)
    rules += date_rules

    # create/update a model for the domain source_concept_id
    #  - for this destination_field and source_field
    #  - do_term_mapping is set to true:
    #    - all term mapping rules associated need to be applied
    rule_domain_source_concept_id, created = MappingRule.objects.update_or_create(
        scan_report=scan_report,
        omop_field=omop_field,
        source_field=source_field,
        concept=concept,
        approved=True,
    )
    rules.append(rule_domain_source_concept_id)

    # create/update a model for the domain concept_id
    #  - for this destination_field and source_field
    #  - do_term_mapping is set to true:
    #    - all term mapping rules associated need to be applied
    rule_domain_concept_id, created = MappingRule.objects.update_or_create(
        scan_report=scan_report,
        omop_field=get_omop_field(f"{domain}_concept_id"),
        source_field=source_field,
        concept=concept,
        approved=True,
    )
    rules.append(rule_domain_concept_id)

    # create/update a model for the domain source_value
    #  - for this destination_field and source_field
    #  - do_term_mapping is set to false
    rule_domain_source_value, created = MappingRule.objects.update_or_create(
        scan_report=scan_report,
        omop_field=get_omop_field(f"{domain}_source_value"),
        source_field=source_field,
        concept=concept,
        approved=True,
    )
    # add this new concept mapping
    # - the concept wont be used, because  do_term_mapping=False
    # - but we need to preserve the link,
    #   so when all associated concepts are deleted, the rule is deleted
    rules.append(rule_domain_source_value)

    if domain == "measurement":
        # create/update a model for the domain value_as_number
        #  - for this destination_field and source_field
        #  - do_term_mapping is set to false
        rule_domain_value_as_number, created = MappingRule.objects.update_or_create(
            scan_report=scan_report,
            omop_field=get_omop_field("value_as_number", "measurement"),
            source_field=source_field,
            concept=concept,
            approved=True,
        )
        rules.append(rule_domain_value_as_number)

    # now we are sure all rules have been created, we can save them safely
    for rule in rules:
        rule.save()

    return True


def refresh_mapping_rules(table_id: int):
    """
    TODO: Docs
    """
    delete_mapping_rules(table_id)

    concepts = find_existing_concepts(table_id)

    nconcepts = 0
    nbadconcepts = 0

    for concept in concepts:
        if save_mapping_rules(concept):
            nconcepts += 1
        else:
            nbadconcepts += 1
