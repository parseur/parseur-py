from typing import Any, Dict, Iterable, List, Optional, Union

from parseur.client import Client
from parseur.schemas.export_config import (
    ExportConfigReadSchema,
    ExportConfigWriteSchema,
    ExportType,
)
from parseur.utils import download_url_field, resolve_absolute_urls


def _export_type_value(value: Union[str, ExportType]) -> str:
    return value.value if isinstance(value, ExportType) else value


class ExportConfig:
    """
    Manage a mailbox's export configurations and download their exports.

    An export config selects which columns (``items``) to export for the
    mailbox (``PARSER``) or one of its table fields (``PARSER_FIELD``). Use
    :meth:`available_fields` to discover the columns you can include, and
    :meth:`download` to fetch the resulting CSV/XLSX.
    """

    @classmethod
    def from_response(cls, data: Dict) -> Dict:
        """Validate/deserialize an export config and resolve its download URLs."""
        return resolve_absolute_urls(ExportConfigReadSchema().load(data))

    @classmethod
    def iter(cls, mailbox_id: int, *, api_key: Optional[str] = None) -> Iterable[Dict]:
        """Yield all export configurations of a mailbox (handles pagination)."""
        for raw in Client.paginate(
            f"/parser/{mailbox_id}/export_config", api_key=api_key
        ):
            yield cls.from_response(raw)

    @classmethod
    def list(
        cls, mailbox_id: int, *, api_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve all export configurations of a mailbox as a list."""
        return list(cls.iter(mailbox_id, api_key=api_key))

    @classmethod
    def retrieve(
        cls, mailbox_id: int, export_config_id: int, *, api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Retrieve a single export configuration by its ID."""
        raw = Client.request(
            "GET",
            f"/parser/{mailbox_id}/export_config/{export_config_id}",
            api_key=api_key,
        )
        return cls.from_response(raw)

    @classmethod
    def create(
        cls,
        mailbox_id: int,
        name: str,
        items: List[str],
        *,
        export_type: Union[str, ExportType] = ExportType.PARSER.value,
        parser_field_id: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create an export configuration.

        :param mailbox_id: ID of the mailbox.
        :param name: Name of the export configuration.
        :param items: Columns to export (see :meth:`available_fields`).
        :param export_type: ``PARSER`` (document-level) or ``PARSER_FIELD``
            (a table field). See :class:`ExportType`.
        :param parser_field_id: The table field id, required for
            ``PARSER_FIELD`` exports (e.g. "PF1").
        :param api_key: Optional API key overriding the global one for this call.
        :return: The created export configuration.
        :raises marshmallow.ValidationError: If a value is invalid.
        """
        body: Dict[str, Any] = {
            "name": name,
            "type": _export_type_value(export_type),
            "items": items,
        }
        if parser_field_id is not None:
            body["parser_field_id"] = parser_field_id
        payload = ExportConfigWriteSchema().load(body)
        raw = Client.request(
            "POST", f"/parser/{mailbox_id}/export_config", json=payload, api_key=api_key
        )
        return cls.from_response(raw)

    @classmethod
    def update(
        cls,
        mailbox_id: int,
        export_config_id: int,
        *,
        api_key: Optional[str] = None,
        **fields: Any,
    ) -> Dict[str, Any]:
        """
        Update an export configuration. Only the fields you pass are changed.

        :param fields: Writable fields (``name``, ``type``, ``items``,
            ``parser_field_id``).
        :raises marshmallow.ValidationError: If a value is invalid or an
            unknown field is provided.
        """
        if "type" in fields:
            fields["type"] = _export_type_value(fields["type"])
        payload = ExportConfigWriteSchema().load(fields)
        raw = Client.request(
            "PATCH",
            f"/parser/{mailbox_id}/export_config/{export_config_id}",
            json=payload,
            api_key=api_key,
        )
        return cls.from_response(raw)

    @classmethod
    def delete(
        cls, mailbox_id: int, export_config_id: int, *, api_key: Optional[str] = None
    ) -> bool:
        """Delete an export configuration. Returns True on success."""
        Client.request(
            "DELETE",
            f"/parser/{mailbox_id}/export_config/{export_config_id}",
            api_key=api_key,
        )
        return True

    @classmethod
    def available_fields(
        cls, mailbox_id: int, *, api_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List the groups of columns that can be exported for a mailbox.

        Returns one entry for the document-level export (``PARSER``) and one per
        table field (``PARSER_FIELD``), each with the ``items`` you can pass to
        :meth:`create`.
        """
        return Client.request(
            "GET", f"/parser/{mailbox_id}/export_fields", api_key=api_key
        )

    @classmethod
    def download(
        cls,
        mailbox_id: int,
        export_config_id: int,
        fmt: str = "csv",
        *,
        api_key: Optional[str] = None,
    ) -> bytes:
        """
        Download the configured export and return its raw bytes.

        :param fmt: ``"csv"`` (default) or ``"xlsx"`` (``"xls"`` is accepted).
        :return: The export file content as bytes.
        """
        key = download_url_field(fmt)
        config = cls.retrieve(mailbox_id, export_config_id, api_key=api_key)
        url = config.get(key)
        if not url:
            raise ValueError(f"No {key} available for export config {export_config_id}")
        return Client.download(url, api_key=api_key)
