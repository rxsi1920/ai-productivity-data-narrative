"""data/dictionary.yml must match the data in data/ and follow the A2 Part C manifest rules for sources and datasets."""

import importlib.util
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_dictionary", ROOT / "scripts" / "build_dictionary.py")
build_dictionary = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_dictionary)

MANIFEST = yaml.safe_load((ROOT / "data" / "dictionary.yml").read_text(encoding="utf-8"))
SOURCE_FIELDS = {"id", "publisher", "title", "url", "licence", "retrieved", "cadence", "status"}
DATASET_FIELDS = {"id", "source_ids", "sample", "processed_output", "primary_key", "columns"}


def test_dictionary_is_up_to_date():
    # Re-running scripts/build_dictionary.py must reproduce the committed file.
    assert build_dictionary.build() == MANIFEST, "run: python scripts/build_dictionary.py"


def test_every_processed_file_is_documented():
    files = {p.relative_to(ROOT).as_posix() for p in (ROOT / "data" / "processed").rglob("*.csv")}
    declared = {d["processed_output"] for d in MANIFEST["datasets"]}
    assert files == declared


def test_required_fields_and_references():
    source_ids = {s["id"] for s in MANIFEST["sources"]}
    for source in MANIFEST["sources"]:
        assert SOURCE_FIELDS <= source.keys(), source["id"]
        assert source["status"] in {"live", "archive", "licensed", "snapshot"}
    for dataset in MANIFEST["datasets"]:
        assert DATASET_FIELDS <= dataset.keys(), dataset["id"]
        assert set(dataset["source_ids"]) <= source_ids, dataset["id"]
        assert (ROOT / dataset["sample"]).exists(), dataset["sample"]
        assert dataset["id"] in MANIFEST["transforms"]


def test_keys_and_latest_observation_match_the_data():
    for dataset in MANIFEST["datasets"]:
        frame = pd.read_csv(ROOT / dataset["processed_output"], dtype=object, keep_default_na=False, na_values=[""])
        assert list(frame.columns) == list(dataset["columns"]), dataset["id"]
        assert not frame.duplicated(dataset["primary_key"]).any(), dataset["id"]
        if "date_column" in dataset:
            latest = pd.to_datetime(frame[dataset["date_column"]], utc=True).max().date().isoformat()
            assert latest == dataset["latest_observation"], dataset["id"]
