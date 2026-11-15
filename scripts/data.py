import re
import sys
import tarfile
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from narrative import utils

RAW_ROOT = utils.get_raw_data_dir()
PROC_ROOT = utils.get_proc_data_dir()

AI_INCIDENTS_REPORTS_URL = "https://incidentdatabase.ai/research/snapshots/"
AI_INCIDENTS_SNAPSHOT_RE = re.compile(r"backup-(\d{14})\.tar\.bz2$")
AI_INCIDENTS_RAW = RAW_ROOT


def acquire1() -> None:
    try:
        response = requests.get(AI_INCIDENTS_REPORTS_URL, timeout=15)
        response.raise_for_status()
    except requests.RequestException as error:
        sys.exit(f"Could not fetch {AI_INCIDENTS_REPORTS_URL}: {error}.")

    soup = BeautifulSoup(response.text, "html.parser")

    candidates = []
    for a in soup.find_all("a", href=True):
        m = AI_INCIDENTS_SNAPSHOT_RE.search(a["href"])
        if m:
            candidates.append((m.group(1), a["href"]))

    if not candidates:
        sys.exit("No snapshot links found; page structure may have changed.")

    _, url = max(candidates)

    AI_INCIDENTS_RAW.mkdir(parents=True, exist_ok=True)
    archive = AI_INCIDENTS_RAW / url.rsplit("/", 1)[-1]
    extract_dir = AI_INCIDENTS_RAW / archive.name.removesuffix(".tar.bz2")

    if not archive.exists():
        part = archive.with_name(archive.name + ".part")
        try:
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(part, "wb") as f:
                    f.writelines(r.iter_content(chunk_size=1 << 20))
        except requests.RequestException as error:
            sys.exit(f"Could not download {url}: {error}.")
        part.rename(archive)
    print(f"Wrote {archive}")

    if not extract_dir.exists():
        with tarfile.open(archive, "r:bz2") as tar:
            tar.extractall(extract_dir, filter="data")
    print(f"Extracted to {extract_dir}")


def transform1() -> Path:
    pass


def validate1() -> Path:
    pass


HUMAN_VALID_DATA_URL = "https://github.com/universe-szw/scientometric-llm-ethics-benchmark/blob/main/scoring_results/human_validation_scores_merged.csv"

DEEPSEEK_EVAL_URL = "https://github.com/universe-szw/scientometric-llm-ethics-benchmark/blob/main/scoring_results/deepseek_v4_pro_scores.csv"
DEEPSEEK_EVAL_CSV = RAW_ROOT / ""

QWEN_EVAL_URL = "https://github.com/universe-szw/scientometric-llm-ethics-benchmark/blob/main/scoring_results/qwen3_6_plus_scores.csv"
QWEN_EVAL_CSV = RAW_ROOT / ""

GPT_EVAL_URL = "https://github.com/universe-szw/scientometric-llm-ethics-benchmark/blob/main/scoring_results/gpt55_scores.csv"
GPT_EVAL_CSV = RAW_ROOT / ""


def _to_raw_github_url(url: str) -> str:
    """Converts GitHub blob URLs to raw.githubusercontent.com links for direct file downloads."""
    if "github.com" in url and "/blob/" in url:
        return url.replace("github.com", "raw.githubusercontent.com").replace(
            "/blob/", "/"
        )
    return url


def acquire2() -> None:
    eval_sources = {
        "human_validation_scores_merged.csv": HUMAN_VALID_DATA_URL,
        "deepseek_v4_pro_scores.csv": DEEPSEEK_EVAL_URL,
        "qwen3_6_plus_scores.csv": QWEN_EVAL_URL,
        "gpt55_scores.csv": GPT_EVAL_URL,
    }

    RAW_ROOT.mkdir(parents=True, exist_ok=True)

    for filename, url in eval_sources.items():
        raw_url = _to_raw_github_url(url)
        dest_path = RAW_ROOT / filename

        if dest_path.exists():
            print(f"File already exists: {dest_path}. Skipping download.")
            continue

        part_path = dest_path.with_name(dest_path.name + ".part")
        try:
            print(f"Downloading {filename} from {raw_url}...")
            with requests.get(raw_url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(part_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1 << 14):
                        if chunk:
                            f.write(chunk)
            part_path.rename(dest_path)
            print(f"Successfully saved to {dest_path}")
        except requests.RequestException as error:
            if part_path.exists():
                part_path.unlink(missing_ok=True)
            sys.exit(
                f"Could not download evaluation dataset {filename} from {raw_url}: {error}"
            )


# def transform2():


def main() -> None:
    acquire1()
    acquire2()


if __name__ == "__main__":
    main()
