from unittest.mock import MagicMock, patch

import parseur
from parseur import ParseurEvent


@patch("parseur.client.requests.request")
def test_retrieve_webhook(mock_request, webhook_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = webhook_data
    mock_request.return_value = mock_response

    result = parseur.Webhook.retrieve(webhook_id=39)

    # Assert: underlying HTTP call
    assert mock_request.called

    # Extract call
    args, kwargs = mock_request.call_args
    assert args[0] == "GET"
    assert args[1] == "https://api.parseur.com/webhook/39"

    assert result.id == result["id"] == 39
    assert result.name == result["name"] == "toto"
    assert result.event == result["event"] == "table.processed"
    assert result.target == result["target"] == "https://yourserver.com/webhook"
    assert result.category == result["category"] == "CUSTOM"
    assert result.headers == result["headers"] == {}


@patch("parseur.client.requests.request")
def test_delete_webhook(mock_request):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_request.return_value = mock_response

    success = parseur.Webhook.delete(webhook_id=39)

    # Assert: underlying HTTP call
    assert mock_request.called

    # Extract call
    args, kwargs = mock_request.call_args
    assert args[0] == "DELETE"
    assert args[1] == "https://api.parseur.com/webhook/39"
    assert success is True


@patch("parseur.client.requests.request")
def test_enable_webhook(mock_request, mailbox_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mailbox_data
    mock_request.return_value = mock_response

    result = parseur.Webhook.enable(mailbox_id=120, webhook_id=39)

    # Assert: underlying HTTP call
    assert mock_request.called

    # Extract call
    args, kwargs = mock_request.call_args
    assert args[0] == "POST"
    assert args[1] == "https://api.parseur.com/parser/120/webhook_set/39"

    assert result.id == result["id"] == 120
    assert result.name == result["name"] == "Mailbox m70tq"


@patch("parseur.client.requests.request")
def test_pause_webhook(mock_request, mailbox_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mailbox_data
    mock_request.return_value = mock_response

    result = parseur.Webhook.pause(mailbox_id=120, webhook_id=39)

    # Assert: underlying HTTP call
    assert mock_request.called

    # Extract call
    args, kwargs = mock_request.call_args
    assert args[0] == "DELETE"
    assert args[1] == "https://api.parseur.com/parser/120/webhook_set/39"

    assert result.id == result["id"] == 120
    assert result.name == result["name"] == "Mailbox m70tq"


@patch("parseur.client.requests.request")
def test_list_webhooks(mock_request, webhook_list_data):

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = webhook_list_data
    mock_request.return_value = mock_response

    result = parseur.Webhook.list()

    # Assert: underlying HTTP call
    assert mock_request.called

    # Extract call
    args, kwargs = mock_request.call_args
    assert args[0] == "GET"
    assert args[1] == "https://api.parseur.com/webhook"

    assert len(result) == 9

    webhook = result[0]
    assert webhook.id == webhook["id"] == 33
    assert webhook.name == webhook["name"] == "n8n_webhook"
    assert webhook.event == webhook["event"] == "document.processed"
    assert (
        webhook.target
        == webhook["target"]
        == "http://localhost:5678/webhook/c28543fb-de48-4ede-9dc1-2c939f2c184a/parseur"
    )
    assert webhook.category == webhook["category"] == "N8N"
    assert (
        webhook.headers
        == webhook["headers"]
        == {"X-Parseur-Token": "ce9e6809-444e-4df0-aab3-71008d914db4"}
    )


@patch("parseur.client.Client.request")
def test_create_webhook(mock_request, webhook_data):
    mock_request.return_value = webhook_data

    result = parseur.Webhook.create(
        event=ParseurEvent.DOCUMENT_PROCESSED,
        target_url="https://yourserver.com/webhook",
        mailbox_id=153,
    )

    mock_request.assert_called_once()
    method, url = mock_request.call_args[0]
    payload = mock_request.call_args[1]["json"]

    assert method == "POST"
    assert url == "/webhook"

    assert payload["event"] == "document.processed"
    assert payload["target"] == "https://yourserver.com/webhook"
    assert payload["category"] == "CUSTOM"
    assert payload["parser"] == 153
    assert "parser_field" not in payload
    assert "headers" not in payload
    assert "name" not in payload

    assert result.id == result["id"] == 39
    assert result.event == result["event"] == "table.processed"
    assert result.name == result["name"] == "toto"
    assert result.target == result["target"] == "https://yourserver.com/webhook"
    assert result.category == result["category"] == "CUSTOM"


@patch("parseur.client.Client.request")
def test_create_table_webhook(mock_request, webhook_data):
    mock_request.return_value = webhook_data

    result = parseur.Webhook.create(
        event=ParseurEvent.TABLE_PROCESSED,
        target_url="https://yourserver.com/webhook",
        table_field_id="PF9999",
        name="my webhook",
        headers={"Authorization": "Bearer abc"},
    )

    payload = mock_request.call_args[1]["json"]

    assert payload["event"] == "table.processed"
    assert payload["target"] == "https://yourserver.com/webhook"
    assert payload["category"] == "CUSTOM"
    assert payload["parser_field"] == "PF9999"
    assert payload["name"] == "my webhook"
    assert payload["headers"] == {"Authorization": "Bearer abc"}

    assert result.name == result["name"] == "toto"
    assert result.target == result["target"] == "https://yourserver.com/webhook"
