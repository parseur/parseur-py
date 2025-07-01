import sys

import click

import parseur


@click.group()
def cli():
    """Parseur CLI - manage Parseur.com from the command line."""
    pass


@cli.command()
@click.option(
    "--api-key",
    required=True,
    help="Your Parseur API key",
)
@click.option(
    "--api-base",
    default=parseur.DEFAULT_API_BASE,
    help="Optional API base URL",
)
def init(api_key, api_base):
    """Initialize the CLI with your API token and optional base URL."""
    config = parseur.Config(parseur.CONFIG_PATH)
    config.api_key = api_key
    config.api_base = api_base
    config.save()
    click.echo(f"✅ Parseur CLI initialized and config saved to {parseur.CONFIG_PATH}")


# ------------------------
# Mailbox commands
# ------------------------


@cli.command("list-mailboxes")
@click.option("--search", help="Search string (mailbox name or email prefix)")
@click.option(
    "--order-by",
    type=click.Choice([e.value for e in parseur.MailboxOrderKey]),
    help=(
        "Order by field. Use one of: "
        "name, document_count, template_count, "
        "PARSEDOK_count (processed), PARSEDKO_count (failed), "
        "QUOTAEXC_count (quota exceeded), EXPORTKO_count (export failed)"
    ),
)
@click.option(
    "--descending/--ascending",
    default=False,
    help="Sort descending (default is ascending)",
)
def list_mailboxes(search, order_by, descending):
    """
    List all mailboxes with optional filtering and sorting.
    """

    order_by_enum = parseur.MailboxOrderKey(order_by) if order_by else None

    mailboxes = parseur.Mailbox.list(
        search=search,
        order_by=order_by_enum,
        ascending=not descending,
    )
    click.echo(parseur.to_json(mailboxes))


@cli.command("get-mailbox")
@click.argument("mailbox_id", type=int)
def get_mailbox(mailbox_id):
    """Get details of a mailbox."""
    result = parseur.Mailbox.retrieve(mailbox_id)
    click.echo(parseur.to_json(result))


@cli.command("get-mailbox-schema")
@click.argument("mailbox_id", type=int)
def get_mailbox_schema(mailbox_id):
    """Get schema of a mailbox."""
    result = parseur.Mailbox.schema(mailbox_id)
    click.echo(parseur.to_json(result))


# ------------------------
# Document commands
# ------------------------


@cli.command("list-documents")
@click.argument("mailbox_id", type=int)
@click.option(
    "--search",
    help="Search string (document id, name, template name, email addresses, metadata)",
)
@click.option(
    "--order-by",
    type=click.Choice([e.value for e in parseur.DocumentOrderKey]),
    help="Order by field (name, created, processed, status)",
)
@click.option(
    "--descending/--ascending",
    default=False,
    help="Sort descending (default is ascending)",
)
@click.option(
    "--received-after",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Filter documents received after this date (YYYY-MM-DD)",
)
@click.option(
    "--received-before",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Filter documents received before this date (YYYY-MM-DD)",
)
@click.option(
    "--with-result",
    is_flag=True,
    help="Include parsed result with each document",
)
def list_documents(
    mailbox_id,
    search,
    order_by,
    descending,
    received_after,
    received_before,
    with_result,
):
    """
    List all documents in a mailbox with optional filtering, sorting, and result inclusion.
    """
    # Convert order_by string to enum if provided
    order_by_enum = parseur.DocumentOrderKey(order_by) if order_by else None
    docs = parseur.Document.list(
        mailbox_id=mailbox_id,
        search=search,
        order_by=order_by_enum,
        ascending=not descending,
        received_after=received_after,
        received_before=received_before,
        with_result=with_result,
    )
    click.echo(parseur.to_json(docs))


@cli.command("get-document")
@click.argument("document_id", type=str)
def get_document(document_id):
    """Get details of a document."""
    result = parseur.Document.retrieve(document_id)
    click.echo(parseur.to_json(result))


@cli.command("reprocess-document")
@click.argument("document_id", type=str)
def reprocess_document(document_id):
    """Reprocess a document."""
    result = parseur.Document.reprocess(document_id)
    click.echo(parseur.to_json(result))


@cli.command("skip-document")
@click.argument("document_id", type=str)
def skip_document(document_id):
    """Skip a document."""
    result = parseur.Document.skip(document_id)
    click.echo(parseur.to_json(result))


@cli.command("copy-document")
@click.argument("document_id", type=str)
@click.argument("target_mailbox_id", type=int)
def copy_document(document_id, target_mailbox_id):
    """Copy a document to another mailbox."""
    result = parseur.Document.copy(document_id, target_mailbox_id)
    click.echo(parseur.to_json(result))


@cli.command("get-document-logs")
@click.argument("document_id", type=str)
def get_document_logs(document_id):
    """Get logs of a document."""
    logs = parseur.Document.logs(document_id)
    click.echo(parseur.to_json(logs))


@cli.command("delete-document")
@click.argument("document_id", type=str)
def delete_document(document_id):
    """Delete a document."""
    parseur.Document.delete(document_id)
    click.echo(f"✅ Document {document_id} deleted.")


@cli.command("upload-file")
@click.argument("mailbox_id", type=int)
@click.argument("file_path", type=click.Path(exists=True))
def upload_file(mailbox_id, file_path):
    """Upload a document file to a mailbox."""
    result = parseur.Document.upload_file(mailbox_id, file_path)
    click.echo(parseur.to_json(result))


@cli.command("upload-folder")
@click.argument("mailbox_id", type=int)
@click.argument("folder_path", type=str)
def upload_folder(mailbox_id, folder_path):
    """Upload all files from a glob path."""
    results = list(parseur.Document.upload_folder(mailbox_id, folder_path))
    click.echo(parseur.to_json(results))


@cli.command("upload-text")
@click.option("--recipient", required=True, help="Mailbox email address")
@click.option("--subject", required=True, help="Subject line for the document")
@click.option("--sender", default=None, help="Sender email (optional)")
@click.option("--body-html", default=None, help="HTML text content")
@click.option("--body-plain", default=None, help="Plain text content")
def upload_text(recipient, subject, sender, body_html, body_plain):
    """Upload text content to a mailbox by email address."""
    result = parseur.Document.upload_text(
        recipient, subject, sender, body_html, body_plain
    )
    click.echo(parseur.to_json(result))


# ------------------------
# Webhook commands
# ------------------------


@cli.command("create-webhook")
@click.option(
    "--event",
    required=True,
    type=click.Choice([e.value for e in parseur.ParseurEvent]),
    help="Event type to listen for",
)
@click.option(
    "--target-url",
    required=True,
    help="The URL to receive webhook POSTs, e.g. https://api.example.com/parseur.",
)
@click.option(
    "--mailbox-id",
    type=int,
    help="Mailbox ID (required for document events).",
)
@click.option(
    "--table-field-id",
    type=str,
    help="Table field ID in 'PF12345' format (required for table events).",
)
@click.option(
    "--header",
    multiple=True,
    type=str,
    help="Custom HTTP header in 'Key:Value' format. Can be used multiple times.",
)
@click.option(
    "--name",
    type=str,
    help="Optional name for the webhook.",
)
def create_webhook(event, target_url, mailbox_id, table_field_id, header, name):
    """
    Create a new custom webhook for your Parseur account.
    """
    headers = {}
    for h in header:
        if ":" not in h:
            click.echo(f"❌ Invalid header format: {h}")
            sys.exit(1)
        key, value = h.split(":", 1)
        headers[key.strip()] = value.strip()

    event_enum = parseur.ParseurEvent(event)
    result = parseur.Webhook.create(
        event=event_enum,
        target_url=target_url,
        mailbox_id=mailbox_id,
        table_field_id=table_field_id,
        headers=headers or None,
        name=name,
    )
    click.echo(parseur.to_json(result))


@cli.command("get-webhook")
@click.argument("webhook_id", type=int)
def get_webhook(webhook_id):
    """Get details of a webhook."""
    result = parseur.Webhook.retrieve(webhook_id)
    click.echo(parseur.to_json(result))


@cli.command("delete-webhook")
@click.argument("webhook_id", type=int)
def delete_webhook(webhook_id):
    """
    Delete a registered webhook by its ID.

    This command permanently removes the webhook from your Parseur account.
    """
    parseur.Webhook.delete(webhook_id)
    click.echo(f"✅ Webhook {webhook_id} deleted.")


@cli.command("enable-webhook")
@click.argument("mailbox_id", type=int)
@click.argument("webhook_id", type=int)
def enable_webhook(mailbox_id, webhook_id):
    """
    Enable a webhook for the specified mailbox.

    Activates the webhook by adding it to the mailbox.
    """
    result = parseur.Webhook.enable(mailbox_id, webhook_id)
    click.echo(parseur.to_json(result))


@cli.command("pause-webhook")
@click.argument("mailbox_id", type=int)
@click.argument("webhook_id", type=int)
def pause_webhook(mailbox_id, webhook_id):
    """
    Pause a webhook for the specified mailbox.

    Removes the webhook from the mailbox without deleting it.
    """
    result = parseur.Webhook.pause(mailbox_id, webhook_id)
    click.echo(parseur.to_json(result))


@cli.command("list-webhooks")
def list_webhooks():
    """List all registered webhooks."""
    webhooks = parseur.Webhook.list()
    click.echo(parseur.to_json(webhooks))


if __name__ == "__main__":
    cli()
