Parseur Python Client API
==========================

This library provides a Python client and CLI to interact with the Parseur.com API.

Installation
------------

.. code-block:: bash

   pip install parseur-py

Quick Start
-----------

.. code-block:: python

   import parseur

   parseur.api_key = "YOUR_API_KEY"

   for mailbox in parseur.Mailbox.list():
      print(mailbox["name"])


Configuration
-------------

The CLI can save and load configuration from a file:

- By default: ``~/.parseur.conf``
- Fields:
    - **api_key**: Your Parseur API token
    - **api_base**: (Optional) Override the Parseur API base URL

Example:

.. code-block:: bash

   parseur init --api-key YOUR_API_TOKEN

Overview
--------


API Key
+++++++

Set a global API key once:

.. code-block:: python

   import parseur

   parseur.api_key = "YOUR_API_KEY"

Every API method also accepts an ``api_key`` keyword argument that **takes
priority over the global one** for that single call. This is handy for
multi-account or multi-tenant usage:

.. code-block:: python

   parseur.Mailbox.list(api_key="sk_account_a")
   parseur.Document.upload_file(123, "invoice.pdf", api_key="sk_account_b")
   parseur.ParserField.add(123, "Total", parseur.FieldFormat.NUMBER, api_key="sk_account_b")


Enums
+++++

ParseurEvent
^^^^^^^^^^^^

Supported webhook events:

.. code-block:: python

   from parseur import ParseurEvent

   ParseurEvent.DOCUMENT_PROCESSED
   ParseurEvent.TABLE_PROCESSED

DocumentOrderKey
^^^^^^^^^^^^^^^^

Used to sort documents:

.. code-block:: python

   from parseur import DocumentOrderKey

   DocumentOrderKey.NAME
   DocumentOrderKey.CREATED
   DocumentOrderKey.PROCESSED
   DocumentOrderKey.STATUS

MailboxOrderKey
^^^^^^^^^^^^^^^

Used to sort mailboxes:

.. code-block:: python

   from parseur import MailboxOrderKey

   MailboxOrderKey.NAME
   MailboxOrderKey.DOCUMENT_COUNT
   MailboxOrderKey.TEMPLATE_COUNT
   MailboxOrderKey.PARSEDOK_COUNT

DocumentStatus
^^^^^^^^^^^^^^

Document processing status:

.. code-block:: python

   from parseur import DocumentStatus

   DocumentStatus.INCOMING
   DocumentStatus.PARSEDOK
   DocumentStatus.EXPORTKO

AIEngine
^^^^^^^^

AI engine accepted when creating/updating a mailbox:

.. code-block:: python

   from parseur import AIEngine

   AIEngine.DISABLED      # Disabled (template-based parsing only)
   AIEngine.GCP_AI_2_5    # AI Text engine v2.5
   AIEngine.GCP_AI_3_TXT  # AI Text engine v3
   AIEngine.GCP_AI_2      # AI Vision engine v3

FieldFormat
^^^^^^^^^^^

Format of a parser field:

.. code-block:: python

   from parseur import FieldFormat

   FieldFormat.TEXT
   FieldFormat.NUMBER
   FieldFormat.DATE
   FieldFormat.TABLE

ExportType
^^^^^^^^^^

Type of an export configuration:

.. code-block:: python

   from parseur import ExportType

   ExportType.PARSER        # document-level export
   ExportType.PARSER_FIELD  # a table field's rows

EmailProcessing
^^^^^^^^^^^^^^^

How a mailbox processes incoming emails and attachments:

.. code-block:: python

   from parseur import EmailProcessing

   EmailProcessing.EMAILS_AND_ATTACHMENTS  # process both
   EmailProcessing.EMAILS_ONLY             # skip attachments
   EmailProcessing.ATTACHMENTS_ONLY        # skip the email body

DateFormat
^^^^^^^^^^

How to read ambiguous dates in documents:

.. code-block:: python

   from parseur import DateFormat

   DateFormat.MONTH_FIRST  # mm/dd/yyyy
   DateFormat.DAY_FIRST    # dd/mm/yyyy

DecimalSeparator
^^^^^^^^^^^^^^^^

Decimal separator for numbers in documents:

.. code-block:: python

   from parseur import DecimalSeparator

   DecimalSeparator.DOT    # 123.45
   DecimalSeparator.COMMA  # 123,45

SenderFilter
^^^^^^^^^^^^

How a mailbox filters incoming senders:

.. code-block:: python

   from parseur import SenderFilter

   SenderFilter.ALLOWLIST  # only the listed emails/domains are accepted
   SenderFilter.BLOCKLIST  # the listed emails/domains are rejected

Metadata
^^^^^^^^

Per-document metadata columns a mailbox can expose. An ``IntFlag``, so columns
compose with ``|`` (see :meth:`Mailbox.set_metadata`):

.. code-block:: python

   from parseur import Metadata

   Metadata.SUBJECT | Metadata.SENDER | Metadata.RECEIVED
   # other members: ATTACHMENTS, CC, BCC, TO, DOCUMENT_URL, PAGE_COUNT, ... (37 total)


Methods
+++++++

Mailboxes
^^^^^^^^^

- List all mailboxes, with optional search and sorting.

  - *search*: filter by mailbox name or email prefix
  - *order_by*: MailboxOrderKey
  - *ascending*: bool

  .. code-block:: python

     mailboxes = parseur.Mailbox.list(search="Invoices", order_by=MailboxOrderKey.NAME)
     for m in mailboxes:
         print(m)

- Get details of a mailbox.

  .. code-block:: python

     mailbox = parseur.Mailbox.retrieve(mailbox_id=123)
     print(mailbox)

- Get the schema of a mailbox.

  .. code-block:: python

     schema = parseur.Mailbox.schema(mailbox_id=123)
     print(schema)

- Download every parsed result of the mailbox as a single file (one row per
  processed document). Returns the file content as bytes.

  .. code-block:: python

     csv_bytes = parseur.Mailbox.download(123)            # CSV (default)
     json_bytes = parseur.Mailbox.download(123, "json")   # JSON
     xlsx_bytes = parseur.Mailbox.download(123, "xlsx")   # XLSX

- Create a mailbox. All fields are optional (Parseur generates a name and
  email address when omitted). The request body is validated and serialized
  with ``MailboxCreateSchema``; invalid values or unknown/read-only fields
  raise ``marshmallow.ValidationError`` before any request is sent. By default
  the AI Vision engine (``GCP_AI_2``) is used, and — when no fields are
  predefined — identification ``REQUESTED`` so Parseur auto-detects the fields.

  .. code-block:: python

     mailbox = parseur.Mailbox.create(
         name="Invoices",
         ai_engine="GCP_AI_2",
         retention_policy=30,
     )
     print(mailbox)

- Update a mailbox. Only the fields you pass are changed. The body is
  validated and serialized with ``MailboxUpdateSchema``.

  .. code-block:: python

     mailbox = parseur.Mailbox.update(123, name="Renamed", ai_engine="GCP_AI_2_5")
     print(mailbox)

Beyond the generic ``update``, each mailbox setting has a dedicated,
self-validating helper (a thin wrapper over ``update`` that targets one
setting). They all return the updated mailbox.

- Rename a mailbox.

  .. code-block:: python

     parseur.Mailbox.rename(123, "Invoices EU")

- Change the AI engine used to extract data.

  .. code-block:: python

     from parseur import AIEngine

     parseur.Mailbox.set_ai_engine(123, AIEngine.GCP_AI_2_5)

- Set (or clear) the natural-language extraction instructions.

  .. code-block:: python

     parseur.Mailbox.set_ai_instructions(123, "Extract the grand total")
     parseur.Mailbox.set_ai_instructions(123, None)  # clear

- Set the input formats — timezone, date format, and decimal separator. All
  three are nullable: pass ``None`` to reset to auto / the account default.

  .. code-block:: python

     from parseur import DateFormat, DecimalSeparator

     parseur.Mailbox.set_timezone(123, "Europe/Paris")
     parseur.Mailbox.set_date_format(123, DateFormat.DAY_FIRST)
     parseur.Mailbox.set_decimal_separator(123, DecimalSeparator.COMMA)

- Choose how incoming emails are processed.

  .. code-block:: python

     from parseur import EmailProcessing

     parseur.Mailbox.set_email_processing(123, EmailProcessing.ATTACHMENTS_ONLY)

- Filter incoming senders by an allow- or block-list (pass ``[]`` to clear).

  .. code-block:: python

     from parseur import SenderFilter

     parseur.Mailbox.set_sender_filter(123, SenderFilter.ALLOWLIST, ["acme.com"])

- Restrict which file types ("Files to process") are accepted. Each value is
  validated against :data:`~parseur.SUPPORTED_FILE_EXTENSIONS`; pass ``None`` to
  accept every supported type again.

  .. code-block:: python

     parseur.Mailbox.set_allowed_extensions(123, ["pdf", "docx"])

- Choose the per-document metadata columns. :class:`~parseur.Metadata` is an
  ``IntFlag``, so columns are enabled/disabled in parallel with ``|``; columns
  not listed are left unchanged.

  .. code-block:: python

     from parseur import Metadata

     parseur.Mailbox.set_metadata(
         123, enable=Metadata.SUBJECT | Metadata.SENDER, disable=Metadata.TO
     )

- Restrict which pages are processed — by page range, or to odd/even pages.
  Pass ``enabled=False`` to clear a restriction.

  .. code-block:: python

     parseur.Mailbox.process_page_range(123, [{"start_index": 1, "end_index": 5}])
     parseur.Mailbox.process_odd_pages(123)
     parseur.Mailbox.process_even_pages(123, enabled=False)

- Configure document splitting (the split itself runs per document via
  :meth:`Document.split`). Pass ``enabled=False`` to turn a method off.

  .. code-block:: python

     parseur.Mailbox.split_by_ai(123, "one invoice per page")
     parseur.Mailbox.split_by_page(123, 2)
     parseur.Mailbox.split_by_page_range(123, [{"start_index": 1, "end_index": 5}])
     parseur.Mailbox.split_by_keywords(123, [{"keyword": "Invoice", "is_before": True}])
     parseur.Mailbox.split_by_ai(123, enabled=False)

.. note::

   The advanced toggles ``force_ocr``, ``expand_result``,
   ``disable_document_links``, ``disable_deskew``, ``extract_xml_from_comment``
   and ``input_date_format_autodetection`` are intentionally not exposed.

- Delete a mailbox.

  .. code-block:: python

     parseur.Mailbox.delete(mailbox_id=123)
     print("Deleted!")

Parser Fields
^^^^^^^^^^^^^

Parseur has no per-field endpoint: a mailbox's fields live in its
``parser_object_set`` and are written back through the mailbox.
``ParserField`` reads the current fields, applies your change, and persists it.
Every write is validated and serialized through ``ParserFieldWriteSchema``, so
an invalid ``format`` or an unknown property raises
``marshmallow.ValidationError`` before any request is sent.

- List the fields of a mailbox.

  .. code-block:: python

     fields = parseur.ParserField.list(mailbox_id=123)
     for field in fields:
         print(field["id"], field["name"], field["format"])

- Add a field (keeping the existing ones).

  .. code-block:: python

     from parseur import FieldFormat

     parseur.ParserField.add(
         123,
         name="Total",
         field_format=FieldFormat.NUMBER,
         query="the grand total of the invoice",
     )

- Update a single field by id (only the provided properties change).

  .. code-block:: python

     parseur.ParserField.update(123, "PF12345", name="Grand Total")

- Delete a field by id.

  .. code-block:: python

     parseur.ParserField.delete(123, "PF12345")

- Download a table field's rows as a single file (one row per line item).
  Returns the file content as bytes.

  .. code-block:: python

     csv_bytes = parseur.ParserField.download(123, "PF12345")           # CSV
     xlsx_bytes = parseur.ParserField.download(123, "PF12345", "xlsx")  # XLSX

Documents
^^^^^^^^^

- List all documents in a mailbox with optional filtering.

  - *search*: Searches document id, name, template, email addresses, metadata
  - *order_by*: DocumentOrderKey
  - *received_after / received_before*: datetime.date
  - *with_result*: bool

  .. code-block:: python

     from datetime import datetime

     documents = parseur.Document.list(
         mailbox_id=123,
         search="invoice",
         order_by=DocumentOrderKey.PROCESSED,
         ascending=False,
         received_after=datetime(2024, 1, 1),
         with_result=True
     )
     for doc in documents:
         print(doc)

- Get document details.

  .. code-block:: python

     document = parseur.Document.retrieve(document_id="abcd-1234")
     print(document)

- Reprocess a document. Asynchronous: returns a notification_set (not the
  document); poll with ``retrieve`` / ``wait`` to see the new result.

  .. code-block:: python

     notifications = parseur.Document.reprocess(document_id="abcd-1234")
     print(notifications)

- Skip a document. Returns the updated document.

  .. code-block:: python

     document = parseur.Document.skip(document_id="abcd-1234")
     print(document)

- Copy document to another mailbox.

  .. code-block:: python

     result = parseur.Document.copy(document_id="abcd-1234", target_mailbox_id=456)
     print(result)

- Split a multi-page document (or undo a split). Both are asynchronous and
  return a notification_set.

  .. code-block:: python

     parseur.Document.split(document_id="abcd-1234")
     parseur.Document.reverse_split(document_id="abcd-1234")

- Retrieve logs for a document.

  .. code-block:: python

     logs = parseur.Document.logs(document_id="abcd-1234")
     for log in logs:
         print(log)

- Delete a document.

  .. code-block:: python

     parseur.Document.delete(document_id="abcd-1234")
     print("Deleted!")

Uploads
^^^^^^^

- Upload a local file.

  .. code-block:: python

     result = parseur.Document.upload_file(mailbox_id=123, file_path="/path/to/file.pdf")
     print(result)

- Upload text/email content.

  .. code-block:: python

     result = parseur.Document.upload_text(
         recipient="inbox@parseur.net",
         subject="Invoice 123",
         sender="billing@example.com",
         body_html="<p>Here is your invoice</p>"
     )
     print(result)

- Upload and wait for processing (synchronous). Polls until the document
  reaches a final status (``PARSEDOK``, ``PARSEDKO``, ``EXPORTKO``, ...). The
  cadence is fixed: a check every 5 seconds, for up to 10 minutes
  (``parseur.document.POLL_INTERVAL`` / ``MAX_WAIT``); a ``TimeoutError`` is
  raised if it is still processing after that.

  .. code-block:: python

     document = parseur.Document.upload_file_and_wait(123, "/path/to/file.pdf")
     print(document["status"], document["result"])

     # Same for email/text content:
     document = parseur.Document.upload_text_and_wait(
         recipient="inbox@parseur.net", subject="Invoice 123", body_plain="Total: 42"
     )

     # Or poll an already-uploaded document:
     document = parseur.Document.wait("abcd-1234")

     # Render progress with the on_poll callback:
     parseur.Document.upload_file_and_wait(
         123, "/path/to/file.pdf",
         on_poll=lambda elapsed, status: print(status, f"{elapsed:.0f}s"),
     )

  On the CLI, add ``--wait`` to show a live progress bar with an ETA::

     parseur upload-file 123 invoice.pdf --wait

Webhooks
^^^^^^^^

- Create a new custom webhook for documents or tables.

  .. code-block:: python

     result = parseur.Webhook.create(
         event=ParseurEvent.DOCUMENT_PROCESSED,
         target_url="https://example.com/webhook",
         mailbox_id=123,
         headers={"X-Custom-Header": "value"},
         name="My Webhook"
     )
     print(result)

- Get webhook details.

  .. code-block:: python

    webhook = parseur.Webhook.retrieve(webhook_id=789)
    print(webhook)

- Delete an existing webhook by its ID.

  .. code-block:: python

    parseur.Webhook.delete(webhook_id=789)
    print("Webhook deleted.")

- Enable a webhook for a specific mailbox.

  .. code-block:: python

     mailbox = parseur.Webhook.enable(mailbox_id=123, webhook_id=789)
     print(mailbox)

- Pause (disable) a webhook for a specific mailbox.

  .. code-block:: python

     mailbox = parseur.Webhook.pause(mailbox_id=123, webhook_id=789)
     print(mailbox)

- Retrieve a list of all registered webhooks.

  .. code-block:: python

     webhooks = parseur.Webhook.list()
     for webhook in webhooks:
         print(webhook)

Exports
^^^^^^^

There are three ways to get a mailbox's results out as a file:

- the whole mailbox, one row per document — :meth:`Mailbox.download`;
- a single table field, one row per line item — :meth:`ParserField.download`;
- a custom column selection — an *export configuration*, described below.

An export configuration selects which columns to export for a mailbox
(``PARSER``) or one of its table fields (``PARSER_FIELD``), and exposes
``csv_download`` / ``xls_download`` URLs for the resulting file.

- Discover the columns you can export.

  .. code-block:: python

     groups = parseur.ExportConfig.available_fields(mailbox_id=123)
     for group in groups:
         print(group["type"], group["items"])

- Create, list, retrieve, update and delete export configurations.

  .. code-block:: python

     config = parseur.ExportConfig.create(
         123, name="Invoices CSV", items=["InvoiceNumber", "TotalDue"]
     )
     parseur.ExportConfig.list(123)
     parseur.ExportConfig.retrieve(123, config["id"])
     parseur.ExportConfig.update(123, config["id"], name="Renamed")
     parseur.ExportConfig.delete(123, config["id"])

  For a table field, pass ``export_type=ExportType.PARSER_FIELD`` and the
  ``parser_field_id``.

- Download the configured export (bytes).

  .. code-block:: python

     csv_bytes = parseur.ExportConfig.download(123, config["id"])           # CSV
     xlsx_bytes = parseur.ExportConfig.download(123, config["id"], "xlsx")  # XLSX

Command Line Interface
++++++++++++++++++++++

The CLI covers reading mailboxes and their fields, document operations
(including synchronous uploads and downloading results), exports, and webhooks.
Mailbox creation/update/deletion and parser-field *management* (add/update/
delete) are available through the Python API and the MCP server, but not the
CLI.

.. code-block:: bash

   parseur init --api-key YOUR_TOKEN
   parseur list-mailboxes
   parseur get-mailbox 123
   parseur get-mailbox-schema 123
   parseur list-parser-fields 123
   parseur list-documents 456 --search invoice --order-by status --descending

   # Synchronous upload: block until the document is parsed (live progress bar).
   parseur upload-file 123 /path/to/file.pdf --wait
   parseur upload-text --recipient inbox@parseur.net --subject "Invoice" --body-plain "Total: 42" --wait

   # Download results as a file (stdout by default, or --output FILE).
   parseur download-mailbox 123 --format csv -o results.csv   # whole mailbox
   parseur download-field 123 PF951 --format xlsx -o lines.xlsx  # a table field
   parseur list-export-configs 123
   parseur download-export 123 10 -o custom.csv               # a custom export

   parseur create-webhook --event document.processed --target-url https://example.com/webhook

MCP Server
++++++++++

``parseur-py`` includes a `Model Context Protocol <https://modelcontextprotocol.io>`_
server that exposes the client as tools for AI assistants (Claude Desktop,
Cursor, Claude Code, ...). It speaks MCP over stdio and reads your API key
from ``~/.parseur.conf`` or the ``PARSEUR_API_KEY`` environment variable.

Install the extra:

.. code-block:: bash

   pip install "parseur-py[mcp]"

Run the server:

.. code-block:: bash

   parseur mcp
   # or: parseur-mcp
   # or: python -m parseur.mcp_server

Example Claude Desktop configuration (``claude_desktop_config.json``):

.. code-block:: json

   {
     "mcpServers": {
       "parseur": {
         "command": "parseur-mcp",
         "env": {
           "PARSEUR_API_KEY": "YOUR_PARSEUR_API_KEY"
         }
       }
     }
   }

Every tool carries a title, a description, per-argument descriptions,
behavioral annotations (read-only / destructive / idempotent / open-world
hints) and a structured JSON output schema, so the assistant knows exactly what
each tool does and what it returns. Read-only tools (``list_*`` / ``get_*``) are
safe to call freely; destructive tools (``delete_*``) are flagged so clients can
ask for confirmation first.

Tools
^^^^^

The server exposes the full client surface as 54 tools:

- **Mailboxes**: ``list_mailboxes``, ``get_mailbox``, ``get_mailbox_schema``,
  ``create_mailbox``, ``delete_mailbox``
- **Mailbox settings** (one tool per setting, instead of a generic update):
  ``rename_mailbox``, ``set_ai_engine``, ``set_ai_instructions``,
  ``set_email_processing``, ``set_metadata``, ``set_timezone``,
  ``set_date_format``, ``set_decimal_separator``, ``set_allowed_extensions``,
  ``set_sender_filter``, ``split_by_ai``, ``split_by_page``,
  ``split_by_page_range``, ``split_by_keywords``, ``process_page_range``,
  ``process_odd_pages``, ``process_even_pages``
- **Parser fields**: ``list_parser_fields``, ``add_parser_field``,
  ``update_parser_field``, ``delete_parser_field``
- **Documents**: ``list_documents``, ``get_document``, ``get_document_logs``,
  ``reprocess_document``, ``skip_document``, ``copy_document``,
  ``split_document``, ``reverse_split_document``, ``delete_document``
- **Uploads**: ``upload_file``, ``upload_text`` (asynchronous) and
  ``upload_file_and_wait``, ``upload_text_and_wait``, ``wait_for_document``
  (block until the document is parsed)
- **Webhooks**: ``list_webhooks``, ``get_webhook``, ``create_webhook``,
  ``delete_webhook``, ``enable_webhook``, ``pause_webhook``
- **Exports**: ``get_mailbox_export``, ``get_table_export``,
  ``list_export_fields``, ``list_export_configs``, ``get_export_config``,
  ``create_export_config``, ``update_export_config``, ``delete_export_config``

Workflow
^^^^^^^^

The tools are designed around the lifecycle of a Parseur mailbox. The server's
own instructions describe the same flow so the assistant can follow it
unassisted.

1. **Create a mailbox** with just a title (``create_mailbox``). Do *not* define
   fields up front: Parseur auto-detects them from the first documents during
   its identification phase. Adjust them afterwards with ``add_parser_field`` /
   ``update_parser_field`` / ``delete_parser_field``.
2. **Send documents** to parse with ``upload_file`` (a path on the server's
   machine) or ``upload_text`` (email/HTML content).
3. **Wait for the result.** Parsing is asynchronous: a document is pending while
   its status is ``INCOMING`` / ``ANALYZING`` / ``PROGRESS`` and finished at
   ``PARSEDOK`` (or ``PARSEDKO`` / ``EXPORTKO``). The extracted data lives in the
   document's ``result`` field, populated only once it reaches ``PARSEDOK``. To
   get the result in a single call, prefer ``upload_file_and_wait`` /
   ``upload_text_and_wait``; to wait on an already-uploaded document use
   ``wait_for_document``.
4. **Get the data out as a file** — three kinds of export:

   - the whole mailbox, one row per document — ``get_mailbox_export``;
   - one table field, one row per line item — ``get_table_export``;
   - a custom column selection — ``list_export_fields`` then
     ``create_export_config``.

   Each returns ready-to-use, self-authenticating ``csv`` / ``json`` / ``xlsx``
   download links. Alternatively, ``create_webhook`` pushes each parsed document
   to a URL in real time.

IDs follow a simple convention: mailboxes and webhooks use an integer id,
documents use a string id, parser/table fields use a ``PF...`` string id, and
export configs use an integer id.

Publishing to the MCP Registry
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The server is described by ``server.json`` at the repository root and can be
published to the official `MCP Registry <https://registry.modelcontextprotocol.io>`_
under the ``io.github.parseur/parseur-py`` name. Ownership is verified through
the GitHub ``parseur`` organization and the ``mcp-name`` marker shipped in the
PyPI README.

.. code-block:: bash

   # 1. Install the publisher CLI
   curl -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_$(uname -s | tr '[:upper:]' '[:lower:]')_$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/').tar.gz" | tar xz mcp-publisher

   # 2. Authenticate (you must be a member of the `parseur` GitHub org)
   ./mcp-publisher login github

   # 3. Publish the version described in server.json
   ./mcp-publisher publish

Keep the ``version`` in ``server.json`` in sync with the ``parseur-py`` release
on PyPI (whose README must contain the ``mcp-name`` marker). A GitHub Actions
workflow publishes automatically on each GitHub release. Clients then run the
server with::

   uvx --from "parseur-py[mcp]" parseur-py