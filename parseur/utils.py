from datetime import date, datetime
import json
from urllib.parse import urljoin

import parseur

ABSOLUTE_URL_FIELDS = {"csv_download", "json_download", "xls_download"}

DOWNLOAD_URL_FIELDS = {
    "csv": "csv_download",
    "json": "json_download",
    "xls": "xls_download",
    "xlsx": "xls_download",
}


def download_url_field(fmt):
    """Return the response key holding the download URL for an export format.

    :param fmt: ``"csv"``, ``"json"`` or ``"xlsx"`` (``"xls"`` is accepted).
    :raises ValueError: If the format is not supported.
    """
    try:
        return DOWNLOAD_URL_FIELDS[fmt]
    except KeyError:
        raise ValueError(f"Unsupported format {fmt!r}; use 'csv', 'json' or 'xlsx'.")


def resolve_absolute_urls(obj):
    if isinstance(obj, dict):
        for key in obj:
            if key in ABSOLUTE_URL_FIELDS and obj[key]:
                obj[key] = urljoin(parseur.api_base, obj[key])
            else:
                obj[key] = resolve_absolute_urls(obj[key])
    elif isinstance(obj, list):
        return [resolve_absolute_urls(item) for item in obj]
    return obj


class ISODateJSONEncoder(json.JSONEncoder):
    """
    JSON Encoder that converts datetime and date objects to ISO 8601 strings.
    """

    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


def to_json(data, indent=2, sort_keys=True, ensure_ascii=False):
    """
    Serialize a Python object to a JSON-formatted string with ISO datetime support.

    This function uses the custom ISODateJSONEncoder to automatically
    convert datetime.datetime objects to ISO 8601 strings.

    :param data: The data to serialize (dict, list, etc.).
    :param indent: Number of spaces to indent in the output JSON. Default is 2.
    :param sort_keys: Whether to sort the dictionary keys in the output. Default is True.
    :param ensure_ascii: Whether to escape non-ASCII characters. Default is False.
    :return: A JSON-formatted string.
    """
    return json.dumps(
        data,
        indent=indent,
        sort_keys=sort_keys,
        ensure_ascii=ensure_ascii,
        cls=ISODateJSONEncoder,
    )
