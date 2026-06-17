import logging
from typing import Any, Dict, Generator, Optional
from urllib.parse import urljoin

import requests

import parseur


class Client:
    @classmethod
    def auth_headers(cls, json=True, api_key: Optional[str] = None) -> Dict[str, str]:
        # An explicitly provided api_key takes priority over the global one.
        key = api_key or parseur.api_key
        if not key:
            raise ValueError("API token is required. Run 'parseur init' first.")
        headers = {"Authorization": f"Token {key}"}
        if json:
            headers["Content-Type"] = "application/json"
        return headers

    @classmethod
    def request(
        cls, method: str, endpoint: str, *, api_key: Optional[str] = None, **kwargs
    ) -> Any:
        url = urljoin(parseur.api_base, endpoint)
        logging.debug(f"Request: {method} {url}")
        headers = cls.auth_headers(json="json" in kwargs, api_key=api_key)
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        # Some endpoints (e.g. DELETE /webhook) reply with an empty body.
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    @classmethod
    def download(cls, url: str, *, api_key: Optional[str] = None) -> bytes:
        """GET a (possibly relative) URL with auth and return the raw bytes."""
        full_url = url if url.startswith("http") else urljoin(parseur.api_base, url)
        headers = cls.auth_headers(json=False, api_key=api_key)
        response = requests.get(full_url, headers=headers)
        response.raise_for_status()
        return response.content

    @classmethod
    def paginate(
        cls,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        *,
        api_key: Optional[str] = None,
    ) -> Generator[Dict, None, None]:
        url = urljoin(parseur.api_base, endpoint)
        headers = cls.auth_headers(api_key=api_key)
        params = params.copy() if params else {}
        page = 1

        while True:
            params["page"] = page
            logging.debug(f"Paginate request: {url} (page {page})")
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            for item in data["results"]:
                yield item

            if data["current"] >= data["total"]:
                break

            page += 1
