from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from marshmallow import ValidationError

import parseur
from parseur import mailbox
from parseur.schemas.mailbox import MailboxReadSchema, Metadata


@patch("parseur.client.requests.get")
def test_list_mailboxes(mock_request, mailbox_list_data):
    # Arrange: mock paginated API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mailbox_list_data
    mock_request.return_value = mock_response

    # Parameters
    search = "invoices"
    order_by = parseur.MailboxOrderKey.DOCUMENT_COUNT
    ascending = False

    result = list(
        parseur.Mailbox.list(search=search, order_by=order_by, ascending=ascending)
    )

    # Assert: underlying HTTP call
    assert mock_request.called

    # Extract call
    args, kwargs = mock_request.call_args
    url = args[0]
    assert url.startswith("https://api.parseur.com/parser")

    # Check query parameters
    params = kwargs.get("params")
    assert params is not None
    assert params["search"] == search
    assert params["ordering"] == "-document_count"

    assert len(result) == len(mailbox_list_data["results"])
    mailbox1 = result[0]
    assert mailbox1.id == mailbox1["id"] == 153
    assert mailbox1.name == mailbox1["name"] == "Elevated Adorable Willet"
    assert (
        mailbox1.email_prefix == mailbox1["email_prefix"] == "elevated.adorable.willet"
    )
    assert (
        mailbox1.account_uuid
        == mailbox1["account_uuid"]
        == "acc_362f4ad34c3843fdb2b9b5f78b3a0203"
    )
    assert mailbox1.ai_engine == mailbox1["ai_engine"] == "GCP_AI_1"

    assert mailbox1.attachments_only == mailbox1["attachments_only"] is False
    assert mailbox1.process_attachments == mailbox1["process_attachments"] is True
    # advanced options (e.g. disable_deskew) are hidden: excluded from the result
    assert "disable_deskew" not in mailbox1
    assert mailbox1.even_pages == mailbox1["even_pages"] is True
    assert mailbox1.odd_pages == mailbox1["odd_pages"] is True
    assert mailbox1.retention_policy == mailbox1["retention_policy"] == 90
    assert (
        mailbox1.split_keywords
        == mailbox1["split_keywords"]
        == [
            {"is_before": True, "keyword": "toto"},
            {"is_before": False, "keyword": "titi"},
        ]
    )
    assert mailbox1.split_page == mailbox1["split_page"] == 2
    assert mailbox1.page_range_set == mailbox1["page_range_set"] == []
    assert (
        mailbox1.split_page_range_set
        == mailbox1["split_page_range_set"]
        == [{"start_index": 1, "end_index": 5}, {"start_index": 8, "end_index": None}]
    )

    assert mailbox1.template_count == mailbox1["template_count"] == 0
    assert mailbox1.webhook_count == mailbox1["webhook_count"] == 0
    assert mailbox1.parser_object_count == mailbox1["parser_object_count"] == 18

    assert mailbox1.document_count == mailbox1["document_count"] == 6
    assert (
        mailbox1.document_per_status_count
        == mailbox1["document_per_status_count"]
        == {
            "INCOMING": 0,
            "ANALYZING": 0,
            "PROGRESS": 0,
            "PARSEDOK": 5,
            "PARSEDKO": 0,
            "QUOTAEXC": 0,
            "SKIPPED": 0,
            "SPLIT": 1,
            "DELETED": 0,
            "EXPORTKO": 0,
            "TRANSKO": 0,
            "INVALID": 0,
        }
    )

    assert (
        mailbox1.last_activity
        == mailbox1["last_activity"]
        == datetime.fromisoformat("2025-07-03T06:17:44.269362+00:00")
    )
    assert (
        mailbox1.parser_object_set_last_modified
        == mailbox1["parser_object_set_last_modified"]
        == datetime.fromisoformat("2025-07-03T06:15:24.473802+00:00")
    )

    assert mailbox1.attachments_field == mailbox1["attachments_field"] is False
    assert (
        mailbox1.original_document_field == mailbox1["original_document_field"] is False
    )
    assert mailbox1.searchable_pdf_field == mailbox1["searchable_pdf_field"] is False
    assert mailbox1.headers_field == mailbox1["headers_field"] is False
    assert mailbox1.received_field == mailbox1["received_field"] is False
    assert mailbox1.received_date_field == mailbox1["received_date_field"] is False
    assert mailbox1.received_time_field == mailbox1["received_time_field"] is False
    assert mailbox1.processed_field == mailbox1["processed_field"] is False
    assert mailbox1.processed_date_field == mailbox1["processed_date_field"] is False
    assert mailbox1.processed_time_field == mailbox1["processed_time_field"] is False
    assert mailbox1.sender_field == mailbox1["sender_field"] is False
    assert mailbox1.sender_name_field == mailbox1["sender_name_field"] is False
    assert (
        mailbox1.split_page_range_field == mailbox1["split_page_range_field"] is False
    )
    assert mailbox1.split_parent_id_field == mailbox1["split_parent_id_field"] is False
    assert mailbox1.recipient_field == mailbox1["recipient_field"] is False
    assert mailbox1.to_field == mailbox1["to_field"] is False
    assert mailbox1.cc_field == mailbox1["cc_field"] is False
    assert mailbox1.bcc_field == mailbox1["bcc_field"] is False
    assert mailbox1.reply_to_field == mailbox1["reply_to_field"] is False
    assert (
        mailbox1.recipient_suffix_field == mailbox1["recipient_suffix_field"] is False
    )
    assert (
        mailbox1.original_recipient_field
        == mailbox1["original_recipient_field"]
        is False
    )
    assert mailbox1.subject_field == mailbox1["subject_field"] is False
    assert mailbox1.template_field == mailbox1["template_field"] is False
    assert mailbox1.html_document_field == mailbox1["html_document_field"] is False
    assert mailbox1.text_document_field == mailbox1["text_document_field"] is False
    assert mailbox1.content_field == mailbox1["content_field"] is False
    assert mailbox1.last_reply_field == mailbox1["last_reply_field"] is False
    assert mailbox1.document_id_field == mailbox1["document_id_field"] is False
    assert mailbox1.document_url_field == mailbox1["document_url_field"] is False
    assert (
        mailbox1.public_document_url_field
        == mailbox1["public_document_url_field"]
        is False
    )
    assert mailbox1.page_count_field == mailbox1["page_count_field"] is False
    assert mailbox1.credit_count_field == mailbox1["credit_count_field"] is False
    assert mailbox1.mailbox_id_field == mailbox1["mailbox_id_field"] is False
    assert mailbox1.parsing_engine_field == mailbox1["parsing_engine_field"] is False

    assert mailbox1.available_webhook_set == mailbox1["available_webhook_set"]
    assert len(mailbox1.available_webhook_set) == 9
    assert mailbox1.webhook_set == mailbox1["webhook_set"] == []

    assert (
        mailbox1.table_set
        == mailbox1["table_set"]
        == [
            {"id": "PF1406", "name": "vergleichsangebote_vermietung"},
            {"id": "PF1397", "name": "vergleichsangebote_verkauf"},
        ]
    )
    assert (
        mailbox1.allowed_extensions
        == mailbox1["allowed_extensions"]
        == [
            "bmp",
            "csv",
            "doc",
            "docx",
            "eml",
            "gif",
            "html",
            "ics",
            "jpg",
            "mbox",
            "msg",
            "ods",
            "odt",
            "pdf",
            "png",
            "rtf",
            "tif",
            "txt",
            "xhtml",
            "xls",
            "xlsm",
            "xlsx",
            "xml",
        ]
    )


@patch("parseur.client.requests.request")
def test_create_mailbox(mock_request, mailbox_data):
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = mailbox_data
    mock_request.return_value = mock_response

    result = parseur.Mailbox.create(name="My Mailbox", ai_engine="GCP_AI_2")

    assert mock_request.called
    args, kwargs = mock_request.call_args
    assert args[0] == "POST"
    assert args[1] == "https://api.parseur.com/parser"
    # identification_status defaults to REQUESTED on creation.
    assert kwargs["json"] == {
        "name": "My Mailbox",
        "ai_engine": "GCP_AI_2",
        "identification_status": "REQUESTED",
    }

    assert result.id == result["id"] == 120


@patch("parseur.client.requests.request")
def test_update_mailbox(mock_request, mailbox_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mailbox_data
    mock_request.return_value = mock_response

    result = parseur.Mailbox.update(120, name="Renamed")

    assert mock_request.called
    args, kwargs = mock_request.call_args
    assert args[0] == "PUT"
    assert args[1] == "https://api.parseur.com/parser/120"
    # id is included in the PUT body alongside the updated fields
    assert kwargs["json"] == {"name": "Renamed", "id": 120}

    assert result.id == result["id"] == 120


@patch("parseur.client.requests.request")
def test_split_by_ai(mock_request, mailbox_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mailbox_data
    mock_request.return_value = mock_response

    parseur.Mailbox.split_by_ai(120, instructions="one invoice per page")

    _, kwargs = mock_request.call_args
    assert kwargs["json"] == {
        "is_ai_split_enabled": True,
        "ai_split_instructions": "one invoice per page",
        "id": 120,
    }


@patch("parseur.client.requests.request")
def test_split_by_page(mock_request, mailbox_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mailbox_data
    mock_request.return_value = mock_response

    parseur.Mailbox.split_by_page(120, 2)

    _, kwargs = mock_request.call_args
    assert kwargs["json"] == {"split_page": 2, "id": 120}


@patch("parseur.client.requests.request")
def test_split_by_page_range(mock_request, mailbox_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mailbox_data
    mock_request.return_value = mock_response

    parseur.Mailbox.split_by_page_range(
        120,
        [{"start_index": 1, "end_index": 5}, {"start_index": 6, "end_index": None}],
    )

    _, kwargs = mock_request.call_args
    assert kwargs["json"] == {
        "split_page_range_set": [
            {"start_index": 1, "end_index": 5},
            {"start_index": 6, "end_index": None},
        ],
        "id": 120,
    }


@patch("parseur.client.requests.request")
def test_split_by_keywords(mock_request, mailbox_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mailbox_data
    mock_request.return_value = mock_response

    parseur.Mailbox.split_by_keywords(120, [{"keyword": "Invoice", "is_before": True}])

    _, kwargs = mock_request.call_args
    assert kwargs["json"] == {
        "split_keywords": [{"keyword": "Invoice", "is_before": True}],
        "id": 120,
    }


@patch("parseur.client.requests.request")
def test_process_page_range(mock_request, mailbox_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mailbox_data
    mock_request.return_value = mock_response

    parseur.Mailbox.process_page_range(120, [{"start_index": 1, "end_index": 3}])

    _, kwargs = mock_request.call_args
    assert kwargs["json"] == {
        "page_range_set": [{"start_index": 1, "end_index": 3}],
        "id": 120,
    }


@patch("parseur.client.requests.request")
def test_split_disable(mock_request, mailbox_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mailbox_data
    mock_request.return_value = mock_response

    parseur.Mailbox.split_by_ai(120, enabled=False)
    assert mock_request.call_args.kwargs["json"] == {
        "is_ai_split_enabled": False,
        "id": 120,
    }

    parseur.Mailbox.split_by_page(120, enabled=False)
    assert mock_request.call_args.kwargs["json"] == {"split_page": None, "id": 120}

    parseur.Mailbox.split_by_page_range(120, enabled=False)
    assert mock_request.call_args.kwargs["json"] == {
        "split_page_range_set": [],
        "id": 120,
    }

    parseur.Mailbox.split_by_keywords(120, enabled=False)
    assert mock_request.call_args.kwargs["json"] == {"split_keywords": [], "id": 120}

    parseur.Mailbox.process_page_range(120, enabled=False)
    assert mock_request.call_args.kwargs["json"] == {"page_range_set": [], "id": 120}


def test_enable_without_value_raises():
    with pytest.raises(ValueError):
        parseur.Mailbox.split_by_page(120)
    with pytest.raises(ValueError):
        parseur.Mailbox.split_by_keywords(120)
    with pytest.raises(ValueError):
        parseur.Mailbox.process_page_range(120)


@patch("parseur.client.requests.request")
def test_process_odd_even_pages(mock_request, mailbox_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mailbox_data
    mock_request.return_value = mock_response

    parseur.Mailbox.process_odd_pages(120)
    assert mock_request.call_args.kwargs["json"] == {"odd_pages": True, "id": 120}

    parseur.Mailbox.process_even_pages(120, enabled=False)
    assert mock_request.call_args.kwargs["json"] == {"even_pages": False, "id": 120}


@patch("parseur.client.requests.request")
def test_set_email_processing(mock_request, mailbox_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mailbox_data
    mock_request.return_value = mock_response

    parseur.Mailbox.set_email_processing(120, parseur.EmailProcessing.ATTACHMENTS_ONLY)
    assert mock_request.call_args.kwargs["json"] == {
        "process_attachments": True,
        "attachments_only": True,
        "id": 120,
    }

    # accepts the raw enum value too
    parseur.Mailbox.set_email_processing(120, "emails_only")
    assert mock_request.call_args.kwargs["json"] == {
        "process_attachments": False,
        "attachments_only": False,
        "id": 120,
    }

    parseur.Mailbox.set_email_processing(
        120, parseur.EmailProcessing.EMAILS_AND_ATTACHMENTS
    )
    assert mock_request.call_args.kwargs["json"] == {
        "process_attachments": True,
        "attachments_only": False,
        "id": 120,
    }


@patch("parseur.client.requests.request")
def test_set_metadata(mock_request, mailbox_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mailbox_data
    mock_request.return_value = mock_response

    parseur.Mailbox.set_metadata(
        120, enable=Metadata.SUBJECT | Metadata.SENDER, disable=Metadata.TO
    )

    _, kwargs = mock_request.call_args
    body = kwargs["json"]
    # enabled and disabled columns are toggled, untouched ones are absent
    assert body["subject_field"] is True
    assert body["sender_field"] is True
    assert body["to_field"] is False
    assert "attachments_field" not in body
    assert body["id"] == 120


def test_set_metadata_rejects_conflicting_columns():
    with pytest.raises(ValueError):
        parseur.Mailbox.set_metadata(
            120, enable=Metadata.SUBJECT, disable=Metadata.SUBJECT
        )


def test_advanced_options_are_hidden():
    from parseur.schemas.mailbox import MailboxWriteSchema

    hidden = {
        "force_ocr",
        "expand_result",
        "disable_document_links",
        "disable_deskew",
        "extract_xml_from_comment",
        "input_date_format_autodetection",
    }
    read_fields = set(MailboxReadSchema().fields)
    write_fields = set(MailboxWriteSchema().fields)

    # The advanced options are exposed neither on read nor on write.
    assert hidden & read_fields == set()
    assert hidden & write_fields == set()


def test_metadata_enum_drives_read_schema():
    # The read schema's ``*_field`` columns are generated from the Metadata enum,
    # so the two must cover exactly the same set.
    read_fields = {
        name for name in MailboxReadSchema().fields if name.endswith("_field")
    }
    assert {column.field for column in Metadata} == read_fields


@patch("parseur.client.requests.request")
def test_rename_and_ai_settings(mock_request, mailbox_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mailbox_data
    mock_request.return_value = mock_response

    parseur.Mailbox.rename(120, "Invoices")
    assert mock_request.call_args.kwargs["json"] == {"name": "Invoices", "id": 120}

    parseur.Mailbox.set_ai_engine(120, parseur.AIEngine.GCP_AI_2_5)
    assert mock_request.call_args.kwargs["json"] == {
        "ai_engine": "GCP_AI_2_5",
        "id": 120,
    }

    parseur.Mailbox.set_ai_instructions(120, "Extract totals")
    assert mock_request.call_args.kwargs["json"] == {
        "ai_instructions": "Extract totals",
        "id": 120,
    }

    parseur.Mailbox.set_ai_instructions(120, None)
    assert mock_request.call_args.kwargs["json"] == {
        "ai_instructions": None,
        "id": 120,
    }


@patch("parseur.client.requests.request")
def test_set_timezone(mock_request, mailbox_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mailbox_data
    mock_request.return_value = mock_response

    parseur.Mailbox.set_timezone(120, "Europe/Paris")
    assert mock_request.call_args.kwargs["json"] == {
        "default_timezone": "Europe/Paris",
        "id": 120,
    }

    # None clears it (the field is nullable)
    parseur.Mailbox.set_timezone(120, None)
    assert mock_request.call_args.kwargs["json"] == {
        "default_timezone": None,
        "id": 120,
    }


@patch("parseur.client.requests.request")
def test_set_date_format(mock_request, mailbox_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mailbox_data
    mock_request.return_value = mock_response

    parseur.Mailbox.set_date_format(120, parseur.DateFormat.DAY_FIRST)
    assert mock_request.call_args.kwargs["json"] == {
        "input_date_format": "DAY_FIRST",
        "id": 120,
    }

    # None clears the format
    parseur.Mailbox.set_date_format(120, None)
    assert mock_request.call_args.kwargs["json"] == {
        "input_date_format": None,
        "id": 120,
    }


@patch("parseur.client.requests.request")
def test_set_decimal_separator(mock_request, mailbox_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mailbox_data
    mock_request.return_value = mock_response

    parseur.Mailbox.set_decimal_separator(120, parseur.DecimalSeparator.COMMA)
    assert mock_request.call_args.kwargs["json"] == {
        "decimal_separator": ",",
        "id": 120,
    }

    parseur.Mailbox.set_decimal_separator(120, None)
    assert mock_request.call_args.kwargs["json"] == {
        "decimal_separator": None,
        "id": 120,
    }


@patch("parseur.client.requests.request")
def test_set_sender_filter(mock_request, mailbox_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mailbox_data
    mock_request.return_value = mock_response

    parseur.Mailbox.set_sender_filter(
        120, mailbox.SenderFilter.ALLOWLIST, ["acme.com", "billing@foo.com"]
    )
    assert mock_request.call_args.kwargs["json"] == {
        "use_whitelist_instead_of_blacklist": True,
        "emails_or_domains": ["acme.com", "billing@foo.com"],
        "id": 120,
    }

    parseur.Mailbox.set_sender_filter(120, mailbox.SenderFilter.BLOCKLIST, [])
    assert mock_request.call_args.kwargs["json"] == {
        "use_whitelist_instead_of_blacklist": False,
        "emails_or_domains": [],
        "id": 120,
    }


@patch("parseur.client.requests.request")
def test_set_allowed_extensions(mock_request, mailbox_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mailbox_data
    mock_request.return_value = mock_response

    parseur.Mailbox.set_allowed_extensions(120, ["pdf", "png"])

    _, kwargs = mock_request.call_args
    assert kwargs["json"] == {"allowed_extensions": ["pdf", "png"], "id": 120}


@patch("parseur.client.requests.request")
def test_set_allowed_extensions_rejects_unknown(mock_request):
    with pytest.raises(ValidationError):
        parseur.Mailbox.set_allowed_extensions(120, ["pdf", "exe"])
    assert not mock_request.called


@patch("parseur.client.requests.request")
def test_delete_mailbox(mock_request):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_request.return_value = mock_response

    success = parseur.Mailbox.delete(120)

    assert mock_request.called
    args, _ = mock_request.call_args
    assert args[0] == "DELETE"
    assert args[1] == "https://api.parseur.com/parser/120"
    assert success is True


@patch("parseur.client.requests.request")
def test_create_mailbox_serializes_nested_fields(mock_request, mailbox_data):
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = mailbox_data
    mock_request.return_value = mock_response

    parseur.Mailbox.create(
        name="Splitter",
        retention_policy=30,
        split_keywords=[{"is_before": True, "keyword": "INVOICE"}],
    )

    _, kwargs = mock_request.call_args
    body = kwargs["json"]
    assert body["name"] == "Splitter"
    assert body["retention_policy"] == 30
    assert body["split_keywords"] == [{"is_before": True, "keyword": "INVOICE"}]
    assert body["identification_status"] == "REQUESTED"


@patch("parseur.client.requests.request")
def test_create_mailbox_identification_status_can_be_overridden(
    mock_request, mailbox_data
):
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = mailbox_data
    mock_request.return_value = mock_response

    parseur.Mailbox.create(name="X", identification_status="MANUAL")

    _, kwargs = mock_request.call_args
    assert kwargs["json"]["identification_status"] == "MANUAL"


@patch("parseur.client.requests.request")
def test_create_mailbox_defaults_to_vision_engine(mock_request, mailbox_data):
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = mailbox_data
    mock_request.return_value = mock_response

    parseur.Mailbox.create(name="X")

    _, kwargs = mock_request.call_args
    assert kwargs["json"]["ai_engine"] == "GCP_AI_2"


@patch("parseur.client.requests.request")
def test_create_mailbox_ai_engine_can_be_overridden(mock_request, mailbox_data):
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = mailbox_data
    mock_request.return_value = mock_response

    parseur.Mailbox.create(name="X", ai_engine="GCP_AI_2_5")

    _, kwargs = mock_request.call_args
    assert kwargs["json"]["ai_engine"] == "GCP_AI_2_5"


@patch("parseur.client.requests.request")
def test_create_mailbox_with_fields_does_not_force_requested(
    mock_request, mailbox_data
):
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = mailbox_data
    mock_request.return_value = mock_response

    # Predefined fields must be extracted, so identification is NOT forced to
    # REQUESTED (which would put the mailbox in identification mode).
    parseur.Mailbox.create(
        name="X", parser_object_set=[{"name": "Total", "format": "NUMBER"}]
    )

    _, kwargs = mock_request.call_args
    assert "identification_status" not in kwargs["json"]


@patch("parseur.client.requests.request")
def test_create_mailbox_rejects_invalid_ai_engine(mock_request):
    with pytest.raises(ValidationError):
        parseur.Mailbox.create(name="X", ai_engine="NOT_AN_ENGINE")
    # The request is never sent when validation fails.
    assert not mock_request.called


@patch("parseur.client.requests.request")
def test_create_mailbox_rejects_unknown_field(mock_request):
    with pytest.raises(ValidationError):
        parseur.Mailbox.create(name="X", document_count=5)
    assert not mock_request.called


@patch("parseur.client.requests.request")
def test_update_mailbox_rejects_unknown_field(mock_request):
    with pytest.raises(ValidationError):
        parseur.Mailbox.update(120, naem="typo")
    assert not mock_request.called


@patch("parseur.client.requests.get")
@patch("parseur.client.requests.request")
def test_download_mailbox(mock_request, mock_get, mailbox_data):
    retrieve = MagicMock()
    retrieve.status_code = 200
    retrieve.json.return_value = mailbox_data
    mock_request.return_value = retrieve

    dl = MagicMock()
    dl.status_code = 200
    dl.content = b"InvoiceNumber,TotalDue\nINV-1,42\n"
    mock_get.return_value = dl

    content = parseur.Mailbox.download(120)

    assert content == b"InvoiceNumber,TotalDue\nINV-1,42\n"
    # the absolute (resolved) csv_download URL was fetched
    url = mock_get.call_args[0][0]
    assert url.startswith("https://api.parseur.com/parser/")
    assert url.endswith(".csv")


@patch("parseur.client.requests.get")
@patch("parseur.client.requests.request")
def test_download_mailbox_xlsx(mock_request, mock_get, mailbox_data):
    retrieve = MagicMock()
    retrieve.status_code = 200
    retrieve.json.return_value = mailbox_data
    mock_request.return_value = retrieve
    mock_get.return_value = MagicMock(status_code=200, content=b"...")

    parseur.Mailbox.download(120, "xlsx")

    assert mock_get.call_args[0][0].endswith(".xlsx")


@patch("parseur.client.requests.request")
def test_download_mailbox_rejects_bad_format(mock_request):
    with pytest.raises(ValueError):
        parseur.Mailbox.download(120, "pdf")
    assert not mock_request.called
