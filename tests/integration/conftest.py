"""Fixtures for the integration test-suite.

Credentials are read from the environment and are NEVER stored in the repo or
in ``~/.parseur.conf``. Run the suite with, for example::

    PARSEUR_API_BASE=https://api.beta.parseur.com \\
    PARSEUR_API_KEY=sk_xxx \\
    pytest tests/integration -v

The whole suite is skipped automatically when ``PARSEUR_API_KEY`` is not set,
so the default ``pytest`` run stays offline.
"""

import os
import uuid

import pytest
import requests

import parseur
from samples.parser_fields import ALL_FORMAT_FIELDS

API_KEY = os.environ.get("PARSEUR_API_KEY")
API_BASE = os.environ.get("PARSEUR_API_BASE") or parseur.DEFAULT_API_BASE


@pytest.fixture(autouse=True)
def configure_real_api(set_dummy_api_key):
    """Point the client at the real API for every integration test.

    Depends on the (autouse) ``set_dummy_api_key`` fixture so that it always
    runs *after* it and wins, overriding the dummy credentials used by the
    unit tests.
    """
    if not API_KEY:
        pytest.skip("integration credentials not set (export PARSEUR_API_KEY)")

    previous_key, previous_base = parseur.api_key, parseur.api_base
    parseur.api_key = API_KEY
    parseur.api_base = API_BASE
    yield
    parseur.api_key, parseur.api_base = previous_key, previous_base


@pytest.fixture
def bootstrap(configure_real_api):
    """Return the ``/bootstrap`` payload (AI engine choices, email domain, ...).

    ``/bootstrap`` is intentionally NOT part of the supported library API; it is
    only used by the tests to discover server-side facts (the real AI engine
    list, the inbound email domain) and assert the library stays aligned.
    """
    resp = requests.get(
        f"{parseur.api_base}/bootstrap",
        headers={"Authorization": f"Token {parseur.api_key}"},
    )
    resp.raise_for_status()
    return resp.json()


@pytest.fixture
def mailbox(configure_real_api):
    """Create a throwaway mailbox and delete it after the test."""
    created = parseur.Mailbox.create(
        name=f"parseur-py integration {uuid.uuid4().hex[:8]}"
    )
    try:
        yield created
    finally:
        try:
            parseur.Mailbox.delete(created["id"])
        except Exception:
            pass


@pytest.fixture
def mailbox_with_fields(configure_real_api):
    """Create a throwaway AI mailbox with one field of every format.

    The fields match ``ALL_FORMAT_FIELDS`` (and the ``sample.txt`` /
    ``sample.pdf`` documents), so uploading those samples yields a fully
    populated result.
    """
    created = parseur.Mailbox.create(
        name=f"parseur-py integration {uuid.uuid4().hex[:8]}",
        ai_engine="GCP_AI_2_5",
        parser_object_set=ALL_FORMAT_FIELDS,
    )
    try:
        yield created
    finally:
        try:
            parseur.Mailbox.delete(created["id"])
        except Exception:
            pass
