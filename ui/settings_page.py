from __future__ import annotations

import streamlit as st

from utils.env_manager import ENV_KEY_LABELS, EnvManager


def render_settings_page(env_manager: EnvManager | None = None) -> None:
    env_manager = env_manager or EnvManager()
    current_values = env_manager.load_env()

    st.subheader("Provider Settings")
    st.caption("API keys are stored locally in the project `.env` file.")

    with st.form("provider_settings_form"):
        updates: dict[str, str] = {}
        for env_key, label in ENV_KEY_LABELS.items():
            current_value = current_values.get(env_key, "")
            masked_value = current_value if current_value else ""
            updates[env_key] = st.text_input(label, value=masked_value, type="password")

        submitted = st.form_submit_button("Save API Keys")
        if submitted:
            env_manager.save_keys(updates)
            st.success("API keys saved to .env")

