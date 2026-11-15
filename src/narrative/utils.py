import base64
import json
from functools import lru_cache
from pathlib import Path

import pandas as pd
import streamlit as st


@lru_cache(maxsize=1)
def get_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists():
            return parent


@lru_cache(maxsize=1)
def get_data_dir() -> Path:
    data_dir = get_project_root() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@lru_cache(maxsize=1)
def get_proc_data_dir() -> Path:
    data_dir = get_data_dir() / "processed"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@lru_cache(maxsize=1)
def get_raw_data_dir() -> Path:
    data_dir = get_data_dir() / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@st.cache_data
def get_json(pth: Path) -> pd.DataFrame:
    with open(pth, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return pd.json_normalize(payload["facilities"])


@st.cache_data
def get_img(pth: Path):
    with open(pth, "rb") as f:
        img_bytes = f.read()
    encoded_img = base64.b64encode(img_bytes).decode()
    return encoded_img


@st.cache_data
def get_csv(pth: Path) -> pd.DataFrame:
    return pd.read_csv(pth)
