from datetime import datetime, timezone
from enum import Enum
from glob import iglob
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from parseur.client import Client
from parseur.decorator import rate_limited_batch
from parseur.schemas.document import (
    DocumentLogSchema,
    DocumentSchema,
    DocumentUploadSchema,
)


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
        """Validate and deserialize a single document log dict."""
        return DocumentUploadSchema().load(data)

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

        for raw in Client.paginate(f"/parser/{mailbox_id}/document_set", params=params):
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
            )
        )

    @classmethod
    def retrieve(cls, document_id: str) -> Dict:
        """Retrieve document details, deserialized."""
        raw = Client.request("GET", f"/document/{document_id}")
        return cls.from_response(raw)

    @classmethod
    def reprocess(cls, document_id: str) -> Dict:
        raw = Client.request("POST", f"/document/{document_id}/process")
        return cls.from_response(raw)

    @classmethod
    def skip(cls, document_id: str) -> Dict:
        raw = Client.request("POST", f"/document/{document_id}/skip")
        return cls.from_response(raw)

    @classmethod
    def copy(cls, document_id: str, target_mailbox_id: int) -> Dict:
        raw = Client.request(
            "POST", f"/document/{document_id}/copy/{target_mailbox_id}"
        )
        return cls.from_response(raw)

    @classmethod
    def logs(cls, document_id: str) -> List[Dict]:
        logs = []
        for raw in Client.paginate(f"/document/{document_id}/log_set"):
            logs.append(cls.log_from_response(raw))
        return logs

    @classmethod
    def delete(cls, document_id: str) -> bool:
        Client.request("DELETE", f"/document/{document_id}")
        logging.info(f"Deleted document ID: {document_id}")
        return True

    @classmethod
    def upload_file(cls, mailbox_id: int, file_path: str) -> Dict:
        with open(file_path, "rb") as file:
            files = {"file": file}
            raw = Client.request("POST", f"/parser/{mailbox_id}/upload", files=files)
            return cls.upload_from_response(raw)

    @classmethod
    @rate_limited_batch()
    def batch_upload_files(
        cls, file_paths: List[str], mailbox_id: int
    ) -> Iterable[Dict]:
        for file_path in file_paths:
            try:
                yield cls.upload_file(mailbox_id, file_path)
            except Exception as e:
                yield {"file": file_path, "error": str(e)}

    @classmethod
    def upload_folder(cls, mailbox_id: int, folder_path: str) -> Iterable[Dict]:
        paths = (
            str(p) for p in iglob(folder_path, recursive=True) if Path(p).is_file()
        )
        return cls.batch_upload_files(paths, mailbox_id)

    @classmethod
    def upload_text(
        cls,
        recipient: str,
        subject: str,
        sender: Optional[str] = None,
        body_html: Optional[str] = None,
        body_plain: Optional[str] = None,
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
        raw = Client.request("POST", "/email", json=data)
        return cls.upload_from_response(raw)
