from typing import Any, Dict, List, Optional, Union

from parseur.client import Client
from parseur.mailbox import Mailbox
from parseur.schemas.paserfield import FieldFormat, ParserFieldWriteSchema
from parseur.utils import download_url_field


def _to_write(fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Reshape API fields to their writable form (drops read-only properties).

    Dumping through ``ParserFieldWriteSchema`` emits only the writable fields
    and handles the nested columns of TABLE fields automatically.
    """
    return ParserFieldWriteSchema(many=True).dump(fields)


def _fmt(field_format: Union[str, FieldFormat]) -> str:
    """Normalize a field format (enum or string) to its string value."""
    return field_format.value if isinstance(field_format, FieldFormat) else field_format


class ParserField:
    """
    Manage the fields (``parser_object_set``) extracted by a mailbox.

    Parseur has no per-field endpoint: fields are read from the mailbox and
    written back via ``PUT /parser/{id}``. These helpers read the current
    fields, apply a change, and persist it. All writes are validated and
    serialized through ``ParserFieldWriteSchema``. A ``PUT`` upserts the
    submitted fields and leaves the others untouched; deletion is requested with
    a ``_destroy`` marker (see :meth:`delete`).
    """

    @classmethod
    def list(
        cls, mailbox_id: int, *, api_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Return the parser fields currently configured on a mailbox."""
        return (
            Mailbox.retrieve(mailbox_id, api_key=api_key).get("parser_object_set") or []
        )

    @classmethod
    def _save(
        cls,
        mailbox_id: int,
        fields: List[Dict[str, Any]],
        *,
        api_key: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Persist a field list via the mailbox and return the result."""
        mailbox = Mailbox.update(mailbox_id, parser_object_set=fields, api_key=api_key)
        return mailbox.get("parser_object_set") or []

    @classmethod
    def add(
        cls,
        mailbox_id: int,
        name: str,
        field_format: Union[str, FieldFormat],
        *,
        query: Optional[str] = None,
        is_required: Optional[bool] = None,
        used_by_ai: Optional[bool] = None,
        choice_set: Optional[List[str]] = None,
        parser_object_set: Optional[List[Dict[str, Any]]] = None,
        api_key: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Add a new field to a mailbox, keeping the existing ones.

        :param mailbox_id: ID of the mailbox.
        :param name: Name of the new field.
        :param field_format: Field format (see :class:`FieldFormat`).
        :param query: Optional AI extraction instructions.
        :param is_required: Optional required flag.
        :param used_by_ai: Optional flag controlling AI extraction.
        :param choice_set: Optional list of allowed values.
        :param parser_object_set: Optional nested columns (for TABLE fields).
        :param api_key: Optional API key overriding the global one for this call.
        :return: The updated list of parser fields.
        """
        fields = _to_write(cls.list(mailbox_id, api_key=api_key))
        new_field: Dict[str, Any] = {"name": name, "format": _fmt(field_format)}
        if query is not None:
            new_field["query"] = query
        if is_required is not None:
            new_field["is_required"] = is_required
        if used_by_ai is not None:
            new_field["used_by_ai"] = used_by_ai
        if choice_set is not None:
            new_field["choice_set"] = choice_set
        if parser_object_set is not None:
            new_field["parser_object_set"] = parser_object_set
        fields.append(new_field)
        return cls._save(mailbox_id, fields, api_key=api_key)

    @classmethod
    def update(
        cls,
        mailbox_id: int,
        field_id: str,
        *,
        api_key: Optional[str] = None,
        **changes: Any,
    ) -> List[Dict[str, Any]]:
        """
        Update a single existing field by its id.

        Only the provided keys are changed; the other fields are preserved.

        :param mailbox_id: ID of the mailbox.
        :param field_id: ID of the field to update (e.g. "PF12345").
        :param api_key: Optional API key overriding the global one for this call.
        :param changes: Writable field properties to change (``name``,
            ``format``, ``query``, ``is_required``, ``used_by_ai``,
            ``choice_set``, ``parser_object_set``). ``field_format`` is accepted
            as an alias for ``format``.
        :return: The updated list of parser fields.
        :raises ValueError: If no field with ``field_id`` exists on the mailbox.
        """
        if "field_format" in changes:
            changes["format"] = changes.pop("field_format")
        if "format" in changes:
            changes["format"] = _fmt(changes["format"])

        fields = _to_write(cls.list(mailbox_id, api_key=api_key))
        for field in fields:
            if field.get("id") == field_id:
                field.update(changes)
                break
        else:
            raise ValueError(
                f"No parser field with id {field_id!r} in mailbox {mailbox_id}"
            )
        return cls._save(mailbox_id, fields, api_key=api_key)

    @classmethod
    def delete(
        cls, mailbox_id: int, field_id: str, *, api_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Delete a single field from a mailbox by its id.

        Sends a ``_destroy`` marker for the field; the other fields are left
        untouched.

        :param mailbox_id: ID of the mailbox.
        :param field_id: ID of the field to delete (e.g. "PF12345").
        :param api_key: Optional API key overriding the global one for this call.
        :return: The updated list of parser fields.
        :raises ValueError: If no field with ``field_id`` exists on the mailbox.
        """
        target = next(
            (
                f
                for f in cls.list(mailbox_id, api_key=api_key)
                if f.get("id") == field_id
            ),
            None,
        )
        if target is None:
            raise ValueError(
                f"No parser field with id {field_id!r} in mailbox {mailbox_id}"
            )
        destroy_entry = {
            "name": target["name"],
            "format": target["format"],
            "_destroy": True,
        }
        return cls._save(mailbox_id, [destroy_entry], api_key=api_key)

    @classmethod
    def download(
        cls,
        mailbox_id: int,
        field_id: str,
        fmt: str = "csv",
        *,
        api_key: Optional[str] = None,
    ) -> bytes:
        """
        Download the rows of a field as a single file.

        This is the table-level export, meant for ``TABLE`` fields: one row per
        line item, with the table columns as columns. For the whole mailbox use
        :meth:`Mailbox.download`; for a custom column selection use
        :class:`ExportConfig`.

        :param mailbox_id: ID of the mailbox.
        :param field_id: ID of the field to export (e.g. "PF12345").
        :param fmt: ``"csv"`` (default), ``"json"`` or ``"xlsx"``.
        :param api_key: Optional API key overriding the global one for this call.
        :return: The export file content as bytes.
        :raises ValueError: If the field is unknown or the format is unavailable.
        """
        key = download_url_field(fmt)
        target = next(
            (
                f
                for f in cls.list(mailbox_id, api_key=api_key)
                if f.get("id") == field_id
            ),
            None,
        )
        if target is None:
            raise ValueError(
                f"No parser field with id {field_id!r} in mailbox {mailbox_id}"
            )
        url = target.get(key)
        if not url:
            raise ValueError(f"No {key} available for parser field {field_id}")
        return Client.download(url, api_key=api_key)
