"""Pre-registered benchmark definitions (metrics fixed before any data is seen).

Freezing definitions in a versioned file before experiments start prevents tuning the
definition to the result. Changing a definition after a run requires a new version and a
DECISION_LOG entry.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import Field

from ..core.contracts import _Strict
from .registry import REPO_ROOT

BENCHMARKS_PATH = REPO_ROOT / "data" / "benchmarks" / "definitions.yaml"


class Metric(_Strict):
    name: str
    definition: str = Field(min_length=10)


class Target(_Strict):
    metric: str
    comparator: Literal[">=", "<=", "==", ">", "<"]
    value: float
    source: str = Field(description="Where the target comes from, e.g. 'MASTER_AUDIT s9 (proposed)'")


class BenchmarkDefinition(_Strict):
    id: str = Field(pattern=r"^B\d{2}$")
    title: str
    phase: int = Field(ge=0, le=7)
    requirement_ids: list[str] = Field(min_length=1)
    test_ids: list[str] = Field(min_length=1)
    question: str = Field(min_length=10)
    unit_of_observation: str
    label_space: str
    dataset_plan: str
    split_protocol: str
    leakage_controls: list[str] = Field(min_length=1)
    metrics: list[Metric] = Field(min_length=1)
    baselines: list[str] = Field(min_length=1)
    proposed_targets: list[Target] = Field(default_factory=list)
    minimum_sample_size: str
    threshold_policy: str
    owner_dependencies: list[str] = Field(default_factory=list)
    status: Literal["defined_not_run", "running", "reported", "withdrawn"]
    result_ref: Optional[str] = None


class BenchmarkFile(_Strict):
    definitions_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    pre_registered: date
    description: str
    benchmarks: list[BenchmarkDefinition] = Field(min_length=1)


def load_benchmarks(path: Path = BENCHMARKS_PATH) -> BenchmarkFile:
    bf = BenchmarkFile.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    ids = [b.id for b in bf.benchmarks]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate benchmark ids")
    for b in bf.benchmarks:
        metric_names = {m.name for m in b.metrics}
        for t in b.proposed_targets:
            if t.metric not in metric_names:
                raise ValueError(f"{b.id}: target references undefined metric {t.metric!r}")
        if b.status == "reported" and not b.result_ref:
            raise ValueError(f"{b.id}: a reported benchmark must reference its result artifact")
    return bf
