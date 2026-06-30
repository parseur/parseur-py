from datetime import datetime, timezone
from enum import Enum
from glob import iglob
import logging
from pathlib import Path
import time
from typing import Dict, Iterable, List, Optional

from parseur.client import Client
from parseur.decorator import rate_limited_batch
from parseur.schemas.document import (
    DocumentLogSchema,
    DocumentSchema,
    DocumentStatus,
    DocumentUploadSchema,
    NotificationSetSchema,
)

# Statuses for a document that is still being processed (not yet final).
PENDING_STATUSES = frozenset(
    {
        DocumentStatus.INCOMING.value,
        DocumentStatus.ANALYZING.value,
        DocumentStatus.PROGRESS.value,
    }
)

# Final statuses: every other status, i.e. a document that is no longer pending.
FINAL_STATUSES = frozenset(
    status.value for status in DocumentStatus if status.value not in PENDING_STATUSES
)

# Failed statuses: final statuses where the document did not end up successfully
# parsed (parsing, export or post-processing error, unsupported file, no credits).
FAILED_STATUSES = frozenset(
    {
        DocumentStatus.PARSEDKO.value,
        DocumentStatus.EXPORTKO.value,
        DocumentStatus.TRANSKO.value,
        DocumentStatus.QUOTAEXC.value,
        DocumentStatus.INVALID.value,
    }
)

# Fixed polling cadence and budget for the synchronous "wait" helpers.
POLL_INTERVAL = 5  # seconds between status checks
MAX_WAIT = 600  # 10 minutes


class DocumentOrderKey(str, Enum):
    """
    Enumeration of supported document sorting keys.

    Used with the `order_by` parameter to specify sorting in list_documents and yield_documents.

    Members:

    - `NAME`: Sort by document name.
    - `CREATED`: Sort by created/received date.
    - `PROCESSED`: Sort by processed date.
    - `STATUS`: Sort by document status.
    """

    NAME = "name"
    CREATED = "created"
    PROCESSED = "processed"
    STATUS = "status"


class Document:
    """Document resource providing class-based API access."""

    @classmethod
    def from_response(cls, data: Dict) -> Dict:
        """Validate and deserialize a single document dict."""
        return DocumentSchema().load(data)

    @classmethod
    def log_from_response(cls, data: Dict) -> Dict:
        """Validate and deserialize a single document log dict."""
        return DocumentLogSchema().load(data)

    @classmethod
    def upload_from_response(cls, data: Dict) -> Dict:
        """Validate and deserialize a document upload response dict."""
        return DocumentUploadSchema().load(data)

    @classmethod
    def notifications_from_response(cls, data: Dict) -> Dict:
        """Deserialize the ``notification_set`` returned by async actions.

        Asynchronous endpoints (reprocess, copy, split, reverse_split) reply
        with ``{"notification_set": {<level>: [messages]}}`` rather than a
        document; this extracts and validates that inner mapping.
        """
        return NotificationSetSchema().load(data.get("notification_set", {}))

    @classmethod
    def iter(
        cls,
        mailbox_id: int,
        *,
        search: Optional[str] = None,
        order_by: Optional[DocumentOrderKey] = None,
        ascending: bool = True,
        received_after: Optional[datetime] = None,
        received_before: Optional[datetime] = None,
        with_result: bool = False,
        api_key: Optional[str] = None,
    ) -> Iterable[Dict]:
        """
        Yield all documents in a mailbox with pagination and filtering.

        :param mailbox_id: The mailbox ID to retrieve documents from.
        :param str search: Search string to filter documents.
            The search query parameter searches the following properties:

            - document id (exact match)
            - document name
            - template name
            - from, to, cc, and bcc email addresses
            - document metadata header

        :param DocumentOrderKey order_by: Enum value specifying the sorting field.
        :param bool ascending: Whether to sort in ascending order (True) or descending order (False).
        :param datetime.datetime received_after: Filter for documents received after this date (converted to UTC YYYY-MM-DD).
        :param datetime.datetime received_before: Filter for documents received before this date (converted to UTC YYYY-MM-DD).
        :param bool with_result: Whether to include the parsed result in the returned documents.
        :param api_key: Optional API key overriding the global one for this call.
        :yield dict: Each yielded dictionary represents a document.
        """
        params = {}

        if search:
            params["search"] = search

        if order_by:
            prefix = "" if ascending else "-"
            params["ordering"] = f"{prefix}{order_by.value}"

        if received_after:
            utc_date = received_after.astimezone(timezone.utc).strftime("%Y-%m-%d")
            params["received_after"] = utc_date
        if received_before:
            utc_date = received_before.astimezone(timezone.utc).strftime("%Y-%m-%d")
            params["received_before"] = utc_date

        if received_after or received_before:
            params["tz"] = "UTC"

        if with_result:
            params["with_result"] = "true"

        for raw in Client.paginate(
            f"/parser/{mailbox_id}/document_set", params=params, api_key=api_key
        ):
            yield cls.from_response(raw)

    @classmethod
    def list(
        cls,
        mailbox_id: int,
        *,
        search: Optional[str] = None,
        order_by: Optional[DocumentOrderKey] = None,
        ascending: bool = True,
        received_after: Optional[datetime] = None,
        received_before: Optional[datetime] = None,
        with_result: bool = False,
        api_key: Optional[str] = None,
    ) -> List[Dict]:
        return list(
            cls.iter(
                mailbox_id,
                search=search,
                order_by=order_by,
                ascending=ascending,
                received_after=received_after,
                received_before=received_before,
                with_result=with_result,
                api_key=api_key,
            )
        )

    @classmethod
    def retrieve(cls, document_id: str, *, api_key: Optional[str] = None) -> Dict:
        """Retrieve document details, deserialized."""
        raw = Client.request("GET", f"/document/{document_id}", api_key=api_key)
        return cls.from_response(raw)

    @classmethod
    def reprocess(cls, document_id: str, *, api_key: Optional[str] = None) -> Dict:
        """Re-run parsing on a document.

        Asynchronous: the API queues the work and returns a notification_set
        (``{<level>: [messages]}``), not the document. Poll with :meth:`wait`
        or :meth:`retrieve` to observe the result.
        """
        raw = Client.request(
            "POST", f"/document/{document_id}/process", api_key=api_key
        )
        return cls.notifications_from_response(raw)

    @classmethod
    def skip(cls, document_id: str, *, api_key: Optional[str] = None) -> Dict:
        """Mark a document as skipped and return the updated document."""
        raw = Client.request("POST", f"/document/{document_id}/skip", api_key=api_key)
        return cls.from_response(raw)

    @classmethod
    def copy(
        cls, document_id: str, target_mailbox_id: int, *, api_key: Optional[str] = None
    ) -> Dict:
        """Copy a document into another mailbox.

        Asynchronous: the new document is created in the background, so the API
        returns a notification_set (``{<level>: [messages]}``), not a document.
        """
        raw = Client.request(
            "POST", f"/document/{document_id}/copy/{target_mailbox_id}", api_key=api_key
        )
        return cls.notifications_from_response(raw)

    @classmethod
    def split(cls, document_id: str, *, api_key: Optional[str] = None) -> Dict:
        """Split a multi-page document following the mailbox's split settings.

        Asynchronous: returns a notification_set (``{<level>: [messages]}``).
        The mailbox must have at least one splitting method enabled and the
        document must be splittable, otherwise the API responds with an error.
        """
        raw = Client.request("POST", f"/document/{document_id}/split", api_key=api_key)
        return cls.notifications_from_response(raw)

    @classmethod
    def reverse_split(cls, document_id: str, *, api_key: Optional[str] = None) -> Dict:
        """Undo a previous split of a document.

        Asynchronous: returns a notification_set (``{<level>: [messages]}``).
        Only valid on a document that was split.
        """
        raw = Client.request(
            "POST", f"/document/{document_id}/reverse_split", api_key=api_key
        )
        return cls.notifications_from_response(raw)

    @classmethod
    def logs(cls, document_id: str, *, api_key: Optional[str] = None) -> List[Dict]:
        logs = []
        for raw in Client.paginate(f"/document/{document_id}/log_set", api_key=api_key):
            logs.append(cls.log_from_response(raw))
        return logs

    @classmethod
    def delete(cls, document_id: str, *, api_key: Optional[str] = None) -> bool:
        Client.request("DELETE", f"/document/{document_id}", api_key=api_key)
        logging.info(f"Deleted document ID: {document_id}")
        return True

    @classmethod
    def upload_file(
        cls, mailbox_id: int, file_path: str, *, api_key: Optional[str] = None
    ) -> Dict:
        """
        Upload a local file to a mailbox.

        The file is read from the filesystem of the machine running this code
        (for an MCP server, that is the server's machine — usually the same as
        the client when launched locally by Claude Desktop). ``~`` is expanded.

        :raises FileNotFoundError: If no readable file exists at ``file_path``.
        """
        path = Path(file_path).expanduser()
        if not path.is_file():
            raise FileNotFoundError(
                f"No file at '{path}'. The file must exist on the machine "
                f"running the Parseur client/MCP server; pass an absolute path."
            )
        with open(path, "rb") as file:
            files = {"file": (path.name, file)}
            raw = Client.request(
                "POST", f"/parser/{mailbox_id}/upload", files=files, api_key=api_key
            )
            return cls.upload_from_response(raw)

    @classmethod
    @rate_limited_batch()
    def batch_upload_files(
        cls, file_paths: List[str], mailbox_id: int, *, api_key: Optional[str] = None
    ) -> Iterable[Dict]:
        for file_path in file_paths:
            try:
                yield cls.upload_file(mailbox_id, file_path, api_key=api_key)
            except Exception as e:
                yield {"file": file_path, "error": str(e)}

    @classmethod
    def upload_folder(
        cls, mailbox_id: int, folder_path: str, *, api_key: Optional[str] = None
    ) -> Iterable[Dict]:
        paths = (
            str(p) for p in iglob(folder_path, recursive=True) if Path(p).is_file()
        )
        return cls.batch_upload_files(paths, mailbox_id, api_key=api_key)

    @classmethod
    def upload_text(
        cls,
        recipient: str,
        subject: str,
        sender: Optional[str] = None,
        body_html: Optional[str] = None,
        body_plain: Optional[str] = None,
        *,
        api_key: Optional[str] = None,
    ) -> Dict:
        data = {"recipient": recipient, "subject": subject}
        if sender:
            data["from"] = sender
        if body_html:
            data["body_html"] = body_html
        if body_plain:
            data["body_plain"] = body_plain
        logging.info(
            f"Uploading text to Parseur: recipient={recipient}, subject={subject}"
        )
        raw = Client.request("POST", "/email", json=data, api_key=api_key)
        return cls.upload_from_response(raw)

    @staticmethod
    def _uploaded_document_id(upload: Dict) -> str:
        """Extract the document id from an upload response.

        ``upload_text`` returns it as ``DocumentID``; file uploads return it as
        the first entry of ``attachments``.
        """
        if upload.get("DocumentID"):
            return upload["DocumentID"]
        attachments = upload.get("attachments") or []
        if attachments:
            return attachments[0]["DocumentID"]
        raise ValueError("Upload response did not contain a document id")

    @classmethod
    def wait(
        cls,
        document_id: str,
        *,
        api_key: Optional[str] = None,
        on_poll=None,
    ) -> Dict:
        """
        Poll a document until it reaches a final (non-pending) status.

        A document is still pending while its status is ``INCOMING``,
        ``ANALYZING`` or ``PROGRESS``; any other status (``PARSEDOK``,
        ``PARSEDKO``, ``EXPORTKO``, ...) is considered final. The cadence
        (``POLL_INTERVAL`` = 5s) and budget (``MAX_WAIT`` = 10 min) are fixed.

        :param document_id: ID of the document to poll.
        :param api_key: Optional API key overriding the global one for this call.
        :param on_poll: Optional callback ``on_poll(elapsed_seconds, status)``
            invoked after every status check (e.g. to render progress).
        :return: The document once it reaches a final status.
        :raises TimeoutError: If still pending after ``MAX_WAIT`` seconds.
        """
        start = time.monotonic()
        while True:
            doc = cls.retrieve(document_id, api_key=api_key)
            elapsed = time.monotonic() - start
            if on_poll is not None:
                on_poll(elapsed, doc["status"])
            if doc["status"] in FINAL_STATUSES:
                return doc
            if elapsed >= MAX_WAIT:
                raise TimeoutError(
                    f"Document {document_id} still '{doc['status']}' "
                    f"after {MAX_WAIT}s"
                )
            time.sleep(POLL_INTERVAL)

    @classmethod
    def upload_file_and_wait(
        cls,
        mailbox_id: int,
        file_path: str,
        *,
        api_key: Optional[str] = None,
        on_poll=None,
    ) -> Dict:
        """
        Upload a file and block until the document reaches a final status.

        :return: The processed document.
        :raises TimeoutError: If processing does not finish within ``MAX_WAIT``.
        """
        upload = cls.upload_file(mailbox_id, file_path, api_key=api_key)
        document_id = cls._uploaded_document_id(upload)
        return cls.wait(document_id, api_key=api_key, on_poll=on_poll)

    @classmethod
    def upload_text_and_wait(
        cls,
        recipient: str,
        subject: str,
        sender: Optional[str] = None,
        body_html: Optional[str] = None,
        body_plain: Optional[str] = None,
        *,
        api_key: Optional[str] = None,
        on_poll=None,
    ) -> Dict:
        """
        Upload text/email content and block until the document is final.

        :return: The processed document.
        :raises TimeoutError: If processing does not finish within ``MAX_WAIT``.
        """
        upload = cls.upload_text(
            recipient,
            subject,
            sender=sender,
            body_html=body_html,
            body_plain=body_plain,
            api_key=api_key,
        )
        document_id = cls._uploaded_document_id(upload)
        return cls.wait(document_id, api_key=api_key, on_poll=on_poll)
