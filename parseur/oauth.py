"""OAuth client for local Parseur applications.

The MCP server runs over stdio on the user's machine, so it cannot delegate
OAuth to the MCP host.  Instead, this module performs the authorization-code
flow itself using a short-lived loopback callback and PKCE.
"""

import base64
import hashlib
import json
import os
import secrets
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlencode, urlsplit

import requests


class OAuthError(RuntimeError):
    """Raised when Parseur OAuth cannot provide a usable access token."""


class OAuthClient:
    def __init__(
        self,
        api_base: str,
        token_path: Optional[Path] = None,
        timeout: int = 300,
    ) -> None:
        self.api_base = api_base.rstrip("/")
        self.resource = f"{self.api_base}/mcp"
        self.token_path = token_path or Path.home() / ".parseur.oauth.json"
        self.timeout = timeout

    @property
    def authorization_endpoint(self) -> str:
        return f"{self.api_base}/oauth/authorize"

    @property
    def registration_endpoint(self) -> str:
        return f"{self.api_base}/oauth/register"

    @property
    def token_endpoint(self) -> str:
        return f"{self.api_base}/oauth/token"

    def get_access_token(self, interactive: bool = False) -> str:
        tokens = self._load_tokens()
        if tokens and tokens.get("access_token") and float(
            tokens.get("expires_at", 0)
        ) > time.time() + 60:
            return str(tokens["access_token"])

        if tokens and tokens.get("refresh_token") and tokens.get("client_id"):
            try:
                return self._refresh(tokens)
            except (OAuthError, requests.RequestException):
                if not interactive:
                    raise OAuthError(
                        "Parseur OAuth has expired. Run 'parseur login' to "
                        "sign in again."
                    )

        if interactive:
            return self.login()
        raise OAuthError(
            "No Parseur credential is available. Run 'parseur login' or "
            "'parseur init --api-key …'."
        )

    def login(self, open_browser: bool = True) -> str:
        callback: Dict[str, str] = {}
        callback_received = threading.Event()

        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(handler) -> None:  # noqa: N802
                request_url = urlsplit(handler.path)
                if request_url.path != "/callback":
                    handler.send_error(404)
                    return
                query = parse_qs(request_url.query)
                for key in ("code", "state", "error", "error_description"):
                    if query.get(key):
                        callback[key] = query[key][0]
                callback_received.set()

                success = "code" in callback and "error" not in callback
                title = "Connexion terminée" if success else "Connexion impossible"
                message = (
                    "Vous pouvez fermer cette page et revenir à votre application."
                    if success
                    else (
                        "Revenez à votre application pour afficher le détail "
                        "de l’erreur."
                    )
                )
                body = (
                    "<!doctype html><html><head><meta charset='utf-8'>"
                    f"<title>{title}</title></head><body style='font-family:system-ui;"
                    "max-width:560px;margin:15vh auto;padding:24px'>"
                    f"<h1>{title}</h1><p>{message}</p></body></html>"
                ).encode()
                handler.send_response(200)
                handler.send_header("Content-Type", "text/html; charset=utf-8")
                handler.send_header("Content-Length", str(len(body)))
                handler.end_headers()
                handler.wfile.write(body)

            def log_message(self, format: str, *args: Any) -> None:
                return

        server = HTTPServer(("127.0.0.1", 0), CallbackHandler)
        server.timeout = self.timeout
        redirect_uri = f"http://127.0.0.1:{server.server_port}/callback"

        try:
            registration = requests.post(
                self.registration_endpoint,
                json={
                    "client_name": "Parseur local MCP server",
                    "redirect_uris": [redirect_uri],
                    "grant_types": ["authorization_code", "refresh_token"],
                    "response_types": ["code"],
                    "token_endpoint_auth_method": "none",
                },
                timeout=15,
            )
            self._raise_for_oauth_error(registration, "OAuth registration failed")
            client_id = registration.json()["client_id"]

            verifier = secrets.token_urlsafe(64)
            challenge = (
                base64.urlsafe_b64encode(
                    hashlib.sha256(verifier.encode("ascii")).digest()
                )
                .rstrip(b"=")
                .decode("ascii")
            )
            state = secrets.token_urlsafe(32)
            authorize_url = self.authorization_endpoint + "?" + urlencode(
                {
                    "response_type": "code",
                    "client_id": client_id,
                    "redirect_uri": redirect_uri,
                    "state": state,
                    "scope": "mcp",
                    "code_challenge": challenge,
                    "code_challenge_method": "S256",
                    "resource": self.resource,
                }
            )

            if open_browser and not webbrowser.open(authorize_url):
                raise OAuthError(
                    f"Could not open a browser. Open this URL: {authorize_url}"
                )

            deadline = time.monotonic() + self.timeout
            while not callback_received.is_set() and time.monotonic() < deadline:
                server.timeout = min(1, max(0, deadline - time.monotonic()))
                server.handle_request()
            if not callback_received.is_set():
                raise OAuthError("Timed out waiting for Parseur sign-in.")
            if callback.get("state") != state:
                raise OAuthError("OAuth callback state did not match.")
            if callback.get("error"):
                detail = callback.get("error_description") or callback["error"]
                raise OAuthError(f"Parseur sign-in was rejected: {detail}")
            if not callback.get("code"):
                raise OAuthError(
                    "The OAuth callback did not contain an authorization code."
                )

            response = requests.post(
                self.token_endpoint,
                data={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "code": callback["code"],
                    "redirect_uri": redirect_uri,
                    "code_verifier": verifier,
                    "resource": self.resource,
                },
                timeout=15,
            )
            self._raise_for_oauth_error(response, "OAuth token exchange failed")
            tokens = self._token_record(response.json(), client_id)
            self._save_tokens(tokens)
            return str(tokens["access_token"])
        except requests.RequestException as error:
            raise OAuthError(f"Could not contact Parseur OAuth: {error}") from error
        finally:
            server.server_close()

    def logout(self) -> None:
        try:
            self.token_path.unlink()
        except FileNotFoundError:
            pass

    def _refresh(self, tokens: Dict[str, Any]) -> str:
        response = requests.post(
            self.token_endpoint,
            data={
                "grant_type": "refresh_token",
                "client_id": tokens["client_id"],
                "refresh_token": tokens["refresh_token"],
                "resource": self.resource,
            },
            timeout=15,
        )
        self._raise_for_oauth_error(response, "OAuth token refresh failed")
        refreshed = self._token_record(response.json(), str(tokens["client_id"]))
        self._save_tokens(refreshed)
        return str(refreshed["access_token"])

    def _token_record(
        self, response: Dict[str, Any], client_id: str
    ) -> Dict[str, Any]:
        if not response.get("access_token") or not response.get("refresh_token"):
            raise OAuthError("The OAuth server returned an incomplete token response.")
        return {
            "api_base": self.api_base,
            "client_id": client_id,
            "access_token": response["access_token"],
            "refresh_token": response["refresh_token"],
            "expires_at": time.time() + int(response.get("expires_in", 3600)),
            "scope": response.get("scope", "mcp"),
        }

    def _load_tokens(self) -> Optional[Dict[str, Any]]:
        try:
            with self.token_path.open() as stream:
                tokens = json.load(stream)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return None
        if tokens.get("api_base", "").rstrip("/") != self.api_base:
            return None
        return tokens

    def _save_tokens(self, tokens: Dict[str, Any]) -> None:
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(
            self.token_path,
            os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
            0o600,
        )
        with os.fdopen(descriptor, "w") as stream:
            json.dump(tokens, stream)
        os.chmod(self.token_path, 0o600)

    @staticmethod
    def _raise_for_oauth_error(response: requests.Response, prefix: str) -> None:
        try:
            response.raise_for_status()
        except requests.HTTPError as error:
            try:
                payload = response.json()
                detail = payload.get("error_description") or payload.get("error")
            except (ValueError, AttributeError):
                detail = None
            raise OAuthError(f"{prefix}: {detail or response.status_code}") from error
