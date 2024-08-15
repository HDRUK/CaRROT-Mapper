import io
import json
import os
from datetime import datetime
from io import BytesIO
from typing import Dict

import azure.functions as func
from shared_code.models import FileHandlerConfig, RulesFileMessage

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shared_code.django_settings")
import django

django.setup()

from django.db.models.query import QuerySet  # type: ignore
from shared.data.models import MappingRule, ScanReport
from shared.files.models import FileDownload, FileType
from shared.files.service import upload_blob
from shared.services.rules_export import (
    get_mapping_rules_as_csv,
    get_mapping_rules_json,
    make_dag,
)


def create_json_rules(rules: QuerySet[MappingRule]) -> BytesIO:
    data = get_mapping_rules_json(rules)
    json_data = json.dumps(data)
    json_bytes = BytesIO(json_data.encode("utf-8"))
    json_bytes.seek(0)
    return json_bytes


def create_csv_rules(rules: QuerySet[MappingRule]) -> BytesIO:
    data = get_mapping_rules_as_csv(rules)
    return io.BytesIO(data.getvalue().encode("utf-8"))


def main(msg: func.QueueMessage) -> None:
    """
    Processes a queue message
    Unwraps the message content
    Gets the data
    Creates the file
    Saves the file to storage
    Creates the download model.

    Args:
        msg (func.QueueMessage): The message received from the queue.
    """
    # Unwrap message
    msg_body: RulesFileMessage = json.loads(msg.get_body().decode("utf-8"))
    scan_report_id = msg_body.get("scan_report_id")
    user_id = msg_body.get("user_id")
    file_type = msg_body.get("file_type")

    # Get models for this SR
    scan_report = ScanReport.objects.get(id=scan_report_id)
    rules = MappingRule.objects.filter(scan_report__id=scan_report_id).all()

    # Setup file config
    file_handlers: Dict[str, FileHandlerConfig] = {
        "text/csv": FileHandlerConfig(
            lambda rules: create_csv_rules(rules), "mapping_csv", "csv"
        ),
        "application/json": FileHandlerConfig(
            lambda rules: create_json_rules(rules), "mapping_json", "json"
        ),
        "image/svg+xml": FileHandlerConfig(
            lambda rules: make_dag(get_mapping_rules_json(rules)), "mapping_svg", "svg"
        ),
    }

    if file_type not in file_handlers:
        raise ValueError(f"Unsupported file type: {file_type}")

    config = file_handlers[file_type]

    # Generate it
    file = config.handler(rules)
    file_type_value = config.file_type_value
    file_extension = config.file_extension

    # Save to blob
    filename = f"Rules - {scan_report.dataset} - {scan_report_id} - {datetime.now()}.{file_extension}"
    upload_blob(filename, "rules-exports", file, file_type)

    # create entity
    file_type_entity = FileType.objects.get(value=file_type_value)
    file_entity = FileDownload.objects.create(
        name=filename,
        scan_report_id=scan_report_id,
        user_id=user_id,
        file_type=file_type_entity,
        file_url="",
    )
    file_entity.save()
