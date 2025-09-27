
import streamlit as st
import json, pandas as pd
from osf_loader import fetch_osf_file

st.set_page_config(page_title="NYC VOC Explorer", layout="wide")

# Load OSF config
with open("config_osf.json", "r") as f:
    OSF = json.load(f)

# Private projects: set OSF_TOKEN in .streamlit/secrets.toml
TOKEN = st.secrets.get("OSF_TOKEN", None)

@st.cache_data(show_spinner=False)
def load_df(key: str) -> pd.DataFrame:
    meta = OSF[key]
    local = fetch_osf_file(meta["url"], meta["local"], token=TOKEN, expected_sha256=meta.get("sha256"))
    try:
        return pd.read_parquet(local)
    except Exception:
        # CSV fallback
        parse_dates = ["Date"] if key in ("daily",) else None
        return pd.read_csv(local, parse_dates=parse_dates)

st.sidebar.title("NYC VOC Explorer")
st.sidebar.caption("Data pulled from OSF at start and cached locally.")

st.sidebar.write("**Datasets**")
with st.sidebar.expander("Status checks", expanded=False):
    for k in OSF.keys():
        st.code(f"{k}: {OSF[k]['url']}", language="bash")

st.write("Use the **Pages** menu (top-left) to navigate.")
st.info("Overview and PD–SID pages are included in this scaffold. Add more pages as needed.")
