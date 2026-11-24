"""Source registry: loading and validation (R01).

The registry is a versioned YAML file of Source records (abyss.core.contracts.Source).
Two files are used in Phase 0:

* data/registry/references.yaml        - documents cited as evidence by the taxonomy
* data/registry/ingestion_sources.yaml - APIs, feeds and datasets that Phase 1+ adapters may use
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import Field

from ..core.contracts import Source, _Strict

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCES_PATH = REPO_ROOT / "data" / "registry" / "references.yaml"
INGESTION_PATH = REPO_ROOT / "data" / "registry" / "ingestion_sources.yaml"


class RegistryFile(_Strict):
    registry_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    description: str
    sources: list[Source] = Field(min_length=1)


@dataclass(frozen=True)
class Registry:
    files: tuple[tuple[Path, str, RegistryFile], ...]  # (path, sha256, parsed)

    @property
    def sources(self) -> dict[str, Source]:
        out: dict[str, Source] = {}
        for _, _, f in self.files:
            for s in f.sources:
                out[s.id] = s
        return out

    def get(self, source_id: str) -> Source:
        return self.sources[source_id]


class RegistryError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_registry_file(path: Path) -> RegistryFile:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return RegistryFile.model_validate(data)


def load_registry(*paths: Path) -> Registry:
    paths = paths or (REFERENCES_PATH, INGESTION_PATH)
    files = []
    seen: dict[str, Path] = {}
    errors: list[str] = []
    for p in paths:
        rf = load_registry_file(p)
        for s in rf.sources:
            if s.id in seen:
                errors.append(f"duplicate source id {s.id!r} in {p.name} (first defined in {seen[s.id].name})")
            seen[s.id] = p
        files.append((p, sha256_file(p), rf))
    uris: dict[str, str] = {}
    for _, _, rf in files:
        for s in rf.sources:
            if s.uri in uris and uris[s.uri] != s.id:
                errors.append(f"sources {uris[s.uri]!r} and {s.id!r} share the URI {s.uri}")
            uris[s.uri] = s.id
    if errors:
        raise RegistryError("; ".join(errors))
    return Registry(files=tuple(files))
