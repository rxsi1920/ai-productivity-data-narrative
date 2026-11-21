############################################################################################################################
# --------------------------------------- MORAL DEGRADATION ----------------------------------------------------------------
############################################################################################################################

import re
import shutil
import sys
import tarfile
from pathlib import Path

import gdown
import kagglehub
import pandas as pd
import pdfplumber
import requests
from bs4 import BeautifulSoup

from narrative import utils

RAW_ROOT = utils.get_raw_data_dir()
PROC_ROOT = utils.get_proc_data_dir()

## AI INCIDENTS DATASET
AI_INCIDENTS_REPORTS_URL = "https://incidentdatabase.ai/research/snapshots/"
AI_INCIDENTS_SNAPSHOT_RE = re.compile(r"backup-(\d{14})\.tar\.bz2$")
AI_INCIDENTS_RAW = RAW_ROOT / "ai_incidents" / "mongodump_full_snapshot"

AI_INCIDENTS_INCIDENTS_RAW = AI_INCIDENTS_RAW / "incidents.csv"
AI_INCIDENTS_REPORTS_RAW = AI_INCIDENTS_RAW / "reports.csv"
AI_INCIDENTS_INCIDENTS_PROC = PROC_ROOT / "ai_incidents.csv"
AI_INCIDENTS_REPORTS_PROC = PROC_ROOT / "ai_reports.csv"
# GMF taxonomy classifications (AIID export, kept as downloaded). Not in every snapshot archive, so acquire1
# only needs it when the raw copy is missing; it is then exported from https://incidentdatabase.ai/taxonomies/gmf/.
AI_INCIDENTS_GMF_RAW = AI_INCIDENTS_RAW / "classifications_GMF.csv"
AI_INCIDENTS_GMF_PROC = PROC_ROOT / "classifications_GMF.csv"


def acquire1() -> None:
    remaining = {
        "incidents.csv": AI_INCIDENTS_INCIDENTS_RAW,
        "reports.csv": AI_INCIDENTS_REPORTS_RAW,
    }

    if all(p.exists() for p in remaining.values()):
        print(f"Files already present in {AI_INCIDENTS_RAW}")
        return

    remaining = {n: p for n, p in remaining.items() if not p.exists()}

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

    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            r.raw.decode_content = True
            with tarfile.open(fileobj=r.raw, mode="r|bz2") as tar:
                for member in tar:
                    if not member.isfile():
                        continue
                    path = Path(member.name)
                    if path.parent.name != AI_INCIDENTS_RAW.name:
                        continue
                    dest = remaining.get(path.name)
                    if dest is None:
                        continue

                    part = dest.with_name(dest.name + ".part")
                    try:
                        with open(part, "wb") as f:
                            shutil.copyfileobj(tar.extractfile(member), f)
                        part.replace(dest)
                    finally:
                        part.unlink(missing_ok=True)

                    print(f"Wrote {dest}")
                    del remaining[path.name]
                    if not remaining:
                        break
    except (requests.RequestException, tarfile.TarError) as error:
        sys.exit(f"Could not download {url}: {error}.")

    if remaining:
        sys.exit(f"Not found in archive: {', '.join(remaining)}.")


def transform1() -> Path:
    PROC_ROOT.mkdir(parents=True, exist_ok=True)

    if not AI_INCIDENTS_INCIDENTS_RAW.exists():
        print(f"Missing file: {AI_INCIDENTS_INCIDENTS_RAW}")
    if not AI_INCIDENTS_REPORTS_RAW.exists():
        print(f"Missing file: {AI_INCIDENTS_REPORTS_RAW}")

    df = pd.read_csv(AI_INCIDENTS_INCIDENTS_RAW, usecols=["_id", "date"])
    df.to_csv(AI_INCIDENTS_INCIDENTS_PROC, index=False)

    df = pd.read_csv(
        AI_INCIDENTS_REPORTS_RAW, usecols=["_id", "date_published", "date_submitted"]
    )
    df.to_csv(AI_INCIDENTS_REPORTS_PROC, index=False)

    # GMF classifications are used unchanged.
    if AI_INCIDENTS_GMF_RAW.exists():
        shutil.copyfile(AI_INCIDENTS_GMF_RAW, AI_INCIDENTS_GMF_PROC)
    else:
        print(
            f"Missing file: {AI_INCIDENTS_GMF_RAW} (export it from https://incidentdatabase.ai/taxonomies/gmf/)"
        )


def validate1() -> Path:
    pass


## HUMAN VS AI EVALUATION DATASETS

HUMAN_VALID_DATA_URL = "https://github.com/universe-szw/scientometric-llm-ethics-benchmark/blob/main/scoring_results/human_validation_scores_merged.csv"

DEEPSEEK_EVAL_URL = "https://github.com/universe-szw/scientometric-llm-ethics-benchmark/blob/main/scoring_results/deepseek_v4_pro_scores.csv"
DEEPSEEK_EVAL_CSV = RAW_ROOT / "deepseek_v4_pro_scores.csv"

QWEN_EVAL_URL = "https://github.com/universe-szw/scientometric-llm-ethics-benchmark/blob/main/scoring_results/qwen3_6_plus_scores.csv"
QWEN_EVAL_CSV = RAW_ROOT / "qwen3_6_plus_scores.csv"

GPT_EVAL_URL = "https://github.com/universe-szw/scientometric-llm-ethics-benchmark/blob/main/scoring_results/gpt55_scores.csv"
GPT_EVAL_CSV = RAW_ROOT / "gpt55_scores.csv"

COMBINED_AI_CSV = PROC_ROOT / "ai_validation_scores_merged.csv"


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


def transform2():
    eval_sources = {
        "deepseek_v4_pro_scores.csv": DEEPSEEK_EVAL_CSV,
        "qwen3_6_plus_scores.csv": QWEN_EVAL_CSV,
        "gpt55_scores.csv": GPT_EVAL_CSV,
    }

    df = pd.concat(
        (pd.read_csv(filepath) for filepath in eval_sources.values()), ignore_index=True
    )
    df.to_csv(COMBINED_AI_CSV, index=False)


### GIRAI COUNTRY CLASSIFICATION

GIRAI_FILE_ID = "1eKFvl-mfAeAqrHv8j11p5ItHznZRRbaD"
GIRAI_FILE_OUT = RAW_ROOT / "GIRAI_Global_Survey_dataset.xlsx"
GIRAI_FRAMEWORK_CSV = PROC_ROOT / "GIRAI_Frameworks.csv"
GIRAI_CLASSIFICATION_CSV = PROC_ROOT / "GIRAI_Classifications.csv"


def acquire3() -> None:
    if GIRAI_FILE_OUT.is_file():
        print(f"File already exists: {GIRAI_FILE_OUT}. Skipping download.")
        return
    gdown.download(id=GIRAI_FILE_ID, output=str(GIRAI_FILE_OUT), quiet=False)


def transform3() -> None:
    pd.read_excel(GIRAI_FILE_OUT, sheet_name="frameworks").to_csv(GIRAI_FRAMEWORK_CSV)
    pd.read_excel(GIRAI_FILE_OUT, sheet_name="country_classifications").to_csv(
        GIRAI_CLASSIFICATION_CSV
    )


### IPSOS GENERAL TRUST DATASETS

IPSOS_AI_2025 = "https://www.ipsos.com/sites/default/files/ct/publication/documents/2025-06/Ipsos-AI-Monitor-2025.pdf"
IPSOS_AI_2026 = "https://www.ipsos.com/sites/default/files/ct/news/documents/2026-06/Ipsos-AI-Monitor-2026.pdf"
IPSOS_AI_2025_RAW = RAW_ROOT / "Ipsos-AI-Monitor-2025.pdf"
IPSOS_AI_2026_RAW = RAW_ROOT / "Ipsos-AI-Monitor-2026.pdf"
IPSOS_TRUST_GOV_PROC = PROC_ROOT / "Ipsos_gov_trust.csv"
IPSOS_TRUST_COMP_PROC = PROC_ROOT / "Ipsos_comp_trust.csv"
IPSOS_AI_TRUST_ENV_PROC = PROC_ROOT / "Ipsos_ai_env_trust.csv"
IPSOS_JOB_SEC_TRUST_PROC = PROC_ROOT / "Ipsos_job_sec_trust.csv"


def acquire4() -> None:
    for url, path in [
        (IPSOS_AI_2025, IPSOS_AI_2025_RAW),
        (IPSOS_AI_2026, IPSOS_AI_2026_RAW),
    ]:
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            path.write_bytes(response.content)


def group_lines(words, tol=3):
    words = sorted(words, key=lambda w: w["top"])
    lines, current, current_top = [], [], None
    for w in words:
        if current_top is None or abs(w["top"] - current_top) <= tol:
            current.append(w)
            if current_top is None:
                current_top = w["top"]
        else:
            lines.append(current)
            current, current_top = [w], w["top"]
    if current:
        lines.append(current)
    return lines


def transform4() -> None:

    ##### GOV TRUST

    with pdfplumber.open(IPSOS_AI_2025_RAW) as pdf:
        page = pdf.pages[22]
        words = page.extract_words()

    known_countries = [
        "30-country average",
        "Singapore",
        "Indonesia",
        "Malaysia",
        "Thailand",
        "Chile",
        "Mexico",
        "Colombia",
        "India",
        "Poland",
        "Argentina",
        "Peru",
        "Spain",
        "Switzerland",
        "South Africa",
        "Italy",
        "Belgium",
        "Ireland",
        "Germany",
        "Netherlands",
        "Türkiye",
        "Brazil",
        "South Korea",
        "Australia",
        "Sweden",
        "France",
        "Canada",
        "Great Britain",
        "Hungary",
        "Japan",
        "United States",
    ]

    data = []
    for line in group_lines(words):
        row_words = sorted(line, key=lambda w: w["x0"])
        stats = [w["text"].replace("%", "") for w in row_words if "%" in w["text"]]
        row_text = " ".join([w["text"] for w in row_words])

        found_country = None
        for c in known_countries:
            if c in row_text:
                found_country = c
                break

        if found_country and len(stats) >= 3:
            data.append(
                {
                    "Country": found_country,
                    "Agree": stats[0],
                    "Unsure": stats[1],
                    "Disagree": stats[2],
                }
            )

    df = pd.DataFrame(data)
    df.to_csv(IPSOS_TRUST_GOV_PROC, index=False)

    ## COMP TRUST
    with pdfplumber.open(IPSOS_AI_2026_RAW) as pdf:
        page = pdf.pages[16]
        words = page.extract_words()

    known_countries = [
        "32-Country Average",
        "India",
        "China",
        "Thailand",
        "South Africa",
        "Italy",
        "Malaysia",
        "Indonesia",
        "Peru",
        "Hungary",
        "Colombia",
        "Mexico",
        "Singapore",
        "Spain",
        "Argentina",
        "Ireland",
        "Poland",
        "Netherlands",
        "Türkiye",
        "Chile",
        "Brazil",
        "Germany",
        "New Zealand",
        "Israel",
        "Belgium",
        "Australia",
        "Great Britain",
        "South Korea",
        "United States",
        "Sweden",
        "Japan",
        "Canada",
        "France",
    ]

    data = []
    for line in group_lines(words):
        row_words = sorted(line, key=lambda w: w["x0"])
        stats = [w["text"].replace("%", "") for w in row_words if "%" in w["text"]]
        row_text = " ".join([w["text"] for w in row_words])

        found_country = None
        for c in known_countries:
            if c in row_text:
                found_country = c
                break

        if found_country and len(stats) >= 2:
            data.append(
                {"Country": found_country, "Agree": stats[0], "Disagree": stats[1]}
            )

    df = pd.DataFrame(data)
    df.to_csv(IPSOS_TRUST_COMP_PROC, index=False)

    ## ENV TRUST
    with pdfplumber.open(IPSOS_AI_2026_RAW) as pdf:
        page = pdf.pages[20]
        words = page.extract_words()

    known_countries = [
        "32-Country Average",
        "China",
        "India",
        "Thailand",
        "Indonesia",
        "South Korea",
        "Peru",
        "Malaysia",
        "South Africa",
        "Türkiye",
        "Singapore",
        "Israel",
        "Mexico",
        "Chile",
        "Colombia",
        "Hungary",
        "Italy",
        "Argentina",
        "Japan",
        "Poland",
        "Spain",
        "Brazil",
        "Ireland",
        "Sweden",
        "Belgium",
        "Australia",
        "New Zealand",
        "United States",
        "Great Britain",
        "France",
        "Germany",
        "Netherlands",
        "Canada",
    ]

    data = []
    for line in group_lines(words):
        row_words = sorted(line, key=lambda w: w["x0"])
        stats = [w["text"].replace("%", "") for w in row_words if "%" in w["text"]]
        row_text = " ".join([w["text"] for w in row_words])

        found_country = None
        for c in known_countries:
            if c in row_text:
                found_country = c
                break

        if found_country and len(stats) >= 2:
            data.append(
                {"Country": found_country, "Agree": stats[0], "Disagree": stats[1]}
            )

    df = pd.DataFrame(data)
    df.to_csv(IPSOS_AI_TRUST_ENV_PROC, index=False)

    ## JOB SECURITY
    with pdfplumber.open(IPSOS_AI_2026_RAW) as pdf:
        page = pdf.pages[25]
        words = page.extract_words()

    known_countries = [
        "32-Country Average",
        "Thailand",
        "Malaysia",
        "India",
        "Indonesia",
        "China",
        "South Africa",
        "Singapore",
        "Türkiye",
        "Colombia",
        "Brazil",
        "Peru",
        "South Korea",
        "Mexico",
        "Argentina",
        "Chile",
        "Japan",
        "Hungary",
        "Spain",
        "Ireland",
        "Israel",
        "Italy",
        "United States",
        "New Zealand",
        "Australia",
        "Great Britain",
        "Belgium",
        "Poland",
        "Canada",
        "France",
        "Sweden",
        "Netherlands",
        "Germany",
    ]

    data = []
    for line in group_lines(words):
        row_words = sorted(line, key=lambda w: w["x0"])
        stats = [w["text"].replace("%", "") for w in row_words if "%" in w["text"]]
        row_text = " ".join([w["text"] for w in row_words])

        found_country = None
        for c in known_countries:
            if c in row_text:
                found_country = c
                break

        if found_country and len(stats) >= 1:
            data.append(
                {
                    "Country": found_country,
                    "Agree": stats[0],
                    "Disagree": stats[1] if len(stats) > 1 else "",
                }
            )

    df = pd.DataFrame(data)
    df.to_csv(IPSOS_JOB_SEC_TRUST_PROC, index=False)


## GLOBAL SURVEY HUB - Global AI Adoption & Workforce Impact Survey 24-26
GLOB_PROD_URL = (
    "meruvakodandasuraj/global-ai-adoption-and-workforce-impact-survey-24-26"
)

SKILLS_TRAINING_RAW = RAW_ROOT / "skills_and_training.csv"
SKILLS_TRAINING_PROC = PROC_ROOT / "skills_and_training.csv"
AI_POLICY_RAW = RAW_ROOT / "ai_policy_and_ethics.csv"
AI_POLICY_PROC = PROC_ROOT / "ai_policy_and_ethics.csv"
SALARY_SATISFACTION_RAW = RAW_ROOT / "salary_and_satisfaction.csv"
SALARY_SATISFACTION_PROC = PROC_ROOT / "salary_and_satisfaction.csv"


def acquire5() -> None:
    required = [SKILLS_TRAINING_RAW, AI_POLICY_RAW, SALARY_SATISFACTION_RAW]
    if all(p.exists() for p in required):
        print(f"Files already present in {RAW_ROOT}")
        return

    cache_path = Path(kagglehub.dataset_download(GLOB_PROD_URL))
    RAW_ROOT.mkdir(parents=True, exist_ok=True)

    for item in cache_path.iterdir():
        target_path = RAW_ROOT / item.name

        if target_path.exists():
            continue

        if item.is_dir():
            shutil.copytree(item, target_path)
        else:
            shutil.copy2(item, target_path)

    print(f"Successfully moved dataset files to: {RAW_ROOT}")


def transform5() -> None:
    shutil.copy2(AI_POLICY_RAW, AI_POLICY_PROC)
    shutil.copy2(SALARY_SATISFACTION_RAW, SALARY_SATISFACTION_PROC)


## SYCOPHANCY DATASETS
SYCOPHANCY_BASE = "https://files.osf.io/v1/resources/smvw7/providers/osfstorage/"
SYCOPHANCY_VIEW_ONLY = "ad71a7201c71477d921000c90c565da7"
SYCOPHANCY_FOLDER = "Data"
SYCOPHANCY_FILES = [
    "study2_responses.csv",
    "study3_responses.redacted.csv",
]

SYCO_STUDY2_RAW = RAW_ROOT / "study2_responses.csv"
SYCO_STUDY3_RAW = RAW_ROOT / "study3_responses.redacted.csv"
SYCO_STUDY2_PROC = PROC_ROOT / "study2_responses.csv"
SYCO_STUDY3_PROC = PROC_ROOT / "study3_responses.redacted.csv"


def _list_items(path: str = "") -> list[dict]:
    items = []
    url = f"{SYCOPHANCY_BASE}{path}"
    params = {"view_only": SYCOPHANCY_VIEW_ONLY, "meta": ""}
    while url:
        r = requests.get(url, params=params, timeout=60)
        r.raise_for_status()
        payload = r.json()
        items.extend(payload["data"])
        url = payload.get("links", {}).get("next")
        params = None
    return items


def acquire6() -> None:
    RAW_ROOT.mkdir(parents=True, exist_ok=True)

    targets = {name: RAW_ROOT / name for name in SYCOPHANCY_FILES}
    if all(p.exists() for p in targets.values()):
        print("[acquire6] Files already present")
        return

    folder = next(
        (
            i
            for i in _list_items()
            if i["attributes"]["kind"] == "folder"
            and i["attributes"]["name"] == SYCOPHANCY_FOLDER
        ),
        None,
    )
    if folder is None:
        raise FileNotFoundError(f"Folder {SYCOPHANCY_FOLDER} not found")

    folder_path = folder["attributes"]["path"].lstrip("/")
    files = {
        i["attributes"]["name"]: i
        for i in _list_items(folder_path)
        if i["attributes"]["kind"] == "file"
    }

    for name, dest in targets.items():
        if dest.exists():
            continue
        item = files.get(name)
        if item is None:
            raise FileNotFoundError(f"{name} not found in {SYCOPHANCY_FOLDER}/")

        download_url = item["links"]["download"]
        print(f"Downloading {name}")
        tmp = dest.with_suffix(dest.suffix + ".part")
        try:
            with requests.get(
                download_url,
                params={"view_only": SYCOPHANCY_VIEW_ONLY},
                stream=True,
                timeout=60,
            ) as r:
                r.raise_for_status()
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
            tmp.replace(dest)
            print(f"Saved {dest}")
        finally:
            tmp.unlink(missing_ok=True)


SYCO_OUTCOME_COLS = [
    "rightorwrong",
    "repair_score",
    "trust_score",
    "performance_trust_score",
    "moral_trust_score",
    "return_likelihood",
    "response_quality",
]

SYCO_STUDY2_COLS = ["is_syco", "scenarioNum"] + SYCO_OUTCOME_COLS
SYCO_STUDY3_COLS = ["Condition", "scenarioNum"] + SYCO_OUTCOME_COLS


def transform6() -> None:
    df = pd.read_csv(SYCO_STUDY2_RAW, usecols=SYCO_STUDY2_COLS)
    df.to_csv(SYCO_STUDY2_PROC, index=False)

    df = pd.read_csv(SYCO_STUDY3_RAW, usecols=SYCO_STUDY3_COLS)
    df.to_csv(SYCO_STUDY3_PROC, index=False)


def main() -> None:
    acquire1()
    transform1()

    acquire2()
    transform2()

    acquire3()
    transform3()

    acquire4()
    transform4()

    acquire5()
    transform5()

    acquire6()
    transform6()


if __name__ == "__main__":
    main()


############################################################################################################################
# --------------------------------------- HUMAN PRACTICE -------------------------------------------------------------------
############################################################################################################################

"""Build the page's chart-ready tables from the source samples.

Every number shown on screen comes from a row of ``data/processed/*.csv``.
Every processed row is derived from a verbatim copy of a source file in
``data/raw/human_practice/wildai/`` (see ``data/raw/human_practice/wildai/SOURCE.md``), ``data/raw/human_practice/workforce/`` (see
``data/raw/human_practice/workforce/SOURCE.md``), ``data/raw/human_practice/schaeffer/`` (see ``data/raw/human_practice/schaeffer/SOURCE.md``)
and ``data/processed/human_practice/MANIFEST.json`` records the SHA-256 of each input and the row count of each output.

    uv run python -m narrative.human_practice_data              # rebuild the processed tables and validate
    uv run python -m narrative.human_practice_data --validate   # validate the existing processed files
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import pandas as pd

from narrative import utils

RAW = utils.get_raw_data_dir() / "human_practice"
PROCESSED = utils.get_proc_data_dir() / "human_practice"
WILDAI, SCHAEFFER, WORKFORCE = RAW / "wildai", RAW / "schaeffer", RAW / "workforce"

WILDAI_COMMIT = (
    "795a71852d569173fcdaca1db2a466109cd80814"  # origin/main of pangramlabs/WildAI
)
WORKFORCE_COMMIT = (
    "b33f3b25b7cce24833c857d242c90152c3b41571"  # karanmakhijauts/at-3-dvn, 26 Oct 2026
)

# Figure 3 of Russell et al. (2026): matched human-token budgets (tokens per parameter),
# drawn model sizes (depths 4-16, i.e. 19.9M-268M) and the matching tolerance.
MATCHED_BUDGETS = (4.72, 18.88, 37.76, 54.72, 72.97, 87.5)
BUDGET_TOLERANCE = 0.015
FITTED_DEPTHS = (4, 6, 9, 12, 16)
SIZE_ORDER = ("19.9m", "35.8m", "86.2m", "135m", "268m")
BUDGET_WORDS = {
    4.72: 5,
    18.88: 20,
    37.76: 40,
    54.72: 55,
    72.97: 73,
    87.5: 88,
}  # the paper's labels

CSV_READ = dict(keep_default_na=False, na_values=[""])

# Schaeffer et al. (2025), Sec. 2: "the definitions can themselves be loosely clustered into three
# families: (i) population risk degrading (Definitions 1, 2 and 3), (ii) distributions deforming from
# their original shape (Definitions 4, 5, 6, 7, and 8), and (iii) decreasing value from additional
# data (Definition 5)."  Definition 5 therefore belongs to two families.
FAMILIES = {
    1: ["Population risk degrading"],
    2: ["Population risk degrading"],
    3: ["Population risk degrading"],
    4: ["Distributions deforming"],
    5: ["Distributions deforming", "Decreasing value from additional data"],
    6: ["Distributions deforming"],
    7: ["Distributions deforming"],
    8: ["Distributions deforming"],
}
# Schaeffer et al. (2025), Appendix A, Table 1 (regression setting): does collapse occur?
# (accumulate, replace)
TABLE1 = {
    1: (False, True),
    2: (True, True),
    3: (False, True),
    4: (False, False),
    5: (True, True),
    6: (False, False),
    7: (False, False),
    8: (False, False),
}
SHORT_NAMES = {
    1: "Catastrophic increase of population risk",
    2: "Any increase of population risk",
    3: "Asymptotically diverging population risk",
    4: "Collapsing variance",
    5: "Change in scaling law",
    6: "Disappearance or entanglement of real data modes",
    7: "Disappearance of real tail data",
    8: "Appearance of hallucinated data",
}
# Wording changes made after checking the table against the paper (see README, "Fact-check edits").
DEF4_CONDITION = (
    "Replace paradigm is unrealistic. Schaeffer et al. cite about 1 quadrillion available "
    "pre-training tokens (attributed to Villalobos et al. 2024). (Sec. 3, 4.1, 4.4)"
)
DEF5_CONDITION = (
    'Not tied to a specific condition. Listed in two families: "distributions deforming" and '
    '"decreasing value from additional data". (Sec. 2)'
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _month_start(period: pd.Series) -> pd.Series:
    return pd.to_datetime(period + "-01", errors="raise").dt.strftime("%Y-%m-%d")


# --------------------------------------------------------------------------- builders
def build_ai_share() -> pd.DataFrame:
    """Monthly AI share of web tokens: observed (with 95% interval) and forecast (80%/95% bands)."""
    obs = pd.read_csv(WILDAI / "monthly_ai_share.csv", **CSV_READ)
    fc = pd.read_csv(WILDAI / "ai_share_forecast.csv", **CSV_READ)
    fc = fc[fc["kind"] == "forecast"]
    observed = pd.DataFrame(
        {
            "month": _month_start(obs["month"]),
            "kind": "observed",
            "share": obs["ai_share"],
            "lo80": pd.NA,
            "hi80": pd.NA,
            "lo95": obs["ai_share_lo95"],
            "hi95": obs["ai_share_hi95"],
            "sampling_source": obs["source"],
            "documents": obs["documents"],
            "tokens": obs["tokens"],
            "ai_tokens": obs["ai_tokens"],
        }
    )
    forecast = pd.DataFrame(
        {
            "month": _month_start(fc["month"]),
            "kind": "forecast",
            "share": fc["share"],
            "lo80": fc["lo80"],
            "hi80": fc["hi80"],
            "lo95": fc["lo95"],
            "hi95": fc["hi95"],
            "sampling_source": "random walk with drift",
            "documents": pd.NA,
            "tokens": pd.NA,
            "ai_tokens": pd.NA,
        }
    )
    return (
        pd.concat([observed, forecast], ignore_index=True)
        .sort_values("month")
        .reset_index(drop=True)
    )


def build_web_composition() -> pd.DataFrame:
    """Monthly share of sampled web tokens and documents by Pangram label (Human, Mixed, AI)."""
    frame = pd.read_csv(WILDAI / "monthly_topic_format.csv", **CSV_READ)
    obs = pd.read_csv(WILDAI / "monthly_ai_share.csv", **CSV_READ).set_index("month")
    totals = frame.groupby(["period", "label"], as_index=False)[
        ["documents", "tokens"]
    ].sum()
    month_tokens = totals.groupby("period")["tokens"].transform("sum")
    month_docs = totals.groupby("period")["documents"].transform("sum")
    totals["token_share"] = totals["tokens"] / month_tokens
    totals["document_share"] = totals["documents"] / month_docs
    totals["sampling_source"] = totals["period"].map(obs["source"])
    totals.insert(0, "month", _month_start(totals["period"]))
    return (
        totals.drop(columns="period")
        .sort_values(["month", "label"])
        .reset_index(drop=True)
    )


def build_adoption() -> pd.DataFrame:
    """Share of US firms giving each answer to the BTOS AI-use question, by two-week collection period."""
    raw = pd.read_csv(WORKFORCE / "btos_ai.csv", **CSV_READ)
    codes = sorted(raw["period_code"].unique())
    out = pd.DataFrame(
        {
            "period_order": raw["period_code"].map(
                {c: i + 1 for i, c in enumerate(codes)}
            ),
            "period_code": raw["period_code"],
            "period_label": raw["period_label"],
            "question_id": raw["question_id"],
            "answer": raw["answer"],
            "share_pct": raw["value_pct"],
        }
    )
    return out.sort_values(["period_order", "answer"]).reset_index(drop=True)


PANEL_TITLES = {"output": "Output gains", "skill": "Skill and learning signals"}


def build_evidence() -> pd.DataFrame:
    """Karan Makhija's six hand-built findings on output and skill, with a display title per panel."""
    raw = pd.read_csv(WORKFORCE / "evidence.csv", **CSV_READ)
    raw.insert(2, "panel_title", raw["panel"].map(PANEL_TITLES))
    return raw


def build_entry_level() -> pd.DataFrame:
    """Employment change by age and AI exposure, Nov 2022 to Jun 2026 (Brynjolfsson, Chandar and Chen 2026)."""
    return pd.read_csv(WORKFORCE / "entry_level_employment.csv", **CSV_READ)


def _snap_budget(tpp: float) -> float | None:
    return next(
        (b for b in MATCHED_BUDGETS if abs(tpp - b) <= BUDGET_TOLERANCE * b), None
    )


def build_fig3_points() -> pd.DataFrame:
    """Points of Figure 3 (Russell et al. 2026): change in C4 loss vs each run's human-only control."""
    models = pd.read_csv(WILDAI / "models.csv", **CSV_READ)
    losses = pd.read_csv(WILDAI / "losses.csv", **CSV_READ)
    loss = losses[losses["target"] == "c4"].set_index("name")["bpb"]
    models["bpb"] = models["name"].map(loss)
    models["tpp"] = models["human_tokens"] / models["n_params"]
    control = models[models["arm"] == "control"].set_index("group")
    runs = models[models["arm"].isin(["ai", "human"])].copy()
    for col in ("tpp", "depth", "bpb", "human_tokens"):
        runs["ctrl_" + col] = runs["group"].map(control[col])
    runs["budget"] = runs["ctrl_tpp"].map(_snap_budget)
    runs = runs[runs["budget"].notna() & runs["ctrl_depth"].isin(FITTED_DEPTHS)].copy()
    runs["x"] = runs.apply(
        lambda r: (
            r.ai_tokens / r.human_tokens
            if r.arm == "ai"
            else r.human_tokens / r.ctrl_human_tokens - 1
        ),
        axis=1,
    )
    runs["change_pct"] = 100 * (runs["bpb"] / runs["ctrl_bpb"] - 1)
    # AI ladders: for each size and budget use the one group with the most AI runs (ties: lowest id);
    # fresh-human points use every group.  This follows the description of the authors' figure code.
    ai = runs[runs["arm"] == "ai"]
    counts = ai.groupby(["size", "budget", "group"]).size().reset_index(name="n")
    best = counts.sort_values(
        ["size", "budget", "n", "group"], ascending=[True, True, False, True]
    ).drop_duplicates(["size", "budget"])
    chosen = set(zip(best["size"], best["budget"], best["group"]))
    runs["in_figure"] = runs.apply(
        lambda r: r.arm == "human" or (r["size"], r.budget, r.group) in chosen, axis=1
    )
    runs["size_order"] = runs["size"].map({s: i for i, s in enumerate(SIZE_ORDER)})
    out = runs[
        [
            "name",
            "group",
            "size",
            "size_order",
            "budget",
            "arm",
            "x",
            "bpb",
            "ctrl_bpb",
            "change_pct",
            "in_figure",
        ]
    ]
    return out.sort_values(["budget", "size_order", "arm", "x", "name"]).reset_index(
        drop=True
    )


def build_cost() -> pd.DataFrame:
    """Compute multiplier needed by unfiltered web text to match its human-only subset (law output)."""
    frame = pd.read_csv(WILDAI / "cost_of_not_filtering.csv", **CSV_READ)
    frame["model_size"] = frame["n_params"].map(lambda n: "268M" if n < 1e9 else "8B")
    frame["scenario"] = frame["label"].fillna("")
    return (
        frame[
            [
                "target",
                "model_size",
                "n_params",
                "human_tpp",
                "ai_share",
                "scenario",
                "cost",
            ]
        ]
        .sort_values(["target", "model_size", "ai_share"])
        .reset_index(drop=True)
    )


# Which charts on the page bear on which definition. This mapping is my own judgement, not from either paper.
# (label shown in the table, one-sentence reason shown in the detail panel)
COVERAGE = {
    1: (
        "Not covered",
        "No chart tests catastrophic degradation. The loss chart shows changes of a few per cent when AI text is mixed into human data, which is not recursive training.",
    ),
    2: (
        "Loss chart (partly)",
        "The loss chart compares loss with added AI text against a human-only control, so a rise is an increase in risk by this definition. Loss is measured on C4 as a proxy for the real distribution, and with mixing, not recursion.",
    ),
    3: (
        "Not covered",
        "This needs successive generations of models; the WildAI models are single-generation mixes of human and AI text.",
    ),
    4: ("Not covered", "No chart measures variance or diversity."),
    5: (
        "Loss and compute charts",
        "Both are about the scaling law: what added AI text does to loss at a fixed human-token budget, and the compute multiplier that follows.",
    ),
    6: (
        "Not covered",
        "No chart shows a model losing or merging modes. The web-composition chart describes what the web contains, not what a model has lost.",
    ),
    7: ("Not covered", "No chart measures how a model handles rare cases."),
    8: (
        "Not covered",
        "No chart checks whether model output is supported by the real data.",
    ),
}
CONTEXT_NOTE = "The web-composition chart is context for every definition: it shows how much AI text is already in web data."


def build_definitions() -> pd.DataFrame:
    """The eight definitions of model collapse (Schaeffer et al. 2025) with their families."""
    raw = pd.read_csv(SCHAEFFER / "section_a_schaeffer_table.csv", **CSV_READ)
    raw.columns = [
        "definition",
        "details",
        "realistic_condition",
        "mitigation",
        "rebuttal",
        "papers",
    ]
    raw.insert(0, "id", range(1, len(raw) + 1))
    if len(raw) != 8:
        raise ValueError("Expected eight definitions")
    raw["short_name"] = raw["id"].map(SHORT_NAMES)
    raw["families"] = raw["id"].map(lambda i: " | ".join(FAMILIES[i]))
    raw["collapse_accumulate"] = raw["id"].map(lambda i: TABLE1[i][0])
    raw["collapse_replace"] = raw["id"].map(lambda i: TABLE1[i][1])
    raw["covered_in"] = raw["id"].map(lambda i: COVERAGE[i][0])
    raw["coverage_note"] = raw["id"].map(lambda i: COVERAGE[i][1])
    raw.loc[raw["id"] == 4, "realistic_condition"] = DEF4_CONDITION
    raw.loc[raw["id"] == 5, "realistic_condition"] = DEF5_CONDITION
    return raw


# --------------------------------------------------------------------------- validation
def validate(tables: dict[str, pd.DataFrame]) -> None:
    share = tables["ai_share"]
    if share.duplicated(["month", "kind"]).any():
        raise ValueError("ai_share: duplicate month/kind")
    for col in ("share", "lo95", "hi95"):
        if not share[col].astype(float).between(0, 1).all():
            raise ValueError(f"ai_share: {col} outside [0, 1]")
    if not (
        (share["lo95"].astype(float) <= share["share"] + 1e-9)
        & (share["share"] <= share["hi95"].astype(float) + 1e-9)
    ).all():
        raise ValueError("ai_share: share outside its 95% interval")
    observed = share[share["kind"] == "observed"]
    forecast = share[share["kind"] == "forecast"]
    if observed["month"].max() >= forecast["month"].min():
        raise ValueError("ai_share: forecast must start after the last observation")

    fig3 = tables["fig3_points"]
    if fig3["x"].le(0).any() or fig3["change_pct"].isna().any():
        raise ValueError("fig3_points: non-positive x or missing loss")
    worked = fig3[fig3["name"] == "268m-g075-ai-r1"]
    if (
        len(worked) != 1
        or abs(float(worked["change_pct"].iloc[0]) - (-1.031081)) > 1e-3
    ):
        raise ValueError(
            "fig3_points: worked example 268m-g075-ai-r1 does not reproduce (-1.03%)"
        )

    cost = tables["cost"]
    finite = cost[cost["cost"].map(math.isfinite)]
    if not (finite.loc[finite["ai_share"] == 0, "cost"].round(6) == 1.0).all():
        raise ValueError("cost: the multiplier at 0% AI share must be 1")

    definitions = tables["definitions"]
    if sorted(definitions["id"]) != list(range(1, 9)):
        raise ValueError("definitions: expected ids 1-8")

    comp = tables["web_composition"]
    if (
        not set(comp["label"]) <= {"AI", "Human", "Mixed"}
        or comp.duplicated(["month", "label"]).any()
    ):
        raise ValueError("web_composition: unexpected label or duplicate month/label")
    if (comp.groupby("month")["token_share"].sum() - 1).abs().max() > 1e-9:
        raise ValueError("web_composition: token shares must sum to 1 in every month")
    ai = comp[comp["label"] == "AI"].set_index("month")["token_share"]
    ref = observed.set_index("month")["share"].astype(float)
    if (ai.reindex(ref.index).fillna(0) - ref).abs().max() > 1e-9:
        raise ValueError(
            "web_composition: AI token share does not reproduce monthly_ai_share.csv"
        )

    adoption = tables["adoption"]
    if (
        adoption.duplicated(["period_code", "answer"]).any()
        or not adoption["share_pct"].between(0, 100).all()
    ):
        raise ValueError("adoption: duplicate period/answer or share outside 0-100")
    if (adoption.groupby("period_code")["share_pct"].sum() - 100).abs().max() > 0.5:
        raise ValueError("adoption: answers should sum to about 100% in every period")

    evidence = tables["evidence"]
    if evidence["id"].duplicated().any() or not set(evidence["panel"]) <= {
        "output",
        "skill",
    }:
        raise ValueError("evidence: duplicate id or unknown panel")
    if not set(evidence["direction"]) <= {"gain", "loss"} or not set(
        evidence["evidence_strength"]
    ) <= {"High", "Medium", "Low"}:
        raise ValueError("evidence: unknown direction or evidence strength")
    if (
        evidence[["source_url", "location_in_source", "check_status"]]
        .isna()
        .any()
        .any()
    ):
        raise ValueError(
            "evidence: every finding needs a source, a location and a check status"
        )

    entry = tables["entry_level"]
    if (
        entry["id"].duplicated().any()
        or entry[["change_pct", "source_url", "location_in_source"]].isna().any().any()
    ):
        raise ValueError("entry_level: duplicate id or missing value/source")


# --------------------------------------------------------------------------- IO
BUILDERS = {
    "adoption": build_adoption,
    "evidence": build_evidence,
    "entry_level": build_entry_level,
    "web_composition": build_web_composition,
    "ai_share": build_ai_share,
    "fig3_points": build_fig3_points,
    "cost": build_cost,
    "definitions": build_definitions,
}
INPUTS = {
    "adoption": [WORKFORCE / "btos_ai.csv"],
    "evidence": [WORKFORCE / "evidence.csv"],
    "entry_level": [WORKFORCE / "entry_level_employment.csv"],
    "web_composition": [
        WILDAI / "monthly_topic_format.csv",
        WILDAI / "monthly_ai_share.csv",
    ],
    "ai_share": [WILDAI / "monthly_ai_share.csv", WILDAI / "ai_share_forecast.csv"],
    "fig3_points": [WILDAI / "models.csv", WILDAI / "losses.csv"],
    "cost": [WILDAI / "cost_of_not_filtering.csv"],
    "definitions": [SCHAEFFER / "section_a_schaeffer_table.csv"],
}


def write_tables(tables: dict[str, pd.DataFrame]) -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    manifest = {
        "wildai_commit": WILDAI_COMMIT,
        "workforce_commit": WORKFORCE_COMMIT,
        "licence": "WildAI results: CC BY-NC-SA 4.0. Other files: see data/workforce/SOURCE.md",
        "tables": {},
    }
    for name, frame in tables.items():
        frame.to_csv(PROCESSED / f"{name}.csv", index=False)
        manifest["tables"][name] = {
            "rows": len(frame),
            "inputs": {str(p.relative_to(RAW)): _sha256(p) for p in INPUTS[name]},
        }
    (PROCESSED / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


def read_processed(name: str) -> pd.DataFrame:
    return pd.read_csv(PROCESSED / f"{name}.csv", **CSV_READ)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--validate", action="store_true", help="validate data/processed/* and stop"
    )
    args = parser.parse_args()
    if args.validate:
        tables = {name: read_processed(name) for name in BUILDERS}
        validate(tables)
        print("Processed data valid")
        return
    tables = {name: builder() for name, builder in BUILDERS.items()}
    validate(tables)
    write_tables(tables)
    for name, frame in tables.items():
        print(f"{name}: {len(frame)} rows")
    print(f"Validated and wrote {len(tables)} tables to {PROCESSED}")


if __name__ == "__main__":
    sys.exit(main())


############################################################################################################################
# --------------------------------------- PROFITABILITY --------------------------------------------------------------------
############################################################################################################################

"""Rebuild every file in data/processed/ from the source samples in data/raw/.

Run from this folder:   python scripts/build_processed.py

Each processed file is its raw file restricted to the analysis window (rows from the first
period listed below onward), with exact duplicate rows dropped and rows sorted by their key
columns. Column names are kept so every figure on screen can be traced back to the raw source.
All further calculations (growth rates, indices, ratios) are done in app.py and shown in each
chart's ⓘ table and in the Appendix. Re-running on unchanged raw files gives identical output.
"""

import pandas as pd

from narrative.utils import *

RAW, OUT = get_raw_data_dir(), get_proc_data_dir()
OUT.mkdir(parents=True, exist_ok=True)

PROFIT_FILES = {
    # file: (time column or None, first period kept)
    "owid_share-companies-using-artificial-intelligence.csv": ("Year", 2021),
    "owid_estimated-share-people-generative-ai.csv": (None, None),
    "eurostat_isoc_eb_ai.csv": ("year", 2021),
    "eurostat_isoc_eb_ain2_industry.csv": ("year", 2021),
    "eurostat_isoc_eb_ai_size.csv": ("year", 2021),
    "eurostat_isoc_eb_ai_barriers.csv": ("year", 2023),
    "owid_private-investment-in-artificial-intelligence-cset.csv": ("Year", 2022),
    "owid_global-investment-in-generative-ai.csv": ("Year", 2019),
    "owid_nvidia-quarterly-revenue-segment.csv": (None, None),
    "owid_data-centers-share-electricity-demand.csv": ("Year", 2020),
    "owid_gdp-per-capita-growth.csv": ("Year", 2015),
    "ilo_output_per_hour.csv": ("year", 2015),
    "ilo_output_per_hour_countries.csv": ("year", 2015),
    "ilo_labour_income_share.csv": ("year", 2015),
    "fred_CP.csv": (None, None),
    "fred_GDP.csv": (None, None),
    "fred_COE.csv": (None, None),
    "fred_OPHNFB.csv": (None, None),
    "fred_ULCNFB.csv": (None, None),
    "eurostat_nasa_10_ki_profit_share.csv": ("year", 2019),
    "eurostat_nasa_10_ki_consumption_growth.csv": ("year", 2019),
    "eurostat_nama_10_lp_ulc.csv": ("year", 2019),
    "eurostat_nama_10_a10_industry.csv": ("year", 2019),
    "eurostat_nama_10_a10_e_hours.csv": ("year", 2019),
    "eurostat_une_rt_a.csv": ("year", 2019),
}


def build_profitability():
    """Keep rows from the first period listed in PROFIT_FILES onward, drop exact duplicate rows, sort by all key columns."""
    for name, (tcol, start) in PROFIT_FILES.items():
        d = pd.read_csv(RAW / name).drop_duplicates()
        if tcol:
            d = d[d[tcol] >= start]
        d = d.sort_values(list(d.columns[:-1])).reset_index(drop=True)
        d.to_csv(OUT / name, index=False)
        print(f"{len(d):>6} rows  data/processed/{name}")


if __name__ == "__main__":
    build_profitability()
