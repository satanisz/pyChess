import hashlib
import io
import tarfile

import pytest

from pychess.models import download


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_tar_fetch_verifies_member_and_can_be_repeated_offline(tmp_path, monkeypatch):
    engine = b"example engine"
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as archive:
        member = tarfile.TarInfo("release/engine")
        member.size = len(engine)
        archive.addfile(member, io.BytesIO(engine))
    payload = buf.getvalue()
    artifact = download.Artifact(
        "Example",
        "https://example.org/engine.tar",
        digest(payload),
        "engine",
        executable=True,
        tar_member="release/engine",
        file_sha256=digest(engine),
    )
    monkeypatch.setattr(download, "urlopen", lambda *a, **kw: io.BytesIO(payload))
    target = download.fetch(artifact, tmp_path)
    assert target.read_bytes() == engine
    assert list(tmp_path.iterdir()) == [target]
    monkeypatch.setattr(download, "urlopen", lambda *a, **kw: pytest.fail("offline"))
    assert download.fetch(artifact, tmp_path) == target


def test_failed_verification_preserves_existing_file(tmp_path, monkeypatch):
    artifact = download.Artifact(
        "My net", "https://example.org/net", digest(b"new"), "net.bin"
    )
    target = tmp_path / artifact.filename
    target.write_bytes(b"old")
    monkeypatch.setattr(download, "urlopen", lambda *a, **kw: io.BytesIO(b"partial"))
    with pytest.raises(ValueError, match="SHA-256"):
        download.fetch(artifact, tmp_path)
    assert list(tmp_path.iterdir()) == [target]
    assert target.read_bytes() == b"old"
    monkeypatch.setattr(download, "urlopen", lambda *a, **kw: io.BytesIO(b"new"))
    assert download.fetch(artifact, tmp_path).read_bytes() == b"new"


def test_rejects_path_escaping_destination():
    with pytest.raises(ValueError, match="filename"):
        download.Artifact("Net", "https://example.org/net", digest(b""), "../net")


def test_bundled_catalog():
    catalog = download.read_catalog(None)
    assert catalog["maia-1100"].executable is False
    assert catalog["stockfish-18-linux-x64"].executable is True
