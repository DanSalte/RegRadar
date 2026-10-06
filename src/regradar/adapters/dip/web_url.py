"""Building block (DIP adapter): links to procedures on the DIP website."""

import re
from urllib.parse import quote

DIP_BASE_URL = "https://dip.bundestag.de"
_SLUG_WORDS = 10


def procedure_web_url(title: str, procedure_id: str) -> str:
    return f"{DIP_BASE_URL}/vorgang/{_slug(title)}/{procedure_id}"


def _slug(title: str) -> str:
    # Mirrors getCleanUrlEncodedTitle() of the DIP web frontend so that
    # links match the ones DIP itself generates.
    text = " ".join(title.split(" ")[:_SLUG_WORDS]).lower()
    text = re.sub(r"\s+", "-", text).replace("/", "-")
    text = re.sub(r"[^a-zäöüß0-9\-]+", "", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return quote(text, safe="-")
