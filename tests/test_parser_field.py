from unittest.mock import MagicMock, patch

import pytest
from marshmallow import ValidationError

import parseur


def _mock(mock_request, mailbox_data):
    """Return MAILBOX_RESPONSE for every request (GET retrieve + PUT update)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mailbox_data
    mock_request.return_value = mock_response
    return mock_response


@patch("parseur.client.requests.request")
def test_list_fields(mock_request, mailbox_data):
    _mock(mock_request, mailbox_data)

    fields = parseur.ParserField.list(120)

    assert [f["id"] for f in fields] == ["PF951"]
    assert fields[0]["format"] == "TABLE"


@patch("parseur.client.requests.request")
def test_add_field_appends_and_strips_readonly(mock_request, mailbox_data):
    _mock(mock_request, mailbox_data)

    parseur.ParserField.add(
        120, "Total", parseur.FieldFormat.NUMBER, query="the grand total"
    )

    # Last call is the PUT that persists the updated field set.
    args, kwargs = mock_request.call_args
    assert args[0] == "PUT"
    assert args[1] == "https://api.parseur.com/parser/120"

    body = kwargs["json"]
    assert body["id"] == 120
    sent_fields = body["parser_object_set"]

    # The existing field is echoed back without read-only keys.
    existing = next(f for f in sent_fields if f.get("id") == "PF951")
    assert "csv_download" not in existing
    assert "type" not in existing

    # The new field was appended (no id since it does not exist yet).
    new_field = next(f for f in sent_fields if f["name"] == "Total")
    assert new_field["format"] == "NUMBER"
    assert new_field["query"] == "the grand total"
    assert "id" not in new_field


@patch("parseur.client.requests.request")
def test_update_field_changes_only_target(mock_request, mailbox_data):
    _mock(mock_request, mailbox_data)

    parseur.ParserField.update(120, "PF951", name="Renamed Sheet")

    _, kwargs = mock_request.call_args
    sent_fields = kwargs["json"]["parser_object_set"]
    target = next(f for f in sent_fields if f["id"] == "PF951")
    assert target["name"] == "Renamed Sheet"


@patch("parseur.client.requests.request")
def test_update_field_format_alias(mock_request, mailbox_data):
    _mock(mock_request, mailbox_data)

    parseur.ParserField.update(120, "PF951", field_format=parseur.FieldFormat.TEXT)

    _, kwargs = mock_request.call_args
    target = next(f for f in kwargs["json"]["parser_object_set"] if f["id"] == "PF951")
    assert target["format"] == "TEXT"


@patch("parseur.client.requests.request")
def test_update_unknown_field_raises(mock_request, mailbox_data):
    _mock(mock_request, mailbox_data)

    with pytest.raises(ValueError):
        parseur.ParserField.update(120, "PF000", name="x")


@patch("parseur.client.requests.request")
def test_add_field_rejects_invalid_format(mock_request, mailbox_data):
    _mock(mock_request, mailbox_data)

    with pytest.raises(ValidationError):
        parseur.ParserField.add(120, "Bad", "NOT_A_FORMAT")


@patch("parseur.client.requests.request")
def test_delete_field(mock_request, mailbox_data):
    _mock(mock_request, mailbox_data)
    target = next(f for f in parseur.ParserField.list(120) if f["id"] == "PF951")

    parseur.ParserField.delete(120, "PF951")

    args, kwargs = mock_request.call_args
    assert args[0] == "PUT"
    assert args[1] == "https://api.parseur.com/parser/120"
    # A single _destroy marker (matched by name) is sent; others untouched.
    assert kwargs["json"]["parser_object_set"] == [
        {"name": target["name"], "format": target["format"], "_destroy": True}
    ]


@patch("parseur.client.requests.request")
def test_delete_unknown_field_raises(mock_request, mailbox_data):
    _mock(mock_request, mailbox_data)

    with pytest.raises(ValueError):
        parseur.ParserField.delete(120, "PF000")


@patch("parseur.client.requests.get")
@patch("parseur.client.requests.request")
def test_download_field(mock_request, mock_get, mailbox_data):
    _mock(mock_request, mailbox_data)
    dl = MagicMock()
    dl.status_code = 200
    dl.content = b"ItemCode,Amount\nWDG-1001,125.0\n"
    mock_get.return_value = dl

    content = parseur.ParserField.download(120, "PF951")

    assert content == b"ItemCode,Amount\nWDG-1001,125.0\n"
    # the table field's resolved csv_download URL was fetched
    url = mock_get.call_args[0][0]
    assert url.startswith("https://api.parseur.com/parser_field/")
    assert url.endswith("/Sheet.csv")


@patch("parseur.client.requests.request")
def test_download_unknown_field_raises(mock_request, mailbox_data):
    _mock(mock_request, mailbox_data)
    with pytest.raises(ValueError):
        parseur.ParserField.download(120, "PF000")
