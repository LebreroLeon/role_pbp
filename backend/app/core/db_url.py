"""Normalize DATABASE_URL for SQLAlchemy + asyncpg (Neon/libpq query params)."""

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

# libpq-only params that asyncpg.connect() rejects as keyword arguments.
_STRIP_QUERY_PARAMS = frozenset({"sslmode", "channel_binding"})

_SSLMODE_TO_ASYNCPG_SSL: dict[str, bool] = {
    "disable": False,
    "allow": False,
    "prefer": True,
    "require": True,
    "verify-ca": True,
    "verify-full": True,
}


def _is_neon_host(hostname: str | None) -> bool:
    return bool(hostname and hostname.endswith(".neon.tech"))


def prepare_asyncpg_url(database_url: str) -> tuple[str, dict]:
    """Return (url, connect_args) safe for create_async_engine with asyncpg."""
    parsed = urlparse(database_url)
    query = parse_qs(parsed.query, keep_blank_values=True)

    connect_args: dict = {}
    if "sslmode" in query:
        sslmode = query.pop("sslmode")[-1].lower()
        if sslmode in _SSLMODE_TO_ASYNCPG_SSL:
            connect_args["ssl"] = _SSLMODE_TO_ASYNCPG_SSL[sslmode]

    for key in _STRIP_QUERY_PARAMS:
        query.pop(key, None)

    # Neon always requires TLS; asyncpg ignores libpq sslmode unless we pass ssl=.
    if "ssl" not in connect_args and _is_neon_host(parsed.hostname):
        connect_args["ssl"] = True

    flat_query = urlencode([(key, values[-1]) for key, values in sorted(query.items())])
    clean_url = urlunparse(parsed._replace(query=flat_query))
    return clean_url, connect_args
