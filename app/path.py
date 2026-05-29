from pathlib import Path
from platformdirs import user_config_dir
import json
import streamlit as st
import app_config

#CONFIG_DIR = Path.home() / f".{app_config.APP_NAME}"

CONFIG_DIR = Path(user_config_dir(app_config.APP_NAME))
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = CONFIG_DIR / app_config.DATA_CONFIG


# ---------------- CONFIG IO ----------------

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return None


def save_config(data_folder: str):

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    config = {
        "data_folder": data_folder
    }

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)


# # ---------------- CORE LOGIC ----------------

# def get_data_folder():
#     config = st.session_state.config

#     if config and "data_folder" in config:
#         return Path(config["data_folder"])

#     return None