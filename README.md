# RepoScribe AI

RepoScribe AI is a Streamlit-based repository intelligence tool for cloning Git repositories, indexing source code, and preparing a Retrieval-Augmented Generation (RAG) workflow for repository Q&A and file or method explanations.

## Features

- Clone and index Git repositories into the local `repos/` workspace
- Support up to 3 locally downloaded repositories at a time
- Show repository cards in the sidebar with active and inactive states
- Reactivate an existing local repository without recloning it
- Delete inactive local repositories with confirmation
- Load and select a branch before processing a repository
- Keep only one branch locally for a given repository at a time
- Scan supported source files: `.py`, `.cs`, `.js`, `.ts`, `.sql`
- Build lightweight file and function metadata for analysis
- Prepare RAG-ready code chunks and placeholder vector storage flow
- Support multiple LLM providers through one model manager
- Save provider API keys and base-model selections in `.env`
- Persist the default selected AI model between application runs
- Show newest repository questions and answers first in the chat view

## Sidebar Behavior

The left sidebar is split into two controlled accordion sections:

- `Repository (x/3)`
- `Model Selection`

Only one section is open at a time, and `Repository` is open by default.

### Repository Section

- Shows repository cards for all locally downloaded repositories
- Highlights the active repository
- Dims inactive repositories
- Allows reactivation of inactive repositories
- Allows deletion of inactive repositories with confirmation
- Includes a `+ Add Repository` button
- Blocks adding a fourth repository until one existing repository is removed

### Model Selection Section

- Shows only configured provider/model combinations in the model dropdown
- Persists the selected default model in `.env`
- Lets users add missing provider API keys from the sidebar

## Provider Configuration

The app currently supports these providers:

- OpenAI
- Google Gemini
- Anthropic Claude
- GitHub Copilot placeholder

Each provider can store:

- API key
- Base model selection

Examples of saved model choices include:

- `gpt-5`
- `gpt-4o`
- `gpt-4`
- `gpt-4.1-mini`

The active default model is also stored and restored on the next app start.

## Project Structure

```text
RepoScribeAI/
|-- app/
|   |-- analyzer.py
|   |-- code_parser.py
|   |-- doc_generator.py
|   |-- llm_manager.py
|   |-- rag_engine.py
|   `-- repo_loader.py
|-- repos/
|-- ui/
|   |-- settings_page.py
|   `-- streamlit_app.py
|-- utils/
|   |-- env_manager.py
|   `-- file_utils.py
|-- vector_store/
|-- .env
|-- .gitignore
|-- pyproject.toml
|-- uv.lock
|-- README.md
`-- run.bat
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

If port `8501` is already in use, run on another port:

```powershell
uv run streamlit run ui/streamlit_app.py --server.port 8503
```

Or on Windows:

```powershell
run.bat
```

## Current Workflow

1. Open the `Repository` section in the sidebar.
2. Review existing local repository cards.
3. Click `+ Add Repository` to process a new repository.
4. Enter the repository URL.
5. Load branches and select the branch to process.
6. Process the repository and make it the active repository.
7. Ask repository questions or generate file and method explanations.

## Notes

- API keys are stored locally in `.env` and should never be committed.
- The current RAG and LLM flows still use placeholder response generation.
- Vector storage and retrieval are scaffolded and ready for deeper provider integration.
- Repository deletion on Windows handles read-only Git pack files in `.git/objects/pack`.
