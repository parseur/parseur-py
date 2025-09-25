from datetime import datetime
from unittest.mock import MagicMock, patch

import parseur


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
    assert mailbox1.disable_deskew == mailbox1["disable_deskew"] is False
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
