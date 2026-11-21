"""Processed files for Profitability and Moral degradation must rebuild from data/raw/ exactly as committed.

Each test runs the real build into an empty temporary folder, offline, and compares every file byte for byte with
data/processed/. A file the build does not recreate, or recreates differently, fails the test.
(The feedback-loop page has the same check in test_human_practice_data.py.)
"""

import importlib.util
import socket
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

MORAL_FILES = [
    "ai_incidents.csv",
    "ai_reports.csv",
    "classifications_GMF.csv",
    "human_validation_scores_merged.csv",
    "ai_validation_scores_merged.csv",
    "GIRAI_Frameworks.csv",
    "GIRAI_Classifications.csv",
    "Ipsos_gov_trust.csv",
    "Ipsos_comp_trust.csv",
    "Ipsos_ai_env_trust.csv",
    "Ipsos_job_sec_trust.csv",
    "ai_policy_and_ethics.csv",
    "salary_and_satisfaction.csv",
    "study2_responses.csv",
    "study3_responses.redacted.csv",
]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def offline(monkeypatch):
    """Fail loudly if a build step tries to download anything: rebuilding must work from data/raw/ alone."""

    def refuse(*args, **kwargs):
        raise RuntimeError("network access during a rebuild from raw")

    monkeypatch.setattr(socket.socket, "connect", refuse)


def _assert_same(built: Path, names) -> None:
    for name in names:
        rebuilt = built / name
        assert rebuilt.exists(), f"{name} was not rebuilt"
        assert rebuilt.read_bytes() == (PROCESSED / name).read_bytes(), f"{name} differs from data/processed/"


def test_profitability_rebuilds_from_raw(tmp_path, monkeypatch, offline):
    build = _load("build_processed", ROOT / "src" / "narrative" / "tabs" / "profitability" / "build_processed.py")
    monkeypatch.setattr(build, "OUT", tmp_path)
    build.build_profitability()
    _assert_same(tmp_path, build.PROFIT_FILES)


def test_moral_degradation_rebuilds_from_raw(tmp_path, monkeypatch, offline):
    data = _load("moral_data", ROOT / "scripts" / "data.py")
    # Point every processed-file path in scripts/data.py at the temporary folder.
    proc_root = data.PROC_ROOT.resolve()
    for name, value in list(vars(data).items()):
        if isinstance(value, Path) and value.resolve().parent == proc_root:
            monkeypatch.setattr(data, name, tmp_path / value.name)
    monkeypatch.setattr(data, "PROC_ROOT", tmp_path)

    for step in (data.transform1, data.transform2, data.transform3, data.transform4, data.transform5,
                 data.transform6):
        step()
    _assert_same(tmp_path, MORAL_FILES)
