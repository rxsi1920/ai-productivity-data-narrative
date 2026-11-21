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
        print(f"Missing file: {AI_INCIDENTS_GMF_RAW} (export it from https://incidentdatabase.ai/taxonomies/gmf/)")


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
    # response_id = the row's position in the raw file (1..n), used as the primary key.
    # The raw files have no other usable key (Study 3's PROLIFIC_PID is a participant ID and is not copied).
    df = pd.read_csv(SYCO_STUDY2_RAW, usecols=SYCO_STUDY2_COLS)
    df.insert(0, "response_id", range(1, len(df) + 1))
    df.to_csv(SYCO_STUDY2_PROC, index=False)

    df = pd.read_csv(SYCO_STUDY3_RAW, usecols=SYCO_STUDY3_COLS)
    df.insert(0, "response_id", range(1, len(df) + 1))
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
