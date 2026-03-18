from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.analyzer import RepoAnalyzer, RepositoryAnalysis
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
        "active_repo_name": "",
        "selected_model": None,
        "chat_history": [],
        "show_missing_key_prompt": False,
        "missing_provider_name": "",
        "show_delete_repo_prompt": False,
        "repo_to_delete": "",
        "show_add_repository_form": False,
        "repo_limit_warning": "",
        "repo_url_input": "",
        "branch_cache_url": "",
        "branch_options": [],
        "sidebar_section": "repository",
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


@st.dialog("Delete Repository")
def _delete_repo_dialog(repo_name: str, analyzer: RepoAnalyzer) -> None:
    st.write(f"Delete local repository `{repo_name}`?")
    st.caption("This removes the downloaded files from the local `repos` folder.")

    left_col, right_col = st.columns(2)
    with left_col:
        if st.button("Confirm Delete", use_container_width=True, type="primary"):
            analyzer.repo_loader.delete_local_repository(repo_name)
            current_analysis = st.session_state.get("analysis_result")
            if current_analysis and current_analysis.load_result.repo_name == repo_name:
                st.session_state["analysis_result"] = None
            if st.session_state.get("active_repo_name") == repo_name:
                st.session_state["active_repo_name"] = ""
            st.session_state["show_delete_repo_prompt"] = False
            st.session_state["repo_to_delete"] = ""
            st.success("Repository deleted.")
            st.rerun()
    with right_col:
        if st.button("Cancel", use_container_width=True):
            st.session_state["show_delete_repo_prompt"] = False
            st.session_state["repo_to_delete"] = ""
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


def _set_active_analysis(result: RepositoryAnalysis) -> None:
    st.session_state["analysis_result"] = result
    st.session_state["active_repo_name"] = result.load_result.repo_name
    st.session_state["chat_history"] = []


def _get_active_repo_name(local_repo_names: list[str]) -> str:
    current_active = st.session_state.get("active_repo_name", "")
    if current_active in local_repo_names:
        return current_active

    current_analysis = st.session_state.get("analysis_result")
    if current_analysis and current_analysis.load_result.repo_name in local_repo_names:
        st.session_state["active_repo_name"] = current_analysis.load_result.repo_name
        return current_analysis.load_result.repo_name

    if len(local_repo_names) == 1:
        st.session_state["active_repo_name"] = local_repo_names[0]
        return local_repo_names[0]

    return ""


def _render_repo_card(repo, is_active: bool, analyzer: RepoAnalyzer) -> None:
    bg_color = "#e9f7ef" if is_active else "#f3f4f6"
    border_color = "#1f8f4d" if is_active else "#c7c9cf"
    text_color = "#111827" if is_active else "#6b7280"
    badge_bg = "#1f8f4d" if is_active else "#e5a50a"
    badge_text = "Active" if is_active else "Inactive"

    st.markdown(
        f"""
        <div style="background:{bg_color}; border:1px solid {border_color}; border-radius:14px; padding:0.8rem 0.9rem; margin-bottom:0.35rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; gap:0.75rem;">
                <div style="font-weight:600; color:{text_color}; overflow-wrap:anywhere;">{repo.repo_name}</div>
                <div style="background:{badge_bg}; color:white; padding:0.2rem 0.55rem; border-radius:999px; font-size:0.72rem; font-weight:600;">{badge_text}</div>
            </div>
            <div style="margin-top:0.4rem; color:{text_color}; font-size:0.92rem;">Branch: {repo.branch}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if is_active:
        st.button("Active", key=f"active_{repo.repo_name}", use_container_width=True, type="primary", disabled=True)
    else:
        action_col, delete_col = st.columns([3, 1])
        with action_col:
            if st.button("Reactivate", key=f"reactivate_{repo.repo_name}", use_container_width=True):
                try:
                    _set_active_analysis(analyzer.load_existing_repository(repo.repo_name))
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        with delete_col:
            if st.button("X", key=f"delete_{repo.repo_name}", use_container_width=True, help="Delete local repository"):
                st.session_state["repo_to_delete"] = repo.repo_name
                st.session_state["show_delete_repo_prompt"] = True


def _set_sidebar_section(section: str) -> None:
    st.session_state["sidebar_section"] = section


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
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] {
            width: 24rem !important;
            min-width: 24rem !important;
        }
        section[data-testid="stSidebar"] > div {
            width: 24rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
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
    active_repo_name = _get_active_repo_name(local_repo_names)

    with st.sidebar:
        repo_open = st.session_state.get("sidebar_section") == "repository"
        model_open = st.session_state.get("sidebar_section") == "model"

        if st.button(
            f"{'▼' if repo_open else '▶'} Repository ({len(local_repositories)}/{analyzer.repo_loader.max_repositories})",
            key="sidebar_repository_toggle",
            use_container_width=True,
        ):
            _set_sidebar_section("repository")

        if repo_open:
            if st.session_state.get("repo_limit_warning"):
                st.warning(st.session_state["repo_limit_warning"])
                st.session_state["repo_limit_warning"] = ""

            for repo in local_repositories:
                _render_repo_card(repo, repo.repo_name == active_repo_name, analyzer)

            if st.button("+ Add Repository", use_container_width=True, type="primary"):
                if len(local_repositories) >= analyzer.repo_loader.max_repositories:
                    st.session_state["repo_limit_warning"] = "Need to remove one repository then load a new repository."
                else:
                    st.session_state["show_add_repository_form"] = True
                st.rerun()

            if st.session_state.get("show_add_repository_form"):
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

                process_now_col, cancel_col = st.columns(2)
                with process_now_col:
                    if st.button("Process Repository", use_container_width=True):
                        if not repo_url.strip():
                            st.warning("Enter a repository URL first.")
                        else:
                            try:
                                with st.spinner("Processing repository..."):
                                    result = analyzer.process_repository(
                                        repo_url.strip(),
                                        branch=selected_branch,
                                    )
                                _set_active_analysis(result)
                                st.session_state["show_add_repository_form"] = False
                                st.success("Repository processed successfully.")
                                st.rerun()
                            except Exception as exc:
                                st.error(str(exc))
                with cancel_col:
                    if st.button("Close", use_container_width=True):
                        st.session_state["show_add_repository_form"] = False
                        st.rerun()

        if st.button(
            f"{'▼' if model_open else '▶'} Model Selection",
            key="sidebar_model_toggle",
            use_container_width=True,
        ):
            _set_sidebar_section("model")

        if model_open:
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

    if st.session_state.get("show_delete_repo_prompt") and st.session_state.get("repo_to_delete"):
        _delete_repo_dialog(st.session_state["repo_to_delete"], analyzer)

    ask_tab, explain_tab, settings_tab = st.tabs(
        ["Ask Questions", "File / Method Explanation", "Settings"]
    )

    with ask_tab:
        st.subheader("Ask Questions")
        analysis_result = st.session_state.get("analysis_result")
        if not analysis_result:
            st.info("Process or reactivate a repository from the sidebar to enable repository Q&A.")
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

            for item in reversed(st.session_state["chat_history"]):
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
            st.info("Process or reactivate a repository to inspect files and methods.")
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
