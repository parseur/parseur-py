import logging
from typing import Any, Dict, Iterable, List, Optional

from parseur.event import ParseurEvent
from parseur.schemas.webhook import WebhookSchema
from parseur.client import Client
from parseur.mailbox import Mailbox


class Webhook:

    @classmethod
    def from_response(cls, data: Dict) -> Dict:
        """
        Deserialize a webhook API response.

        :param data: Raw API response dictionary.
        :return: Deserialized webhook dictionary.
        """
        return WebhookSchema().load(data)

    @classmethod
    def create(
        cls,
        event: ParseurEvent,
        target_url: str,
        mailbox_id: Optional[int] = None,
        table_field_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new custom webhook for Parseur.

        :param event: Webhook event type (document or table event).
        :param target_url: The URL to send webhook POSTs to.
        :param mailbox_id: Mailbox ID (required for document events).
        :param table_field_id: Table field ID (required for table events, e.g. "PF12345").
        :param headers: Optional custom HTTP headers.
        :param name: Optional custom name for the webhook.
        :return: The created webhook object as a dictionary.
        """
        body = {
            "event": event.value,
            "target": target_url,
            "category": "CUSTOM",
        }

        if name:
            body["name"] = name
        if headers:
            body["headers"] = headers

        if event.is_table_event():
            if not table_field_id:
                raise ValueError("table_field_id is required for table events")
            body["parser_field"] = table_field_id
        else:
            if not mailbox_id:
                raise ValueError("mailbox_id is required for document events")
            body["parser"] = mailbox_id

        raw = Client.request("POST", "/webhook", json=body)
        return cls.from_response(raw)

    @classmethod
    def retrieve(cls, webhook_id: int) -> bool:
        """
        Retrieve a webhook from the account.

        :param webhook_id: ID of the webhook to delete.
        :return: The updated mailbox object as a dictionary.
        """
        raw = Client.request("GET", f"/webhook/{webhook_id}")
        return cls.from_response(raw)

    @classmethod
    def delete(cls, webhook_id: int) -> bool:
        """
        Delete a webhook from the account.

        :param webhook_id: ID of the webhook to delete.
        :return: True if deletion was successful.
        """
        Client.request("DELETE", f"/webhook/{webhook_id}")
        logging.info(f"Deleted webhook ID: {webhook_id}")
        return True

    @classmethod
    def enable(cls, mailbox_id: int, webhook_id: int) -> Dict[str, Any]:
        """
        Enable an existing webhook for a given mailbox.

        :param mailbox_id: ID of the mailbox.
        :param webhook_id: ID of the webhook to enable.
        :return: The updated mailbox object as a dictionary.
        """
        raw = Client.request("POST", f"/parser/{mailbox_id}/webhook_set/{webhook_id}")
        return Mailbox.from_response(raw)

    @classmethod
    def pause(cls, mailbox_id: int, webhook_id: int) -> Dict[str, Any]:
        """
        Pause (disable) an existing webhook for a given mailbox.

        :param mailbox_id: ID of the mailbox.
        :param webhook_id: ID of the webhook to pause.
        :return: The updated mailbox object as a dictionary.
        """
        raw = Client.request("DELETE", f"/parser/{mailbox_id}/webhook_set/{webhook_id}")
        return Mailbox.from_response(raw)

    @classmethod
    def list(cls) -> List[Dict[str, Any]]:
        """Retrieve all webhooks as a list."""
        return list(cls.iter())

    @classmethod
    def iter(cls) -> Iterable[Dict[str, Any]]:
        """Yield all webhooks registered on the account."""
        for raw in Client.request("GET", "/webhook"):
            yield cls.from_response(raw)
