"""The api_key passed to a call must take priority over the global one."""

from unittest.mock import MagicMock, patch

import pytest

import parseur
from parseur.client import Client


def _ok(json_value=None):
    response = MagicMock()
    response.status_code = 200
    response.content = b"{}"
    response.json.return_value = json_value if json_value is not None else {}
    return response


def test_auth_headers_prefers_explicit_key():
    parseur.api_key = "global-key"
    assert Client.auth_headers()["Authorization"] == "Token global-key"
    assert Client.auth_headers(api_key="call-key")["Authorization"] == "Token call-key"


def test_auth_headers_falls_back_to_global():
    parseur.api_key = "global-key"
    assert Client.auth_headers(api_key=None)["Authorization"] == "Token global-key"


def test_auth_headers_requires_a_key():
    parseur.api_key = None
    with pytest.raises(ValueError):
        Client.auth_headers()


@patch("parseur.client.requests.request")
def test_request_sends_override_key(mock_request):
    parseur.api_key = "global-key"
    mock_request.return_value = _ok()

    Client.request("GET", "/parser/1", api_key="call-key")

    _, kwargs = mock_request.call_args
    assert kwargs["headers"]["Authorization"] == "Token call-key"


@patch("parseur.client.requests.get")
def test_paginate_sends_override_key(mock_get):
    parseur.api_key = "global-key"
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"results": [{"id": 1}], "current": 1, "total": 1}
    mock_get.return_value = response

    list(Client.paginate("/parser", api_key="call-key"))

    _, kwargs = mock_get.call_args
    assert kwargs["headers"]["Authorization"] == "Token call-key"


@patch("parseur.client.requests.request")
def test_resource_method_threads_override_key(mock_request):
    """A high-level resource call forwards its api_key down to the request."""
    parseur.api_key = "global-key"
    mock_request.return_value = _ok({"fields": []})

    # Mailbox.schema returns the raw response (no schema validation), so it is
    # a clean way to assert the header that reached the HTTP layer.
    parseur.Mailbox.schema(1, api_key="call-key")

    _, kwargs = mock_request.call_args
    assert kwargs["headers"]["Authorization"] == "Token call-key"
