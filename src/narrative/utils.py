from pathlib import Path


def get_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists():
            return parent


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
