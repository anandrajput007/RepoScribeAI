@echo off
where uv >nul 2>nul
if errorlevel 1 (
    echo uv is not installed.
    echo Install uv from https://docs.astral.sh/uv/
    exit /b 1
)

uv run streamlit run ui/streamlit_app.py

