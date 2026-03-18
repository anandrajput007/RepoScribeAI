from __future__ import annotations

import streamlit as st

from app.llm_manager import LLMManager
from utils.env_manager import DEFAULT_MODEL_ENV_KEY, ENV_KEY_LABELS, EnvManager


def render_settings_page(
    env_manager: EnvManager | None = None,
    llm_manager: LLMManager | None = None,
) -> None:
    env_manager = env_manager or EnvManager()
    llm_manager = llm_manager or LLMManager(env_manager)
    current_values = env_manager.load_env()

    st.subheader("Provider Settings")
    st.caption("API keys are stored locally in the project `.env` file.")

    with st.form("provider_settings_form"):
        updates: dict[str, str] = {}
        for provider in llm_manager.get_provider_configs():
            st.markdown(f"### {provider.provider}")
            updates[provider.env_key] = st.text_input(
                ENV_KEY_LABELS[provider.env_key],
                value=current_values.get(provider.env_key, ""),
                type="password",
                key=f"settings_{provider.env_key}",
            )
            selected_model = current_values.get(provider.model_env_key, "") or provider.available_models[0]
            model_index = provider.available_models.index(selected_model) if selected_model in provider.available_models else 0
            updates[provider.model_env_key] = st.selectbox(
                f"{provider.provider} Base Model",
                provider.available_models,
                index=model_index,
                key=f"settings_{provider.model_env_key}",
            )

        configured_models = llm_manager.get_configured_models()
        configured_labels = [model.display_label for model in configured_models]
        default_label = current_values.get(DEFAULT_MODEL_ENV_KEY, "")
        if configured_labels:
            default_index = configured_labels.index(default_label) if default_label in configured_labels else 0
            updates[DEFAULT_MODEL_ENV_KEY] = st.selectbox(
                "Default AI Model",
                configured_labels,
                index=default_index,
                key="settings_default_model",
            )
        else:
            updates[DEFAULT_MODEL_ENV_KEY] = ""
            st.info("Save at least one provider API key to enable default model selection.")

        submitted = st.form_submit_button("Save API Keys")
        if submitted:
            env_manager.save_keys(updates)
            st.success("Provider settings saved to .env")
