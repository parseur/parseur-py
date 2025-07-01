from enum import Enum
from typing import Any, Dict, Iterable, List, Optional

from parseur.client import Client
from parseur.schemas.mailbox import MailboxSchema
from parseur.utils import resolve_absolute_urls


class MailboxOrderKey(str, Enum):
    """
    Enumeration of supported mailbox sorting keys.

    Used with the `order_by` parameter to specify sorting in Mailbox.list() and Mailbox.iter().
    """

    NAME = "name"
    DOCUMENT_COUNT = "document_count"
    TEMPLATE_COUNT = "template_count"
    PARSEDOK_COUNT = "PARSEDOK_count"
    PARSEDKO_COUNT = "PARSEDKO_count"
    QUOTAEXC_COUNT = "QUOTAEXC_count"
    EXPORTKO_COUNT = "EXPORTKO_count"


class Mailbox:

    @classmethod
    def from_response(cls, data: Dict) -> Dict:
        """
        Deserialize a single mailbox API response.

        :param data: Raw API response dictionary.
        :return: Validated and transformed mailbox dictionary.
        """
        return resolve_absolute_urls(MailboxSchema().load(data))

    @classmethod
    def iter(
        cls,
        *,
        search: Optional[str] = None,
        order_by: Optional[MailboxOrderKey] = None,
        ascending: bool = True,
    ) -> Iterable[Dict]:
        """
        Yield all mailboxes with pagination and optional filtering or sorting.
        """
        params = {}
        if search:
            params["search"] = search
        if order_by:
            prefix = "" if ascending else "-"
            params["ordering"] = f"{prefix}{order_by.value}"
        for raw in Client.paginate("/parser", params=params):
            yield cls.from_response(raw)

    @classmethod
    def list(
        cls,
        *,
        search: Optional[str] = None,
        order_by: Optional[MailboxOrderKey] = None,
        ascending: bool = True,
    ) -> List[Dict[str, Any]]:
        """Retrieve all mailboxes as a list."""
        return list(cls.iter(search=search, order_by=order_by, ascending=ascending))

    @classmethod
    def retrieve(cls, mailbox_id: int) -> Dict[str, Any]:
        """Retrieve a single mailbox by ID."""
        raw = Client.request("GET", f"/parser/{mailbox_id}")
        return cls.from_response(raw)

    @classmethod
    def schema(cls, mailbox_id: int) -> Dict[str, Any]:
        """Get the schema for a mailbox."""
        return Client.request("GET", f"/parser/{mailbox_id}/schema")
