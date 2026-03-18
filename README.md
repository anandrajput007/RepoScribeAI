# RepoScribe AI

RepoScribe AI is a Streamlit-based developer tool for cloning repositories, indexing source code, and preparing a Retrieval-Augmented Generation (RAG) workflow for repository Q&A and file/method explanations.

## Features

- Clone a Git repository into a local `repos/` workspace
- Scan and index supported source files: `.py`, `.cs`, `.js`, `.ts`, `.sql`
- Build lightweight file and function metadata for analysis
- Prepare RAG-ready chunks and placeholder vector storage flow
- Support multiple LLM providers through a single model manager
- Manage API keys securely through the UI and a local `.env` file

## Project Structure

```text
RepoScribeAI/
├── app/
│   ├── analyzer.py
│   ├── code_parser.py
│   ├── doc_generator.py
│   ├── llm_manager.py
│   ├── rag_engine.py
│   └── repo_loader.py
├── repos/
├── ui/
│   ├── settings_page.py
│   └── streamlit_app.py
├── utils/
│   ├── env_manager.py
│   └── file_utils.py
├── vector_store/
├── .env
├── .gitignore
├── pyproject.toml
├── uv.lock
├── README.md
└── run.bat
```

## Getting Started

1. Install `uv`: https://docs.astral.sh/uv/
2. Sync dependencies:

```powershell
uv sync
```

3. Run the app:

```powershell
uv run streamlit run ui/streamlit_app.py
```

Or on Windows:

```powershell
run.bat
```

## Notes

- API keys are stored locally in `.env` and should never be committed.
- The current RAG and LLM flows are scaffolded with placeholder generation so the app can run before external provider integrations are enabled.
- `uv.lock` is included as a placeholder path in the project structure and ignored by Git as requested. Generate it with `uv sync` if you want a concrete lockfile.

