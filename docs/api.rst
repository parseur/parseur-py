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

.. code-block:: python

   import parseur

   parseur.api_key = "YOUR_API_KEY"


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

     mailbox = parseur.Mailbox.get(mailbox_id=123)
     print(mailbox)

- Get the schema of a mailbox.

  .. code-block:: python

     schema = parseur.Mailbox.schema(mailbox_id=123)
     print(schema)

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

- Reprocess a document.

  .. code-block:: python

     result = parseur.Document.reprocess(document_id="abcd-1234")
     print(result)

- Skip a document.

  .. code-block:: python

     result = parseur.Document.skip(document_id="abcd-1234")
     print(result)

- Copy document to another mailbox.

  .. code-block:: python

     result = parseur.Document.copy(document_id="abcd-1234", target_mailbox_id=456)
     print(result)

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

Command Line Interface
++++++++++++++++++++++

The CLI provides the same features as the API.

.. code-block:: bash

   parseur init --api-key YOUR_TOKEN
   parseur list-mailboxes
   parseur get-mailbox 123
   parseur list-documents 456 --search invoice --order-by status --descending
   parseur upload-file 123 /path/to/file.pdf
   parseur create-webhook --event document.processed --target-url https://example.com/webhook