from pathlib import Path

from parseur.config import Config
from parseur.document import (
    Document,
    DocumentOrderKey,
    FAILED_STATUSES,
    FINAL_STATUSES,
    PENDING_STATUSES,
)
from parseur.event import ParseurEvent
from parseur.export_config import ExportConfig
from parseur.mailbox import (
    EmailProcessing,
    Mailbox,
    MailboxOrderKey,
    Metadata,
    SenderFilter,
)
from parseur.parser_field import ParserField
from parseur.schemas.document import DocumentStatus
from parseur.schemas.export_config import ExportType
from parseur.schemas.mailbox import (
    AIEngine,
    DateFormat,
    DecimalSeparator,
    SUPPORTED_FILE_EXTENSIONS,
)
from parseur.schemas.paserfield import FieldFormat
from parseur.utils import to_json
from parseur.webhook import Webhook

__all__ = [
    "AIEngine",
    "Config",
    "DateFormat",
    "DecimalSeparator",
    "Document",
    "DocumentOrderKey",
    "DocumentStatus",
    "EmailProcessing",
    "ExportConfig",
    "ExportType",
    "FAILED_STATUSES",
    "FINAL_STATUSES",
    "FieldFormat",
    "Mailbox",
    "MailboxOrderKey",
    "Metadata",
    "PENDING_STATUSES",
    "ParseurEvent",
    "ParserField",
    "SUPPORTED_FILE_EXTENSIONS",
    "SenderFilter",
    "Webhook",
    "to_json",
]


CONFIG_PATH = Path.home() / ".parseur.conf"
config = Config(CONFIG_PATH)
config.load()

DEFAULT_API_BASE = "https://api.parseur.com"

api_key = config.api_key
api_base = config.api_base or DEFAULT_API_BASE
