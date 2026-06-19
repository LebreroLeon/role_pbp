from app.core.db_url import prepare_asyncpg_url


def test_neon_sslmode_is_mapped_to_asyncpg_ssl():
    url = (
        "postgresql+asyncpg://user:secret@"
        "ep-noisy-violet-assbeg1l-pooler.c-4.eu-central-1.aws.neon.tech/neondb"
        "?sslmode=require&channel_binding=require"
    )
    clean_url, connect_args = prepare_asyncpg_url(url)

    assert "sslmode" not in clean_url
    assert "channel_binding" not in clean_url
    assert connect_args == {"ssl": True}
    assert clean_url.startswith("postgresql+asyncpg://user:secret@")


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
