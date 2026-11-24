"""Fetch versioned engine binaries and weights for local experiments."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tarfile
from dataclasses import dataclass
from http.client import HTTPException
from importlib.resources import files
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class Artifact:
    description: str
    url: str
    sha256: str
    filename: str
    executable: bool = False
    tar_member: str | None = None
    file_sha256: str | None = None

    def __post_init__(self) -> None:
        if not all(
            isinstance(s, str) and s
            for s in (
                self.description,
                self.url,
                self.filename,
            )
        ):
            raise ValueError("description, url and filename must be nonempty strings")
        if urlsplit(self.url).scheme != "https" or not urlsplit(self.url).hostname:
            raise ValueError("url must be an HTTPS URL")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", self.filename):
            raise ValueError("filename must be a single filename")
        if not isinstance(self.executable, bool):
            raise ValueError("executable must be a boolean")
        if self.tar_member is not None and (
            not isinstance(self.tar_member, str) or not self.tar_member
        ):
            raise ValueError("tar_member must name a file")
        if (self.tar_member is None) != (self.file_sha256 is None):
            raise ValueError("tar_member and file_sha256 must be specified together")
        for digest in (self.sha256, self.installed_hash):
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError("expected a lowercase SHA-256 digest")

    @property
    def installed_hash(self) -> str:
        return self.sha256 if self.file_sha256 is None else self.file_sha256


def read_catalog(path: Path | None) -> dict[str, Artifact]:
    source = path or files("pychess.models").joinpath("catalog.json")
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("catalog must be a JSON object keyed by artifact name")
    catalog = {}
    for name, entry in data.items():
        try:
            catalog[name] = Artifact(**entry)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid catalog entry {name!r}: {exc}") from exc
    names = {entry.filename.casefold() for entry in catalog.values()}
    if len(names) != len(catalog):
        raise ValueError("catalog entries must have distinct filenames")
    return catalog


def _digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def fetch(artifact: Artifact, directory: Path) -> Path:
    """Install by atomic rename after verifying the download and selected file."""
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / artifact.filename
    if (
        not target.is_symlink()
        and target.is_file()
        and _digest(target) == artifact.installed_hash
    ):
        if artifact.executable:
            target.chmod(0o755)
        return target

    with TemporaryDirectory(dir=directory) as temp:
        payload = Path(temp) / "download"
        request = Request(artifact.url, headers={"User-Agent": "pyChess-models"})
        with urlopen(request, timeout=60) as response, payload.open("wb") as output:
            shutil.copyfileobj(response, output)
        if _digest(payload) != artifact.sha256:
            raise ValueError(f"SHA-256 mismatch downloading {artifact.filename}")
        if artifact.tar_member is not None:
            with tarfile.open(payload) as archive:
                member = archive.getmember(artifact.tar_member)
                if not member.isfile():
                    raise ValueError(f"Expected a regular file: {member.name}")
                payload = Path(temp) / "member"
                with archive.extractfile(member) as src, payload.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
            if _digest(payload) != artifact.installed_hash:
                raise ValueError(f"SHA-256 mismatch extracting {artifact.filename}")
        payload.chmod(0o755 if artifact.executable else 0o644)
        payload.replace(target)
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, help="use a custom JSON catalog")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="list available downloads")
    install = commands.add_parser("fetch", help="download engine binaries or weights")
    install.add_argument("names", nargs="+", metavar="NAME")
    install.add_argument("--directory", type=Path, default=Path(".pychess/models"))
    args = parser.parse_args(argv)
    try:
        catalog = read_catalog(args.catalog)
        if args.command == "list":
            for name, artifact in catalog.items():
                sys.stdout.write(f"{name}\t{artifact.description}\n")
        else:
            for name in args.names:
                if name not in catalog:
                    raise ValueError(f"Unknown artifact {name!r}. See list.")
                target = fetch(catalog[name], args.directory)
                sys.stdout.write(f"{name}\t{target.resolve()}\n")
    except (OSError, HTTPException, ValueError, tarfile.TarError, KeyError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
