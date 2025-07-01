import pytest

import parseur
from samples.document import (
    DOCUMENT_LIST_RESPONSE,
    DOCUMENT_LOG_RESPONSE,
    DOCUMENT_RESPONSE,
)
from samples.mailbox import MAILBOX_LIST_RESPONSE, MAILBOX_RESPONSE
from samples.webhook import WEBHOOK_LIST_RESPONSE, WEBHOOK_RESPONSE


@pytest.fixture(autouse=True)
def set_dummy_api_key():
    parseur.api_key = "dummy-token"
    parseur.api_base = "https://api.parseur.com"


@pytest.fixture()
def mailbox_data():
    return MAILBOX_RESPONSE


@pytest.fixture()
def mailbox_list_data():
    return MAILBOX_LIST_RESPONSE


@pytest.fixture()
def document_data():
    return DOCUMENT_RESPONSE


@pytest.fixture()
def document_list_data():
    return DOCUMENT_LIST_RESPONSE


@pytest.fixture()
def document_log_data():
    return DOCUMENT_LOG_RESPONSE


@pytest.fixture()
def webhook_data():
    return WEBHOOK_RESPONSE


@pytest.fixture()
def webhook_list_data():
    return WEBHOOK_LIST_RESPONSE
