
import streamlit as st
import json, pandas as pd, os
from osf_loader import fetch_osf_file

st.set_page_config(page_title="NYC VOC Explorer", layout="wide")

with open("config_osf.json", "r") as f:
    OSF = json.load(f)

try:
    TOKEN = st.secrets["OSF_TOKEN"]
except Exception:
    TOKEN = os.getenv("OSF_TOKEN", None)

@st.cache_data(show_spinner=False)
def load_df(key: str) -> pd.DataFrame:
    meta = OSF[key]
    local = fetch_osf_file(meta["url"], meta["local"], token=TOKEN, expected_sha256=meta.get("sha256"))
    try:
        return pd.read_parquet(local)
    except Exception:
        parse_dates = ["Date"] if key in ("daily",) else None
        return pd.read_csv(local, parse_dates=parse_dates)

st.sidebar.title("NYC VOC Explorer")
st.write("Use the **Pages** menu to navigate.")

