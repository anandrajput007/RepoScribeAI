from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.analyzer import RepoAnalyzer
from app.code_parser import CodeParser, FileMetadata
from app.doc_generator import DocumentationGenerator
from app.llm_manager import LLMManager
from ui.settings_page import render_settings_page
from utils.env_manager import ENV_KEY_LABELS, EnvManager
from utils.file_utils import ensure_directory


APP_TITLE = "RepoScribe AI - Repository Intelligence Platform"


def _initialize_state() -> None:
    defaults = {
        "analysis_result": None,
        "selected_model": None,
        "chat_history": [],
        "show_missing_key_prompt": False,
        "missing_provider_name": "",
        "repo_url_input": "",
        "branch_cache_url": "",
        "branch_options": [],
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


@st.dialog("Configure Provider API Key")
def _missing_key_dialog(provider_name: str, llm_manager: LLMManager, env_manager: EnvManager) -> None:
    provider = llm_manager.get_provider_by_name(provider_name)
    if not provider:
        st.write("No provider metadata found.")
        return

    current_model = llm_manager.get_provider_model(provider)
    st.write(f"{provider.provider} requires an API key before it can be used.")
    api_key = st.text_input(ENV_KEY_LABELS[provider.env_key], type="password")
    model_choice = st.selectbox(
        f"{provider.provider} Base Model",
        provider.available_models,
        index=provider.available_models.index(current_model) if current_model in provider.available_models else 0,
    )

    left_col, right_col = st.columns(2)
    with left_col:
        if st.button("Save Key", use_container_width=True):
            if api_key.strip():
                env_manager.save_keys(
                    {
                        provider.env_key: api_key.strip(),
                        provider.model_env_key: model_choice,
                    }
                )
                st.session_state["show_missing_key_prompt"] = False
                st.rerun()
    with right_col:
        if st.button("Cancel", use_container_width=True):
            st.session_state["show_missing_key_prompt"] = False
            st.rerun()


def _get_selected_file_metadata(file_index: list[FileMetadata], selected_path: str) -> FileMetadata | None:
    for item in file_index:
        if item.path == selected_path:
            return item
    return None


def _refresh_branch_options(repo_url: str, analyzer: RepoAnalyzer) -> None:
    if not repo_url.strip():
        st.session_state["branch_options"] = []
        st.session_state["branch_cache_url"] = ""
        return

    branches = analyzer.repo_loader.get_remote_branches(repo_url.strip())
    st.session_state["branch_options"] = branches
    st.session_state["branch_cache_url"] = repo_url.strip()


def main() -> None:
    ensure_directory(Path("repos"))
    ensure_directory(Path("vector_store"))
    _initialize_state()

    env_manager = EnvManager()
    llm_manager = LLMManager(env_manager)
    analyzer = RepoAnalyzer()
    parser = CodeParser()
    doc_generator = DocumentationGenerator()

    st.set_page_config(page_title="RepoScribe AI", layout="wide")
    st.title(APP_TITLE)

    configured_models = llm_manager.get_configured_models()
    configured_labels = [model.display_label for model in configured_models]
    default_model = llm_manager.get_default_model_label()
    if configured_labels and default_model not in configured_labels:
        default_model = configured_labels[0]
        llm_manager.save_default_model_label(default_model)
    if configured_labels and st.session_state.get("selected_model") not in configured_labels:
        st.session_state["selected_model"] = default_model or configured_labels[0]

    local_repositories = analyzer.repo_loader.list_local_repositories()
    local_repo_names = [repo.repo_name for repo in local_repositories]

    with st.sidebar:
        with st.expander("Repository Control", expanded=True):
            st.caption(f"Local repositories: {len(local_repositories)}/{analyzer.repo_loader.max_repositories}")
            if len(local_repositories) >= analyzer.repo_loader.max_repositories:
                st.warning("Already 3 repositories are downloaded. Remove one before processing a new repository.")

            selected_local_repo = st.selectbox(
                "Select local repository",
                [""] + local_repo_names,
                key="selected_local_repo",
            )
            selected_local_info = next(
                (repo for repo in local_repositories if repo.repo_name == selected_local_repo),
                None,
            )
            if selected_local_info:
                st.caption(f"Branch: {selected_local_info.branch}")
                st.caption(f"URL: {selected_local_info.repo_url}")

            open_col, delete_col = st.columns(2)
            with open_col:
                if st.button("Open Local", use_container_width=True):
                    if selected_local_repo:
                        try:
                            st.session_state["analysis_result"] = analyzer.load_existing_repository(selected_local_repo)
                            st.success("Local repository loaded.")
                        except Exception as exc:
                            st.error(str(exc))
            with delete_col:
                if st.button("Delete Local", use_container_width=True):
                    if selected_local_repo:
                        analyzer.repo_loader.delete_local_repository(selected_local_repo)
                        current_analysis = st.session_state.get("analysis_result")
                        if current_analysis and current_analysis.load_result.repo_name == selected_local_repo:
                            st.session_state["analysis_result"] = None
                        st.success("Local repository deleted.")
                        st.rerun()

            st.divider()
            repo_url = st.text_input("Repository URL", key="repo_url_input")
            fetch_col, process_col = st.columns(2)
            with fetch_col:
                if st.button("Load Branches", use_container_width=True):
                    if repo_url.strip():
                        try:
                            _refresh_branch_options(repo_url, analyzer)
                            if not st.session_state["branch_options"]:
                                st.warning("No branches were found for this repository.")
                        except Exception as exc:
                            st.error(str(exc))
                    else:
                        st.warning("Enter a repository URL first.")

            branch_options = (
                st.session_state.get("branch_options", [])
                if st.session_state.get("branch_cache_url") == repo_url.strip()
                else []
            )
            if branch_options:
                default_branch_index = branch_options.index("main") if "main" in branch_options else 0
                selected_branch = st.selectbox("Select branch", branch_options, index=default_branch_index)
            else:
                selected_branch = st.text_input("Branch", value="main", key="branch_text_input")

            with process_col:
                if st.button("Process Repository", use_container_width=True):
                    if not repo_url.strip():
                        st.warning("Enter a repository URL first.")
                    else:
                        try:
                            with st.spinner("Processing repository..."):
                                st.session_state["analysis_result"] = analyzer.process_repository(
                                    repo_url.strip(),
                                    branch=selected_branch,
                                )
                            st.success("Repository processed successfully.")
                        except Exception as exc:
                            st.error(str(exc))

        with st.expander("Model Selection", expanded=True):
            if configured_labels:
                selected_index = configured_labels.index(st.session_state["selected_model"]) if st.session_state["selected_model"] in configured_labels else 0
                selected_model = st.selectbox("Select AI Model", configured_labels, index=selected_index)
                st.session_state["selected_model"] = selected_model
                llm_manager.save_default_model_label(selected_model)
            else:
                st.info("No configured providers yet.")

            provider_names = [provider.provider for provider in llm_manager.get_provider_configs()]
            provider_to_configure = st.selectbox("Configure provider", provider_names, key="provider_to_configure")
            if not llm_manager.is_provider_configured(provider_to_configure):
                if st.button("Add Provider Key", use_container_width=True):
                    st.session_state["missing_provider_name"] = provider_to_configure
                    st.session_state["show_missing_key_prompt"] = True
            else:
                st.caption("Provider configured. Change base model from Settings.")

        st.caption("Use the tabs in the main area.")

    if st.session_state.get("show_missing_key_prompt"):
        _missing_key_dialog(st.session_state.get("missing_provider_name", ""), llm_manager, env_manager)

    ask_tab, explain_tab, settings_tab = st.tabs(
        ["Ask Questions", "File / Method Explanation", "Settings"]
    )

    with ask_tab:
        st.subheader("Ask Questions")
        analysis_result = st.session_state.get("analysis_result")
        if not analysis_result:
            st.info("Process or open a repository from the sidebar to enable repository Q&A.")
        else:
            question = st.chat_input("Ask a question about the repository")
            if question:
                if not st.session_state.get("selected_model"):
                    st.warning("Select a configured model first.")
                else:
                    results = analyzer.rag_engine.retrieve_relevant_code(question, top_k=5)
                    answer = llm_manager.generate_response(
                        prompt=question,
                        context_chunks=results,
                        model_label=st.session_state["selected_model"],
                    )
                    st.session_state["chat_history"].append({"question": question, "answer": answer})

            for item in st.session_state["chat_history"]:
                with st.chat_message("user"):
                    st.write(item["question"])
                with st.chat_message("assistant"):
                    st.write(item["answer"])

            summary = analyzer.get_repository_summary(analysis_result.file_index)
            col1, col2, col3 = st.columns(3)
            col1.metric("Indexed Files", summary["total_files"])
            col2.metric("Indexed Methods", summary["total_methods"])
            col3.metric("Languages", len(summary["languages"]))

    with explain_tab:
        st.subheader("File / Method Explanation")
        analysis_result = st.session_state.get("analysis_result")
        if not analysis_result or not analysis_result.file_index:
            st.info("Process or open a repository to inspect files and methods.")
        else:
            file_options = [item.path for item in analysis_result.file_index]
            left_col, right_col = st.columns(2)
            with left_col:
                selected_file = st.selectbox("File name", file_options)
            selected_metadata = _get_selected_file_metadata(analysis_result.file_index, selected_file)
            method_options = [""] + parser.list_method_names(analysis_result.file_index, selected_file)
            with right_col:
                method_name = st.selectbox("Method name", method_options)

            if st.button("Generate Explanation"):
                file_content = analyzer.get_file_content(
                    analysis_result.load_result.local_path,
                    selected_file,
                )
                generated = doc_generator.generate_file_method_explanation(
                    file_metadata=selected_metadata,
                    method_name=method_name,
                    file_content=file_content,
                )

                with st.expander("Technical Documentation", expanded=True):
                    st.write(generated["technical"])
                with st.expander("Functional Explanation"):
                    st.write(generated["functional"])
                with st.expander("Data Flow"):
                    st.write(generated["data_flow"])
                with st.expander("Test Cases"):
                    st.text(generated["test_cases"])
                with st.expander("Acceptance Criteria"):
                    st.text(generated["acceptance_criteria"])

    with settings_tab:
        render_settings_page(env_manager, llm_manager)


if __name__ == "__main__":
    main()
