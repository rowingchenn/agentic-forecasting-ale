"""The ALE-published images this engine uses, pinned by release version.

``releases.json`` beside this module is the one place a version is written. For every
image it records the release this engine uses and a hash of the sources that release
was built from. A published release never changes: editing an image's sources without
giving it a new version fails the image lock test, and CI publishes only versions the
registry does not have yet. Task Dockerfiles pin a base release the same way, so an
engine update never changes the image an existing Task builds from.

Run as a script it prints the releases for ``images/build.sh`` and the publishing
workflow (``--json``), or one image's reference (``--reference NAME``), using only the
standard library.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from functools import cache
from pathlib import Path

__all__ = ["REGISTRY", "ImageRelease", "reference", "releases", "source_content"]

REGISTRY = "ghcr.io/agentslastexam"
VERSION = re.compile(r"\d+\.\d+\.\d+")
_LOCK = Path(__file__).with_name("releases.json")


@dataclass(frozen=True)
class ImageRelease:
    repository: str
    version: str
    content: str
    dockerfile: str
    context: str
    inputs: tuple[str, ...]

    @property
    def reference(self) -> str:
        return f"{REGISTRY}/{self.repository}:{self.version}"


@cache
def releases() -> dict[str, ImageRelease]:
    loaded = json.loads(_LOCK.read_text(encoding="utf-8"))
    found = {
        repository: ImageRelease(
            repository=repository,
            version=entry["version"],
            content=entry["content"],
            dockerfile=entry["dockerfile"],
            context=entry["context"],
            inputs=tuple(entry["inputs"]),
        )
        for repository, entry in loaded.items()
    }
    for release in found.values():
        if not VERSION.fullmatch(release.version):
            raise ValueError(f"{release.repository} version {release.version!r} is not X.Y.Z")
    return found


def reference(repository: str) -> str:
    """The exact published reference this engine uses for an ALE image."""
    return releases()[repository].reference


def source_content(release: ImageRelease, root: Path) -> str:
    """Hash an image's committed sources the way the publishing workflow does."""
    listing = subprocess.run(
        ["git", "ls-files", "-s", "--", *release.inputs],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout
    return hashlib.sha256(listing).hexdigest()[:12]


def _main(argv: list[str]) -> int:
    if argv == ["--json"]:
        print(json.dumps([_row(release) for release in releases().values()]))
        return 0
    if len(argv) == 2 and argv[0] == "--reference" and argv[1] in releases():
        print(reference(argv[1]))
        return 0
    for name in argv or list(releases()):
        release = releases().get(name)
        if release is None:
            print(f"unknown image: {name}", file=sys.stderr)
            return 1
        print(release.repository, release.version, release.content, release.dockerfile,
              release.context, *release.inputs)  # fmt: skip
    return 0


def _row(release: ImageRelease) -> dict[str, str]:
    return {
        "repository": release.repository,
        "version": release.version,
        "content": release.content,
        "dockerfile": release.dockerfile,
        "context": release.context,
        "inputs": " ".join(release.inputs),
    }


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
