import hashlib
import re
from urllib.parse import urlparse, urlunparse


def canonical_url(url: str) -> str:
    parsed = urlparse(url)
    # Drop fragments and tracking params
    query = re.sub(r"(^|&)(utm_[^=]+=[^&]*)", "", parsed.query)
    normalized = parsed._replace(query=query, fragment="")
    return urlunparse(normalized)


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
