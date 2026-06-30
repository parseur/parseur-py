import logging
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Union

from parseur.client import Client
from parseur.schemas.mailbox import (
    AIEngine,
    DateFormat,
    DecimalSeparator,
    IdentificationStatus,
    MailboxCreateSchema,
    MailboxReadSchema,
    MailboxUpdateSchema,
    Metadata,
)
from parseur.utils import download_url_field, resolve_absolute_urls


class EmailProcessing(str, Enum):
    """How a mailbox processes incoming emails and their attachments.

    Maps to the ``process_attachments`` / ``attachments_only`` mailbox flags
    (see :meth:`Mailbox.set_email_processing`).
    """

    EMAILS_AND_ATTACHMENTS = "emails_and_attachments"  # process emails and attachments
    EMAILS_ONLY = "emails_only"  # process emails only, skip attachments
    ATTACHMENTS_ONLY = "attachments_only"  # process attachments only, skip emails


class SenderFilter(str, Enum):
    """How a mailbox filters incoming senders.

    Maps to ``use_whitelist_instead_of_blacklist`` (see
    :meth:`parseur.Mailbox.set_sender_filter`), paired with ``emails_or_domains``.
    """

    ALLOWLIST = "allowlist"  # only the listed emails/domains are accepted
    BLOCKLIST = "blocklist"  # the listed emails/domains are rejected


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
        return resolve_absolute_urls(MailboxReadSchema().load(data))

    @classmethod
    def iter(
        cls,
        *,
        search: Optional[str] = None,
        order_by: Optional[MailboxOrderKey] = None,
        ascending: bool = True,
        api_key: Optional[str] = None,
    ) -> Iterable[Dict]:
        """
        Yield all mailboxes with pagination and optional filtering or sorting.

        :param api_key: Optional API key overriding the global one for this call.
        """
        params = {}
        if search:
            params["search"] = search
        if order_by:
            prefix = "" if ascending else "-"
            params["ordering"] = f"{prefix}{order_by.value}"
        for raw in Client.paginate("/parser", params=params, api_key=api_key):
            yield cls.from_response(raw)

    @classmethod
    def list(
        cls,
        *,
        search: Optional[str] = None,
        order_by: Optional[MailboxOrderKey] = None,
        ascending: bool = True,
        api_key: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve all mailboxes as a list."""
        return list(
            cls.iter(
                search=search,
                order_by=order_by,
                ascending=ascending,
                api_key=api_key,
            )
        )

    @classmethod
    def retrieve(
        cls, mailbox_id: int, *, api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Retrieve a single mailbox by ID."""
        raw = Client.request("GET", f"/parser/{mailbox_id}", api_key=api_key)
        return cls.from_response(raw)

    @classmethod
    def schema(
        cls, mailbox_id: int, *, api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get the schema for a mailbox."""
        return Client.request("GET", f"/parser/{mailbox_id}/schema", api_key=api_key)

    @classmethod
    def create(
        cls,
        name: Optional[str] = None,
        *,
        ai_engine: Optional[str] = None,
        api_key: Optional[str] = None,
        **fields: Any,
    ) -> Dict[str, Any]:
        """
        Create a new mailbox (parser).

        :param name: Optional display name. Parseur generates one if omitted.
        :param ai_engine: AI engine (see :class:`AIEngine`). Defaults to the AI
            Vision engine (``GCP_AI_2``), which understands layout and images.
        :param api_key: Optional API key overriding the global one for this call.
        :param fields: Any other writable mailbox fields (e.g. ``ai_instructions``,
            ``parser_object_set``) forwarded to the API.
        :return: The created mailbox object as a dictionary.
        :raises marshmallow.ValidationError: If a value is invalid or an
            unknown/read-only field is provided.

        Defaults applied on creation (each overridable):

        - ``ai_engine`` is set to the AI Vision engine (``GCP_AI_2``).
        - When no fields are predefined, ``identification_status`` is set to
          ``REQUESTED`` so Parseur auto-detects fields from the first documents.
          If you predefine ``parser_object_set``, identification is left to the
          API default so those fields are used as-is (``REQUESTED`` would put the
          mailbox in identification mode and skip extraction).
        """
        body: Dict[str, Any] = dict(fields)
        if name is not None:
            body["name"] = name
        if ai_engine is not None:
            body["ai_engine"] = ai_engine
        body.setdefault("ai_engine", AIEngine.GCP_AI_2.value)
        # Auto-identification only makes sense when the fields are not predefined.
        if not body.get("parser_object_set"):
            body.setdefault(
                "identification_status", IdentificationStatus.REQUESTED.value
            )
        payload = MailboxCreateSchema().load(body)
        raw = Client.request("POST", "/parser", json=payload, api_key=api_key)
        return cls.from_response(raw)

    @classmethod
    def update(
        cls, mailbox_id: int, *, api_key: Optional[str] = None, **fields: Any
    ) -> Dict[str, Any]:
        """
        Update an existing mailbox.

        Only the fields you pass are changed; others are left untouched.

        :param mailbox_id: ID of the mailbox to update.
        :param api_key: Optional API key overriding the global one for this call.
        :param fields: Writable mailbox fields to update (e.g. ``name``,
            ``ai_engine``, ``ai_instructions``, ``retention_policy``).
        :return: The updated mailbox object as a dictionary.
        :raises marshmallow.ValidationError: If a value is invalid or an
            unknown/read-only field is provided.
        """
        body: Dict[str, Any] = dict(fields)
        body["id"] = mailbox_id
        payload = MailboxUpdateSchema().load(body)
        raw = Client.request(
            "PUT", f"/parser/{mailbox_id}", json=payload, api_key=api_key
        )
        return cls.from_response(raw)

    @classmethod
    def rename(
        cls, mailbox_id: int, name: str, *, api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Rename a mailbox.

        :param mailbox_id: ID of the mailbox.
        :param name: New display name.
        :param api_key: Optional API key overriding the global one for this call.
        :return: The updated mailbox.
        """
        return cls.update(mailbox_id, name=name, api_key=api_key)

    @classmethod
    def set_ai_engine(
        cls,
        mailbox_id: int,
        ai_engine: Union[AIEngine, str],
        *,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Set the AI engine a mailbox uses to extract data.

        :param mailbox_id: ID of the mailbox.
        :param ai_engine: One of :class:`~parseur.AIEngine`.
        :param api_key: Optional API key overriding the global one for this call.
        :return: The updated mailbox.
        """
        return cls.update(
            mailbox_id, ai_engine=AIEngine(ai_engine).value, api_key=api_key
        )

    @classmethod
    def set_ai_instructions(
        cls,
        mailbox_id: int,
        instructions: Optional[str],
        *,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Set the natural-language extraction instructions for a mailbox.

        :param mailbox_id: ID of the mailbox.
        :param instructions: Instructions text, or ``None`` to clear them.
        :param api_key: Optional API key overriding the global one for this call.
        :return: The updated mailbox.
        """
        return cls.update(mailbox_id, ai_instructions=instructions, api_key=api_key)

    @classmethod
    def split_by_ai(
        cls,
        mailbox_id: int,
        instructions: Optional[str] = None,
        *,
        enabled: bool = True,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Enable (or disable) splitting incoming documents with AI.

        Sets ``is_ai_split_enabled`` and, optionally, the natural-language
        ``ai_split_instructions``. AI splitting takes precedence over the other
        split methods. The split itself runs per document via
        :meth:`Document.split`.

        :param mailbox_id: ID of the mailbox.
        :param instructions: Optional AI splitting instructions.
        :param enabled: Set to ``False`` to turn AI splitting off.
        :param api_key: Optional API key overriding the global one for this call.
        :return: The updated mailbox.
        """
        fields: Dict[str, Any] = {"is_ai_split_enabled": enabled}
        if enabled and instructions is not None:
            fields["ai_split_instructions"] = instructions
        return cls.update(mailbox_id, api_key=api_key, **fields)

    @classmethod
    def split_by_page(
        cls,
        mailbox_id: int,
        every: Optional[int] = None,
        *,
        enabled: bool = True,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Enable (or disable) splitting documents every ``every`` pages.

        :param mailbox_id: ID of the mailbox.
        :param every: Number of pages per resulting document (required unless
            ``enabled`` is ``False``).
        :param enabled: Set to ``False`` to turn this split method off.
        :param api_key: Optional API key overriding the global one for this call.
        :return: The updated mailbox.
        """
        if enabled and every is None:
            raise ValueError("`every` is required to enable splitting by page count")
        return cls.update(
            mailbox_id, split_page=(every if enabled else None), api_key=api_key
        )

    @classmethod
    def split_by_page_range(
        cls,
        mailbox_id: int,
        ranges: Optional[List[Dict[str, Any]]] = None,
        *,
        enabled: bool = True,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Enable (or disable) splitting documents by explicit page ranges.

        :param mailbox_id: ID of the mailbox.
        :param ranges: List of ``{"start_index", "end_index"}`` dicts (validated
            by ``PageRangeSchema``); required unless ``enabled`` is ``False``.
        :param enabled: Set to ``False`` to clear the page-range split method.
        :param api_key: Optional API key overriding the global one for this call.
        :return: The updated mailbox.
        """
        if enabled and not ranges:
            raise ValueError("`ranges` is required to enable splitting by page range")
        return cls.update(
            mailbox_id, split_page_range_set=ranges if enabled else [], api_key=api_key
        )

    @classmethod
    def split_by_keywords(
        cls,
        mailbox_id: int,
        keywords: Optional[List[Dict[str, Any]]] = None,
        *,
        enabled: bool = True,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Enable (or disable) splitting documents on keywords.

        :param mailbox_id: ID of the mailbox.
        :param keywords: List of ``{"keyword", "is_before"}`` dicts (validated by
            ``SplitKeyWordsSchema``); required unless ``enabled`` is ``False``.
        :param enabled: Set to ``False`` to clear the keyword split method.
        :param api_key: Optional API key overriding the global one for this call.
        :return: The updated mailbox.
        """
        if enabled and not keywords:
            raise ValueError("`keywords` is required to enable splitting by keywords")
        return cls.update(
            mailbox_id, split_keywords=keywords if enabled else [], api_key=api_key
        )

    @classmethod
    def set_email_processing(
        cls,
        mailbox_id: int,
        mode: Union[EmailProcessing, str],
        *,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Configure how incoming emails and attachments are processed.

        :param mailbox_id: ID of the mailbox.
        :param mode: One of :class:`EmailProcessing` —
            ``EMAILS_AND_ATTACHMENTS`` (process both), ``EMAILS_ONLY`` (skip
            attachments) or ``ATTACHMENTS_ONLY`` (skip the email body).
        :param api_key: Optional API key overriding the global one for this call.
        :return: The updated mailbox.
        """
        process_attachments, attachments_only = {
            EmailProcessing.EMAILS_AND_ATTACHMENTS: (True, False),
            EmailProcessing.EMAILS_ONLY: (False, False),
            EmailProcessing.ATTACHMENTS_ONLY: (True, True),
        }[EmailProcessing(mode)]
        return cls.update(
            mailbox_id,
            process_attachments=process_attachments,
            attachments_only=attachments_only,
            api_key=api_key,
        )

    @classmethod
    def set_metadata(
        cls,
        mailbox_id: int,
        enable: Metadata = Metadata(0),
        disable: Metadata = Metadata(0),
        *,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Enable and/or disable metadata columns on a mailbox, in one call.

        Compose columns with ``|``. Only the columns referenced in ``enable`` or
        ``disable`` are changed; the others are left as they are.

        :param mailbox_id: ID of the mailbox.
        :param enable: Columns to turn on, e.g.
            ``Metadata.SUBJECT | Metadata.SENDER``.
        :param disable: Columns to turn off, e.g. ``Metadata.TO``.
        :param api_key: Optional API key overriding the global one for this call.
        :return: The updated mailbox.
        :raises ValueError: If a column appears in both ``enable`` and ``disable``.
        """
        if enable & disable:
            raise ValueError(f"columns both enabled and disabled: {enable & disable!r}")
        toggles: Dict[str, Any] = {}
        for column in Metadata:
            if column & enable:
                toggles[column.field] = True
            elif column & disable:
                toggles[column.field] = False
        return cls.update(mailbox_id, api_key=api_key, **toggles)

    @classmethod
    def set_allowed_extensions(
        cls,
        mailbox_id: int,
        extensions: Optional[List[str]],
        *,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Restrict which file types ("Files to process") the mailbox accepts.

        :param mailbox_id: ID of the mailbox.
        :param extensions: List of extensions to accept (e.g.
            ``["pdf", "docx", "png"]``). Each is validated against
            :data:`~parseur.schemas.mailbox.SUPPORTED_FILE_EXTENSIONS`. Pass
            ``None`` (or an empty list) to accept every supported type again.
        :param api_key: Optional API key overriding the global one for this call.
        :return: The updated mailbox.
        """
        return cls.update(mailbox_id, allowed_extensions=extensions, api_key=api_key)

    # ------------------------
    # Input formats (all nullable — pass None to clear and fall back to auto /
    # the account default).
    # ------------------------

    @classmethod
    def set_timezone(
        cls,
        mailbox_id: int,
        timezone: Optional[str],
        *,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Set the timezone used to interpret dates/times in documents.

        :param mailbox_id: ID of the mailbox.
        :param timezone: An IANA timezone name (e.g. ``"Europe/Paris"``), or
            ``None`` to clear it and fall back to the account default.
        :param api_key: Optional API key overriding the global one for this call.
        :return: The updated mailbox.
        """
        return cls.update(mailbox_id, default_timezone=timezone, api_key=api_key)

    @classmethod
    def set_date_format(
        cls,
        mailbox_id: int,
        date_format: Optional[Union[DateFormat, str]],
        *,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Set how ambiguous dates in documents are read.

        :param mailbox_id: ID of the mailbox.
        :param date_format: :class:`~parseur.DateFormat` (``MONTH_FIRST`` or
            ``DAY_FIRST``), or ``None`` to clear it.
        :param api_key: Optional API key overriding the global one for this call.
        :return: The updated mailbox.
        """
        value = None if date_format is None else DateFormat(date_format).value
        return cls.update(mailbox_id, input_date_format=value, api_key=api_key)

    @classmethod
    def set_decimal_separator(
        cls,
        mailbox_id: int,
        separator: Optional[Union[DecimalSeparator, str]],
        *,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Set the decimal separator for numbers in documents.

        :param mailbox_id: ID of the mailbox.
        :param separator: :class:`~parseur.DecimalSeparator` (``DOT`` or
            ``COMMA``), or ``None`` to clear it.
        :param api_key: Optional API key overriding the global one for this call.
        :return: The updated mailbox.
        """
        value = None if separator is None else DecimalSeparator(separator).value
        return cls.update(mailbox_id, decimal_separator=value, api_key=api_key)

    @classmethod
    def set_sender_filter(
        cls,
        mailbox_id: int,
        mode: Union[SenderFilter, str],
        emails_or_domains: List[str],
        *,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Filter incoming senders by an allow- or block-list.

        Sets the mode and its list together. Pass an empty list to clear the
        filter (accept every sender).

        :param mailbox_id: ID of the mailbox.
        :param mode: :class:`~parseur.SenderFilter` — ``ALLOWLIST`` (only the
            listed senders are accepted) or ``BLOCKLIST`` (the listed senders are
            rejected).
        :param emails_or_domains: Emails or domains to allow/block, e.g.
            ``["acme.com", "billing@foo.com"]``.
        :param api_key: Optional API key overriding the global one for this call.
        :return: The updated mailbox.
        """
        return cls.update(
            mailbox_id,
            use_whitelist_instead_of_blacklist=(
                SenderFilter(mode) == SenderFilter.ALLOWLIST
            ),
            emails_or_domains=emails_or_domains,
            api_key=api_key,
        )

    @classmethod
    def process_page_range(
        cls,
        mailbox_id: int,
        ranges: Optional[List[Dict[str, Any]]] = None,
        *,
        enabled: bool = True,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Restrict processing to the given page ranges of each document.

        :param mailbox_id: ID of the mailbox.
        :param ranges: List of ``{"start_index", "end_index"}`` dicts (validated
            by ``PageRangeSchema``); required unless ``enabled`` is ``False``.
        :param enabled: Set to ``False`` to clear the page-range restriction
            (process every page again).
        :param api_key: Optional API key overriding the global one for this call.
        :return: The updated mailbox.
        """
        if enabled and not ranges:
            raise ValueError("`ranges` is required to enable page-range processing")
        return cls.update(
            mailbox_id, page_range_set=ranges if enabled else [], api_key=api_key
        )

    @classmethod
    def process_odd_pages(
        cls, mailbox_id: int, enabled: bool = True, *, api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Restrict processing to odd pages (1, 3, 5, ...) of each document."""
        return cls.update(mailbox_id, odd_pages=enabled, api_key=api_key)

    @classmethod
    def process_even_pages(
        cls, mailbox_id: int, enabled: bool = True, *, api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Restrict processing to even pages (2, 4, 6, ...) of each document."""
        return cls.update(mailbox_id, even_pages=enabled, api_key=api_key)

    @classmethod
    def download(
        cls,
        mailbox_id: int,
        fmt: str = "csv",
        *,
        api_key: Optional[str] = None,
    ) -> bytes:
        """
        Download every parsed result of the mailbox as a single file.

        This is the document-level export: one row per processed document, with
        the mailbox's fields as columns. To export the rows of a table field
        instead, use :meth:`ParserField.download`; for a custom column
        selection, use :class:`ExportConfig`.

        :param mailbox_id: ID of the mailbox.
        :param fmt: ``"csv"`` (default), ``"json"`` or ``"xlsx"``.
        :param api_key: Optional API key overriding the global one for this call.
        :return: The export file content as bytes.
        :raises ValueError: If the format is unsupported or unavailable.
        """
        key = download_url_field(fmt)
        mailbox = cls.retrieve(mailbox_id, api_key=api_key)
        url = mailbox.get(key)
        if not url:
            raise ValueError(f"No {key} available for mailbox {mailbox_id}")
        return Client.download(url, api_key=api_key)

    @classmethod
    def delete(cls, mailbox_id: int, *, api_key: Optional[str] = None) -> bool:
        """
        Delete a mailbox.

        :param mailbox_id: ID of the mailbox to delete.
        :param api_key: Optional API key overriding the global one for this call.
        :return: True if the deletion request was accepted.
        """
        Client.request("DELETE", f"/parser/{mailbox_id}", api_key=api_key)
        logging.info(f"Deleted mailbox ID: {mailbox_id}")
        return True
