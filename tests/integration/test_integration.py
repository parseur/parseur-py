"""End-to-end integration tests against the real Parseur API.

These tests create and delete real resources (mailboxes, fields, webhooks,
documents) on the account the credentials belong to. They are skipped unless
``PARSEUR_API_KEY`` is set (see ``conftest.py``).

They double as a contract check: every response goes through the marshmallow
schemas, so a mismatch between the documented shape and the real API surfaces
as a ``ValidationError`` here.

Test order matters. Each test is independent (it creates and tears down its own
resources), but they are intentionally ordered from foundational to composite —
connectivity, then mailbox create/read/update, then parser fields, documents,
webhooks, and finally the full end-to-end parse + webhook. pytest runs tests in
definition order, so a low-level failure (e.g. ``Mailbox.create``) surfaces on
its own focused test first, before cascading into the fixture-based ones that
depend on it.
"""

import pathlib

import pytest

import parseur
from parseur import FieldFormat, ParseurEvent
from samples import parser_fields as pf
from samples.parser_fields import ALL_FORMAT_FIELDS

pytestmark = pytest.mark.integration

SAMPLES = pathlib.Path(__file__).resolve().parent.parent / "samples"


def _assert_invoice_parsed(result):
    """Assert the parsed result of sample.txt / sample.pdf covers all formats."""
    for field in ALL_FORMAT_FIELDS:
        assert field["name"] in result, f"missing field {field['name']}"

    # Scalars, one per format.
    assert result["InvoiceNumber"] == pf.INVOICE_NUMBER  # ONELINE
    assert result["InvoiceDate"] == pf.INVOICE_DATE  # DATE
    assert result["DueDate"] == pf.DUE_DATE  # DATE
    assert result["TotalDue"] == pf.TOTAL_DUE  # NUMBER
    assert result["AccountManager"]["full"] == pf.ACCOUNT_MANAGER  # NAME
    assert result["CustomerPortal"] == pf.PORTAL_LINK  # LINK

    # The line table: at least 10 rows, each with all six (non-nested) columns.
    rows = result["LineItems"]  # TABLE
    assert isinstance(rows, list)
    assert len(rows) == len(pf.LINE_ITEMS) >= 10
    expected_columns = {name for name, _ in pf.TABLE_COLUMNS}
    assert len(expected_columns) >= 6
    for row in rows:
        assert expected_columns <= set(row)
    first, expected = rows[0], pf.LINE_ITEMS[0]
    assert first["ItemCode"] == expected["ItemCode"]
    assert first["Description"] == expected["Description"]
    assert first["Quantity"] == expected["Quantity"]
    assert first["Amount"] == expected["Amount"]


# ------------------------
# Bootstrap / coherence
# ------------------------


def test_ai_engine_enum_matches_bootstrap(bootstrap):
    """The AIEngine enum must stay in sync with the real server choices."""
    server_choices = {choice[0] for choice in bootstrap["choices"]["parser.ai_engine"]}
    enum_values = {engine.value for engine in parseur.AIEngine}
    assert enum_values == server_choices


def test_supported_file_extensions_match_bootstrap(bootstrap):
    """SUPPORTED_FILE_EXTENSIONS must stay in sync with the real server list."""
    categories = bootstrap["choices"]["parser.supported_documents"]
    server_extensions = {
        ext for category in categories.values() for ext in category["extensions"]
    }
    assert set(parseur.SUPPORTED_FILE_EXTENSIONS) == server_extensions


# ------------------------
# Mailboxes (foundational write/read first)
# ------------------------


def test_create_mailbox_returns_valid_object(mailbox):
    assert isinstance(mailbox["id"], int)
    assert mailbox["name"].startswith("parseur-py integration")
    assert mailbox["email_prefix"]


def test_retrieve_mailbox(mailbox):
    fetched = parseur.Mailbox.retrieve(mailbox["id"])
    assert fetched["id"] == mailbox["id"]


def test_update_mailbox(mailbox):
    updated = parseur.Mailbox.update(mailbox["id"], name="renamed by integration test")
    assert updated["name"] == "renamed by integration test"


def test_mailbox_setting_helpers(mailbox):
    """The configuration helpers must be accepted by the real API and round-trip.

    Each helper goes through ``MailboxUpdateSchema`` on the way out and
    ``MailboxReadSchema`` on the way back, so this is a contract check for the
    writable settings surface.
    """
    from parseur import (
        AIEngine,
        DateFormat,
        DecimalSeparator,
        EmailProcessing,
        Metadata,
        SenderFilter,
    )

    mailbox_id = mailbox["id"]

    assert parseur.Mailbox.rename(mailbox_id, "renamed helper")["name"] == "renamed helper"
    assert (
        parseur.Mailbox.set_ai_engine(mailbox_id, AIEngine.GCP_AI_2_5)["ai_engine"]
        == "GCP_AI_2_5"
    )
    parseur.Mailbox.set_ai_instructions(mailbox_id, "extract the total")

    # Input formats
    assert (
        parseur.Mailbox.set_timezone(mailbox_id, "Europe/Paris")["default_timezone"]
        == "Europe/Paris"
    )
    assert (
        parseur.Mailbox.set_date_format(mailbox_id, DateFormat.DAY_FIRST)[
            "input_date_format"
        ]
        == "DAY_FIRST"
    )
    assert (
        parseur.Mailbox.set_decimal_separator(mailbox_id, DecimalSeparator.COMMA)[
            "decimal_separator"
        ]
        == ","
    )

    # Email intake
    updated = parseur.Mailbox.set_email_processing(
        mailbox_id, EmailProcessing.ATTACHMENTS_ONLY
    )
    assert updated["process_attachments"] is True
    assert updated["attachments_only"] is True

    updated = parseur.Mailbox.set_sender_filter(
        mailbox_id, SenderFilter.ALLOWLIST, ["acme.com"]
    )
    assert updated["use_whitelist_instead_of_blacklist"] is True
    assert updated["emails_or_domains"] == ["acme.com"]

    updated = parseur.Mailbox.set_allowed_extensions(mailbox_id, ["pdf", "png"])
    assert set(updated["allowed_extensions"]) == {"pdf", "png"}

    # Metadata columns
    updated = parseur.Mailbox.set_metadata(mailbox_id, enable=Metadata.SUBJECT)
    assert updated["subject_field"] is True

    # Page processing and splitting
    assert parseur.Mailbox.process_odd_pages(mailbox_id)["odd_pages"] is True
    assert parseur.Mailbox.split_by_page(mailbox_id, 2)["split_page"] == 2
    parseur.Mailbox.split_by_keywords(
        mailbox_id, [{"keyword": "Invoice", "is_before": True}]
    )


def test_mailbox_schema(mailbox):
    schema = parseur.Mailbox.schema(mailbox["id"])
    assert schema is not None


def test_list_mailboxes(mailbox):
    # Environment-agnostic: only assert about the mailbox we just created.
    found = parseur.Mailbox.list(search=mailbox["name"])
    assert any(m["id"] == mailbox["id"] for m in found)


# ------------------------
# Parser fields
# ------------------------


def test_parser_field_add_list_update_delete(mailbox):
    mailbox_id = mailbox["id"]

    # Add
    fields = parseur.ParserField.add(
        mailbox_id,
        name="Total",
        field_format=FieldFormat.NUMBER,
        query="the grand total",
    )
    added = next(f for f in fields if f["name"] == "Total")
    assert added["format"] == "NUMBER"
    field_id = added["id"]

    # List
    listed = parseur.ParserField.list(mailbox_id)
    assert any(f["id"] == field_id for f in listed)

    # Update
    updated = parseur.ParserField.update(mailbox_id, field_id, name="Grand Total")
    assert any(f["id"] == field_id and f["name"] == "Grand Total" for f in updated)

    # Delete
    remaining = parseur.ParserField.delete(mailbox_id, field_id)
    assert all(f["id"] != field_id for f in remaining)


def test_add_table_field_with_columns(mailbox):
    fields = parseur.ParserField.add(
        mailbox["id"],
        name="Line Items",
        field_format=FieldFormat.TABLE,
        parser_object_set=[
            {"name": "Description", "format": "TEXT"},
            {"name": "Amount", "format": "NUMBER"},
        ],
    )
    table = next(f for f in fields if f["name"] == "Line Items")
    assert table["format"] == "TABLE"
    assert {c["name"] for c in table["parser_object_set"]} == {"Description", "Amount"}


# ------------------------
# Documents
# ------------------------


@pytest.mark.parametrize("filename", ["sample.txt", "sample.pdf"])
def test_upload_file_parses_all_formats(mailbox_with_fields, filename):
    """Upload the text and PDF samples and check every format is parsed.

    Exercises the synchronous ``upload_file_and_wait`` helper.
    """
    doc = parseur.Document.upload_file_and_wait(
        mailbox_with_fields["id"], str(SAMPLES / filename)
    )
    assert doc["name"] == filename
    assert doc["status"] == "PARSEDOK"
    _assert_invoice_parsed(doc["result"])


def test_upload_text_and_list_documents(mailbox, bootstrap):
    recipient = f"{mailbox['email_prefix']}@{bootstrap['email_domain']}"
    upload = parseur.Document.upload_text(
        recipient=recipient,
        subject="parseur-py integration test",
        body_plain="Total: 42",
    )
    assert upload["DocumentID"]

    # Retrieving validates the uploaded document against DocumentSchema.
    doc = parseur.Document.retrieve(upload["DocumentID"])
    assert doc["id"]

    documents = parseur.Document.list(mailbox["id"])
    assert isinstance(documents, list)


# ------------------------
# Webhooks
# ------------------------


def test_webhook_lifecycle(mailbox):
    webhook = parseur.Webhook.create(
        event=ParseurEvent.DOCUMENT_PROCESSED,
        target_url="https://example.com/parseur-py-integration",
        mailbox_id=mailbox["id"],
        name="parseur-py integration webhook",
    )
    webhook_id = webhook["id"]

    try:
        fetched = parseur.Webhook.retrieve(webhook_id)
        assert fetched["id"] == webhook_id

        all_webhooks = parseur.Webhook.list()
        assert any(w["id"] == webhook_id for w in all_webhooks)

        parseur.Webhook.enable(mailbox["id"], webhook_id)
        parseur.Webhook.pause(mailbox["id"], webhook_id)
    finally:
        assert parseur.Webhook.delete(webhook_id) is True


# ------------------------
# Export configs
# ------------------------


def test_export_config_lifecycle(mailbox_with_fields):
    """Configure an export, list/retrieve it, download it, then delete it."""
    mailbox_id = mailbox_with_fields["id"]

    # A parsed document is needed for export fields to exist.
    parseur.Document.upload_file_and_wait(mailbox_id, str(SAMPLES / "sample.pdf"))

    groups = parseur.ExportConfig.available_fields(mailbox_id)
    parser_group = next(g for g in groups if g["type"] == "PARSER")
    items = parser_group["items"][:3]

    config = parseur.ExportConfig.create(mailbox_id, "integration export", items)
    config_id = config["id"]
    try:
        assert config["items"] == items
        assert config["csv_download"].startswith("http")

        listed = parseur.ExportConfig.list(mailbox_id)
        assert any(c["id"] == config_id for c in listed)

        updated = parseur.ExportConfig.update(mailbox_id, config_id, name="renamed")
        assert updated["name"] == "renamed"

        # Download the actual CSV export and check its header.
        content = parseur.ExportConfig.download(mailbox_id, config_id)
        header = content.split(b"\n")[0].decode()
        assert items[0] in header
    finally:
        assert parseur.ExportConfig.delete(mailbox_id, config_id) is True


def test_download_mailbox_and_table_results(mailbox_with_fields):
    """Download a mailbox's results and one table field's rows as files."""
    mailbox_id = mailbox_with_fields["id"]

    # A parsed document gives both exports something to return.
    parseur.Document.upload_file_and_wait(mailbox_id, str(SAMPLES / "sample.pdf"))

    # Mailbox-level export: one row per document, the scalar fields as columns.
    mailbox_csv = parseur.Mailbox.download(mailbox_id).decode()
    assert "InvoiceNumber" in mailbox_csv.split("\n")[0]

    # Table-level export: one row per line item, the table columns as columns.
    table = next(
        f for f in parseur.ParserField.list(mailbox_id) if f["format"] == "TABLE"
    )
    table_csv = parseur.ParserField.download(mailbox_id, table["id"]).decode()
    assert "ItemCode" in table_csv.split("\n")[0]


# ------------------------
# End-to-end: parse a document and fire its webhook
# ------------------------


def test_webhook_is_called_and_document_is_parsed(mailbox_with_fields):
    """End-to-end: the all-format mailbox parses ``sample.txt`` and the attached
    webhook is called."""
    mailbox = mailbox_with_fields

    # The fields cover every format, including a non-nested table.
    field_formats = {f["format"] for f in mailbox["parser_object_set"]}
    assert {fmt.value for fmt in FieldFormat} <= field_formats

    webhook = parseur.Webhook.create(
        event=ParseurEvent.DOCUMENT_PROCESSED,
        target_url="https://example.com/parseur-py-e2e",
        mailbox_id=mailbox["id"],
        name="parseur-py e2e",
    )
    try:
        doc = parseur.Document.upload_file_and_wait(
            mailbox["id"], str(SAMPLES / "sample.txt")
        )
        _assert_invoice_parsed(doc["result"])

        # The webhook was called: Parseur logs a REQUEST entry naming the target.
        logs = parseur.Document.logs(doc["id"])
        request_logs = [log for log in logs if log.get("code") == "REQUEST"]
        assert request_logs, "no webhook delivery (REQUEST) log found"
        assert "example.com/parseur-py-e2e" in request_logs[0]["message"]
    finally:
        parseur.Webhook.delete(webhook["id"])
