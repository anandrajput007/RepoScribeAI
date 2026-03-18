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


APP_TITLE = "RepoScribe AI — Repository Intelligence Platform"


def _initialize_state() -> None:
    defaults = {
        "analysis_result": None,
        "selected_model": None,
        "chat_history": [],
        "show_missing_key_prompt": False,
        "missing_model_label": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


@st.dialog("Configure Provider API Key")
def _missing_key_dialog(model_label: str, llm_manager: LLMManager, env_manager: EnvManager) -> None:
    model = llm_manager.get_model_by_label(model_label)
    if not model:
        st.write("No model metadata found.")
        return

    st.write(f"{model.label} requires an API key before it can be used.")
    api_key = st.text_input(ENV_KEY_LABELS[model.env_key], type="password")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Key", use_container_width=True):
            if api_key.strip():
                env_manager.save_key(model.env_key, api_key.strip())
                st.session_state["show_missing_key_prompt"] = False
                st.rerun()
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state["show_missing_key_prompt"] = False
            st.rerun()


def _get_selected_file_metadata(file_index: list[FileMetadata], selected_path: str) -> FileMetadata | None:
    for item in file_index:
        if item.path == selected_path:
            return item
    return None


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
    configured_labels = [model.label for model in configured_models]
    all_labels = [model.label for model in llm_manager.SUPPORTED_MODELS]

    with st.sidebar:
        st.header("Repository Controls")
        repo_url = st.text_input("Repository URL")
        if st.button("Process Repository", use_container_width=True):
            if not repo_url.strip():
                st.warning("Enter a repository URL first.")
            else:
                with st.spinner("Processing repository..."):
                    try:
                        st.session_state["analysis_result"] = analyzer.process_repository(repo_url.strip())
                        st.success("Repository processed successfully.")
                    except Exception as exc:
                        st.error(str(exc))

        st.divider()
        st.subheader("Model Selection")
        selection_source = configured_labels if configured_labels else ["No configured models"]
        selected_label = st.selectbox("Select AI Model", selection_source)
        st.session_state["selected_model"] = selected_label if selected_label != "No configured models" else None

        missing_option = st.selectbox("Add or inspect provider", all_labels, index=0 if all_labels else None)
        if missing_option and not llm_manager.is_model_configured(missing_option):
            if st.button("Configure Selected Provider", use_container_width=True):
                st.session_state["missing_model_label"] = missing_option
                st.session_state["show_missing_key_prompt"] = True

        st.divider()
        st.caption("Navigation")
        st.write("Use the tabs in the main area.")

    if st.session_state.get("show_missing_key_prompt"):
        _missing_key_dialog(st.session_state.get("missing_model_label", ""), llm_manager, env_manager)

    ask_tab, explain_tab, settings_tab = st.tabs(
        ["Ask Questions", "File / Method Explanation", "Settings"]
    )

    with ask_tab:
        st.subheader("Ask Questions")
        analysis_result = st.session_state.get("analysis_result")
        if not analysis_result:
            st.info("Process a repository from the sidebar to enable repository Q&A.")
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
            st.info("Process a repository to inspect files and methods.")
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
        render_settings_page(env_manager)


if __name__ == "__main__":
    main()
