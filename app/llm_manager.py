from __future__ import annotations

from dataclasses import dataclass

from utils.env_manager import EnvManager


@dataclass(frozen=True)
class ProviderModel:
    provider: str
    model_name: str
    label: str
    env_key: str


class LLMManager:
    SUPPORTED_MODELS = [
        ProviderModel("OpenAI", "gpt-4", "GPT-4 (OpenAI)", "OPENAI_API_KEY"),
        ProviderModel("Google Gemini", "gemini-pro", "Gemini Pro", "GEMINI_API_KEY"),
        ProviderModel("Anthropic", "claude-3-sonnet", "Claude 3", "ANTHROPIC_API_KEY"),
        ProviderModel("GitHub Copilot", "copilot-placeholder", "Copilot (Coming Soon)", "COPILOT_API_KEY"),
    ]

    def __init__(self, env_manager: EnvManager | None = None) -> None:
        self.env_manager = env_manager or EnvManager()

    def get_configured_models(self) -> list[ProviderModel]:
        env_values = self.env_manager.load_env()
        return [
            model
            for model in self.SUPPORTED_MODELS
            if env_values.get(model.env_key, "").strip()
        ]

    def get_model_by_label(self, label: str) -> ProviderModel | None:
        for model in self.SUPPORTED_MODELS:
            if model.label == label:
                return model
        return None

    def is_model_configured(self, label: str) -> bool:
        model = self.get_model_by_label(label)
        if not model:
            return False
        return bool(self.env_manager.load_env().get(model.env_key, "").strip())

    def generate_response(self, prompt: str, context_chunks: list[dict], model_label: str) -> str:
        model = self.get_model_by_label(model_label)
        if not model:
            return "No valid model selected."

        if not self.is_model_configured(model_label):
            return f"{model.label} is not configured yet. Add the required API key in Settings."

        context_summary = ", ".join(
            chunk.get("metadata", {}).get("path", "unknown file")
            for chunk in context_chunks[:3]
        ) or "no retrieved files"

        return (
            f"Placeholder response from {model.label}.\n\n"
            f"Prompt: {prompt}\n"
            f"Relevant context: {context_summary}\n\n"
            "Wire this method to the provider SDK to enable live completions."
        )

