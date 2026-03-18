from __future__ import annotations

from pathlib import Path

from dotenv import dotenv_values, set_key


ENV_KEY_LABELS = {
    "OPENAI_API_KEY": "OpenAI API Key",
    "GEMINI_API_KEY": "Gemini API Key",
    "ANTHROPIC_API_KEY": "Claude API Key",
    "COPILOT_API_KEY": "Copilot API Key",
}

MODEL_ENV_KEY_LABELS = {
    "OPENAI_MODEL": "OpenAI Base Model",
    "GEMINI_MODEL": "Gemini Base Model",
    "ANTHROPIC_MODEL": "Claude Base Model",
    "COPILOT_MODEL": "Copilot Base Model",
}

DEFAULT_MODEL_ENV_KEY = "DEFAULT_MODEL_LABEL"


class EnvManager:
    def __init__(self, env_path: str | Path = ".env") -> None:
        self.env_path = Path(env_path)
        if not self.env_path.exists():
            self.env_path.write_text("", encoding="utf-8")

    def load_env(self) -> dict[str, str]:
        values = dotenv_values(self.env_path)
        return {key: value or "" for key, value in values.items()}

    def save_key(self, env_key: str, value: str) -> None:
        set_key(str(self.env_path), env_key, value)

    def save_keys(self, values: dict[str, str]) -> None:
        for key, value in values.items():
            self.save_key(key, value)

    def get_value(self, key: str, default: str = "") -> str:
        return self.load_env().get(key, default)
