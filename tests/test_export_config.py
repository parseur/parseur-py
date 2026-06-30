from unittest.mock import MagicMock, patch

import pytest
from marshmallow import ValidationError

import parseur
from samples.export_config import (
    EXPORT_CONFIG_LIST_RESPONSE,
    EXPORT_CONFIG_RESPONSE,
    EXPORT_FIELDS_RESPONSE,
)


@patch("parseur.client.requests.get")
def test_list_export_configs(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = EXPORT_CONFIG_LIST_RESPONSE
    mock_get.return_value = mock_response

    result = parseur.ExportConfig.list(120)

    args, _ = mock_get.call_args
    assert args[0].endswith("/parser/120/export_config")
    assert len(result) == 1
    cfg = result[0]
    assert cfg["id"] == 10
    assert cfg["name"] == "My CSV export"
    assert cfg["items"] == ["InvoiceNumber", "PONumber", "InvoiceDate"]
    # download URLs are resolved to absolute
    assert cfg["csv_download"].startswith("https://api.parseur.com/parser/")


@patch("parseur.client.requests.request")
def test_retrieve_export_config(mock_request, set_dummy_api_key):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = EXPORT_CONFIG_RESPONSE
    mock_request.return_value = mock_response

    cfg = parseur.ExportConfig.retrieve(120, 10)

    args, _ = mock_request.call_args
    assert args[0] == "GET"
    assert args[1].endswith("/parser/120/export_config/10")
    assert cfg["id"] == 10


@patch("parseur.client.requests.request")
def test_create_export_config(mock_request):
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = EXPORT_CONFIG_RESPONSE
    mock_request.return_value = mock_response

    parseur.ExportConfig.create(120, "My CSV export", ["InvoiceNumber", "TotalDue"])

    args, kwargs = mock_request.call_args
    assert args[0] == "POST"
    assert args[1].endswith("/parser/120/export_config")
    assert kwargs["json"] == {
        "name": "My CSV export",
        "type": "PARSER",
        "items": ["InvoiceNumber", "TotalDue"],
    }


@patch("parseur.client.requests.request")
def test_create_export_config_table(mock_request):
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = EXPORT_CONFIG_RESPONSE
    mock_request.return_value = mock_response

    parseur.ExportConfig.create(
        120,
        "Lines",
        ["ItemCode", "Amount"],
        export_type=parseur.ExportType.PARSER_FIELD,
        parser_field_id="PF951",
    )

    _, kwargs = mock_request.call_args
    body = kwargs["json"]
    assert body["type"] == "PARSER_FIELD"
    assert body["parser_field_id"] == "PF951"


@patch("parseur.client.requests.request")
def test_create_export_config_rejects_empty_items(mock_request):
    with pytest.raises(ValidationError):
        parseur.ExportConfig.create(120, "X", [])
    assert not mock_request.called


@patch("parseur.client.requests.request")
def test_create_export_config_rejects_bad_type(mock_request):
    with pytest.raises(ValidationError):
        parseur.ExportConfig.create(120, "X", ["a"], export_type="NOPE")
    assert not mock_request.called


@patch("parseur.client.requests.request")
def test_update_export_config(mock_request):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = EXPORT_CONFIG_RESPONSE
    mock_request.return_value = mock_response

    parseur.ExportConfig.update(120, 10, name="Renamed")

    args, kwargs = mock_request.call_args
    assert args[0] == "PATCH"
    assert args[1].endswith("/parser/120/export_config/10")
    assert kwargs["json"] == {"name": "Renamed"}


@patch("parseur.client.requests.request")
def test_delete_export_config(mock_request):
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.content = b""
    mock_request.return_value = mock_response

    assert parseur.ExportConfig.delete(120, 10) is True
    args, _ = mock_request.call_args
    assert args[0] == "DELETE"
    assert args[1].endswith("/parser/120/export_config/10")


@patch("parseur.client.requests.request")
def test_available_fields(mock_request):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = EXPORT_FIELDS_RESPONSE
    mock_request.return_value = mock_response

    groups = parseur.ExportConfig.available_fields(120)

    args, _ = mock_request.call_args
    assert args[0] == "GET"
    assert args[1].endswith("/parser/120/export_fields")
    assert {g["type"] for g in groups} == {"PARSER", "PARSER_FIELD"}


@patch("parseur.client.requests.get")
@patch("parseur.client.requests.request")
def test_download_export(mock_request, mock_get):
    retrieve_resp = MagicMock()
    retrieve_resp.status_code = 200
    retrieve_resp.json.return_value = EXPORT_CONFIG_RESPONSE
    mock_request.return_value = retrieve_resp

    dl_resp = MagicMock()
    dl_resp.status_code = 200
    dl_resp.content = b"InvoiceNumber,TotalDue\nINV-1,42\n"
    mock_get.return_value = dl_resp

    content = parseur.ExportConfig.download(120, 10)

    assert content == b"InvoiceNumber,TotalDue\nINV-1,42\n"
    # the absolute (resolved) csv_download URL was fetched
    args, _ = mock_get.call_args
    assert args[0].startswith("https://api.parseur.com/parser/")
    assert args[0].endswith(".csv?cfg=10")
