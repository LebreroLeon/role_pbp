import ssl

from app.core.db_url import asyncpg_ssl_require_context, prepare_asyncpg_url


def _assert_require_context(ctx: object) -> None:
    assert isinstance(ctx, ssl.SSLContext)
    assert ctx.check_hostname is False
    assert ctx.verify_mode == ssl.CERT_NONE


def test_neon_sslmode_is_mapped_to_asyncpg_ssl():
    url = (
        "postgresql+asyncpg://user:secret@"
        "ep-noisy-violet-assbeg1l-pooler.c-4.eu-central-1.aws.neon.tech/neondb"
        "?sslmode=require&channel_binding=require"
    )
    clean_url, connect_args = prepare_asyncpg_url(url)

    assert "sslmode" not in clean_url
    assert "channel_binding" not in clean_url
    _assert_require_context(connect_args["ssl"])
    assert clean_url.startswith("postgresql+asyncpg://user:secret@")


def test_neon_host_without_sslmode_enables_ssl():
    url = (
        "postgresql+asyncpg://neondb_owner:secret@"
        "ep-noisy-violet-assbeg1l-pooler.c-4.eu-central-1.aws.neon.tech/neondb"
    )
    clean_url, connect_args = prepare_asyncpg_url(url)

    assert clean_url == url
    _assert_require_context(connect_args["ssl"])


def test_local_url_without_sslmode_unchanged():
    url = "postgresql+asyncpg://rolepbp:rolepbp@localhost:5432/rolepbp"
    clean_url, connect_args = prepare_asyncpg_url(url)

    assert clean_url == url
    assert connect_args == {}


def test_sslmode_disable():
    url = "postgresql+asyncpg://user:pass@host/db?sslmode=disable"
    clean_url, connect_args = prepare_asyncpg_url(url)

    assert "sslmode" not in clean_url
    assert connect_args == {"ssl": False}


def test_sslmode_verify_full_uses_asyncpg_string():
    url = "postgresql+asyncpg://user:pass@host/db?sslmode=verify-full"
    clean_url, connect_args = prepare_asyncpg_url(url)

    assert "sslmode" not in clean_url
    assert connect_args == {"ssl": "verify-full"}


def test_asyncpg_ssl_require_context_matches_sslmode_require():
    ctx = asyncpg_ssl_require_context()
    _assert_require_context(ctx)
