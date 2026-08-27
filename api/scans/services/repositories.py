from urllib.parse import urlsplit, urlunsplit


def normalize_repository_url(value: str) -> str:
    """Return a stable exact-repository key without altering path case."""
    parsed = urlsplit(value.strip())
    scheme = (parsed.scheme or "https").lower()
    hostname = (parsed.hostname or "").lower()
    port = f":{parsed.port}" if parsed.port else ""
    path = parsed.path.rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    return urlunsplit((scheme, f"{hostname}{port}", path, "", ""))
