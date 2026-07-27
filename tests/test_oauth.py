import json
import http.client
import stat
import threading
import time
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlsplit

import pytest
import requests

from parseur.oauth import OAuthClient, OAuthError


def response(payload, status=200):
    result = MagicMock()
    result.status_code = status
    result.json.return_value = payload
    if status >= 400:
        result.raise_for_status.side_effect = requests.HTTPError(response=result)
    return result


def test_returns_valid_stored_access_token(tmp_path):
    path = tmp_path / "tokens.json"
    path.write_text(
        json.dumps(
            {
                "api_base": "https://api.example",
                "access_token": "stored-access",
                "refresh_token": "stored-refresh",
                "client_id": "client",
                "expires_at": time.time() + 3600,
            }
        )
    )

    token = OAuthClient("https://api.example", path).get_access_token()

    assert token == "stored-access"


@patch("parseur.oauth.requests.post")
def test_refreshes_and_rotates_expired_tokens(mock_post, tmp_path):
    path = tmp_path / "tokens.json"
    path.write_text(
        json.dumps(
            {
                "api_base": "https://api.example",
                "access_token": "expired",
                "refresh_token": "old-refresh",
                "client_id": "client",
                "expires_at": 0,
            }
        )
    )
    mock_post.return_value = response(
        {
            "access_token": "new-access",
            "refresh_token": "new-refresh",
            "expires_in": 3600,
            "scope": "mcp",
        }
    )

    token = OAuthClient("https://api.example", path).get_access_token()

    assert token == "new-access"
    assert json.loads(path.read_text())["refresh_token"] == "new-refresh"
    _, kwargs = mock_post.call_args
    assert kwargs["data"]["grant_type"] == "refresh_token"
    assert kwargs["data"]["resource"] == "https://api.example/mcp"


@patch("parseur.oauth.webbrowser.open", return_value=True)
@patch("parseur.oauth.requests.post")
def test_login_uses_loopback_callback_pkce_and_stores_tokens(
    mock_post, mock_browser, tmp_path
):
    path = tmp_path / "tokens.json"
    mock_post.side_effect = [
        response({"client_id": "dynamic-client"}, status=201),
        response(
            {
                "access_token": "access",
                "refresh_token": "refresh",
                "expires_in": 3600,
                "scope": "mcp",
            }
        ),
    ]

    def complete_callback(url):
        params = parse_qs(urlsplit(url).query)
        callback_url = params["redirect_uri"][0]

        def send_callback():
            parsed = urlsplit(callback_url)
            query = (
                f"{parsed.path}?code=authorization-code"
                f"&state={params['state'][0]}"
            )
            connection = http.client.HTTPConnection(
                parsed.hostname, parsed.port, timeout=5
            )
            connection.request("GET", query)
            connection.getresponse().read()
            connection.close()

        threading.Thread(target=send_callback).start()
        return True

    mock_browser.side_effect = complete_callback

    token = OAuthClient("https://api.example", path, timeout=2).login()

    assert token == "access"
    authorize_url = mock_browser.call_args.args[0]
    authorize = parse_qs(urlsplit(authorize_url).query)
    assert authorize["code_challenge_method"] == ["S256"]
    assert authorize["scope"] == ["mcp"]
    assert authorize["resource"] == ["https://api.example/mcp"]
    assert authorize["redirect_uri"][0].startswith("http://127.0.0.1:")

    registration = mock_post.call_args_list[0].kwargs["json"]
    assert registration["redirect_uris"] == authorize["redirect_uri"]
    exchange = mock_post.call_args_list[1].kwargs["data"]
    assert exchange["code_verifier"]
    assert exchange["redirect_uri"] == authorize["redirect_uri"][0]
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_missing_tokens_require_login(tmp_path):
    with pytest.raises(OAuthError, match="parseur login"):
        OAuthClient("https://api.example", tmp_path / "missing").get_access_token()


def test_tokens_are_scoped_to_api_base(tmp_path):
    path = tmp_path / "tokens.json"
    path.write_text(
        json.dumps(
            {
                "api_base": "https://other.example",
                "access_token": "wrong-server",
                "expires_at": time.time() + 3600,
            }
        )
    )

    with pytest.raises(OAuthError):
        OAuthClient("https://api.example", path).get_access_token()
