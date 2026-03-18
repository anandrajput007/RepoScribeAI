from __future__ import annotations

from dataclasses import dataclass

from utils.env_manager import DEFAULT_MODEL_ENV_KEY, EnvManager


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    env_key: str
    model_env_key: str
    label: str
    available_models: tuple[str, ...]


@dataclass(frozen=True)
class ConfiguredModel:
    provider: str
    env_key: str
    model_env_key: str
    selected_model: str
    display_label: str


class LLMManager:
    SUPPORTED_MODELS = [
        ProviderConfig("OpenAI", "OPENAI_API_KEY", "OPENAI_MODEL", "OpenAI", ("gpt-5", "gpt-4o", "gpt-4", "gpt-4.1-mini")),
        ProviderConfig("Google Gemini", "GEMINI_API_KEY", "GEMINI_MODEL", "Google Gemini", ("gemini-2.5-pro", "gemini-2.5-flash", "gemini-1.5-pro")),
        ProviderConfig("Anthropic", "ANTHROPIC_API_KEY", "ANTHROPIC_MODEL", "Anthropic Claude", ("claude-3-7-sonnet", "claude-3-5-sonnet", "claude-3-haiku")),
        ProviderConfig("GitHub Copilot", "COPILOT_API_KEY", "COPILOT_MODEL", "GitHub Copilot", ("copilot-placeholder",)),
    ]

    def __init__(self, env_manager: EnvManager | None = None) -> None:
        self.env_manager = env_manager or EnvManager()

    def get_provider_configs(self) -> list[ProviderConfig]:
        return self.SUPPORTED_MODELS

    def get_provider_by_name(self, provider_name: str) -> ProviderConfig | None:
        for provider in self.SUPPORTED_MODELS:
            if provider.provider == provider_name:
                return provider
        return None

    def get_provider_model(self, provider: ProviderConfig) -> str:
        model_name = self.env_manager.get_value(provider.model_env_key, "")
        if model_name in provider.available_models:
            return model_name
        return provider.available_models[0]

    def get_configured_models(self) -> list[ConfiguredModel]:
        env_values = self.env_manager.load_env()
        models: list[ConfiguredModel] = []
        for provider in self.SUPPORTED_MODELS:
            if env_values.get(provider.env_key, "").strip():
                selected_model = env_values.get(provider.model_env_key, "").strip()
                if selected_model not in provider.available_models:
                    selected_model = provider.available_models[0]
                models.append(
                    ConfiguredModel(
                        provider=provider.provider,
                        env_key=provider.env_key,
                        model_env_key=provider.model_env_key,
                        selected_model=selected_model,
                        display_label=f"{selected_model} ({provider.provider})",
                    )
                )
        return models

    def get_configured_model_by_label(self, display_label: str) -> ConfiguredModel | None:
        for model in self.get_configured_models():
            if model.display_label == display_label:
                return model
        return None

    def is_provider_configured(self, provider_name: str) -> bool:
        provider = self.get_provider_by_name(provider_name)
        if not provider:
            return False
        return bool(self.env_manager.get_value(provider.env_key).strip())

    def get_default_model_label(self) -> str:
        return self.env_manager.get_value(DEFAULT_MODEL_ENV_KEY, "")

    def save_default_model_label(self, label: str) -> None:
        self.env_manager.save_key(DEFAULT_MODEL_ENV_KEY, label)

    def generate_response(self, prompt: str, context_chunks: list[dict], model_label: str) -> str:
        model = self.get_configured_model_by_label(model_label)
        if not model:
            return "No valid model selected."

        context_summary = ", ".join(
            chunk.get("metadata", {}).get("path", "unknown file")
            for chunk in context_chunks[:3]
        ) or "no retrieved files"

        return (
            f"Placeholder response from {model.display_label}.\n\n"
            f"Prompt: {prompt}\n"
            f"Relevant context: {context_summary}\n\n"
            "Wire this method to the provider SDK to enable live completions."
        )
