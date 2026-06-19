"""Normalize DATABASE_URL for SQLAlchemy + asyncpg (Neon/libpq query params)."""

import ssl
from ssl import SSLContext
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

# libpq-only params that asyncpg.connect() rejects as keyword arguments.
_STRIP_QUERY_PARAMS = frozenset({"sslmode", "channel_binding"})

# sslmode values asyncpg accepts as the ssl= argument (see asyncpg docs).
_SSLMODE_STRINGS = frozenset({"allow", "prefer", "verify-ca", "verify-full"})


def asyncpg_ssl_require_context() -> SSLContext:
    """SSL context equivalent to libpq sslmode=require (Neon pooler)."""
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _asyncpg_ssl_for_sslmode(sslmode: str) -> bool | str | SSLContext:
    mode = sslmode.lower()
    if mode == "disable":
        return False
    if mode == "require":
        return asyncpg_ssl_require_context()
    if mode in _SSLMODE_STRINGS:
        return mode
    return asyncpg_ssl_require_context()


def _is_neon_host(hostname: str | None) -> bool:
    return bool(hostname and hostname.endswith(".neon.tech"))


def prepare_asyncpg_url(database_url: str) -> tuple[str, dict]:
    """Return (url, connect_args) safe for create_async_engine with asyncpg."""
    parsed = urlparse(database_url)
    query = parse_qs(parsed.query, keep_blank_values=True)

    connect_args: dict = {}
    if "sslmode" in query:
        sslmode = query.pop("sslmode")[-1]
        connect_args["ssl"] = _asyncpg_ssl_for_sslmode(sslmode)

    for key in _STRIP_QUERY_PARAMS:
        query.pop(key, None)

    # Neon always requires TLS; asyncpg defaults to ssl='prefer' (may fall back to plain).
    if "ssl" not in connect_args and _is_neon_host(parsed.hostname):
        connect_args["ssl"] = asyncpg_ssl_require_context()

    flat_query = urlencode([(key, values[-1]) for key, values in sorted(query.items())])
    clean_url = urlunparse(parsed._replace(query=flat_query))
    return clean_url, connect_args
