from pathlib import Path

from parseur.config import Config
from parseur.document import Document, DocumentOrderKey
from parseur.event import ParseurEvent
from parseur.mailbox import Mailbox, MailboxOrderKey
from parseur.schemas.document import DocumentStatus
from parseur.utils import to_json
from parseur.webhook import Webhook

__all__ = [
    "Config",
    "Document",
    "DocumentOrderKey",
    "DocumentStatus",
    "Mailbox",
    "MailboxOrderKey",
    "ParseurEvent",
    "Webhook",
    "to_json",
]


CONFIG_PATH = Path.home() / ".parseur.conf"
config = Config(CONFIG_PATH)
config.load()

DEFAULT_API_BASE = "https://api.parseur.com"

api_key = config.api_key
api_base = config.api_base or DEFAULT_API_BASE
