"""Build ATAK import URIs used by QR codes and 'Add to ATAK' links."""

from urllib.parse import quote

IMPORT_ENDPOINT = "tak://com.atakmap.app/import"


def build_import_uri(download_url: str) -> str:
    """Return the tak:// URI ATAK uses to fetch and import ``download_url``.

    ATAK 5.1+ parses ``tak://com.atakmap.app/import?url=<url-encoded URL>``.
    The url value is fully percent-encoded (``safe=""``) so its own ``:`` and
    ``/`` cannot confuse the outer URI parser.
    """
    return f"{IMPORT_ENDPOINT}?url={quote(download_url, safe='')}"
