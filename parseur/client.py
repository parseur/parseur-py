import logging
from typing import Any, Dict, Generator, Optional
from urllib.parse import urljoin

import requests

import parseur


class Client:
    @classmethod
    def auth_headers(cls, json=True) -> Dict[str, str]:
        if not parseur.api_key:
            raise ValueError("API token is required. Run 'parseur init' first.")
        headers = {"Authorization": f"Token {parseur.api_key}"}
        if json:
            headers["Content-Type"] = "application/json"
        return headers

    @classmethod
    def request(cls, method: str, endpoint: str, **kwargs) -> Any:
        url = urljoin(parseur.api_base, endpoint)
        logging.debug(f"Request: {method} {url}")
        headers = cls.auth_headers(json="json" in kwargs)
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()

    @classmethod
    def paginate(
        cls, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Generator[Dict, None, None]:
        url = urljoin(parseur.api_base, endpoint)
        headers = cls.auth_headers()
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
