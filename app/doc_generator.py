from __future__ import annotations

from app.code_parser import FileMetadata


class DocumentationGenerator:
    def generate_file_method_explanation(
        self,
        file_metadata: FileMetadata | None,
        method_name: str,
        file_content: str,
    ) -> dict[str, str]:
        file_path = file_metadata.path if file_metadata else "Unknown file"
        method_names = ", ".join(method.name for method in file_metadata.methods) if file_metadata else "No methods indexed"
        selected_method = method_name.strip() or "the selected file"

        technical = (
            f"{selected_method} in {file_path} belongs to the {file_metadata.language if file_metadata else 'unknown'} layer. "
            f"Indexed methods in this file: {method_names}."
        )
        functional = (
            f"This placeholder summary describes what {selected_method} is expected to do based on repository indexing. "
            "Connect this module to live LLM generation for richer explanations."
        )
        data_flow = (
            f"The current file snapshot contains {len(file_content.splitlines())} lines. "
            "Use RAG retrieval plus semantic analysis to map upstream inputs and downstream outputs."
        )
        test_cases = (
            f"- Validate the happy path for {selected_method}\n"
            f"- Validate error handling and invalid inputs in {file_path}\n"
            "- Validate integration points and side effects"
        )
        acceptance = (
            f"- Explanation covers technical and business intent for {selected_method}\n"
            "- Inputs, outputs, and dependencies are identified\n"
            "- Test scenarios are actionable"
        )

        return {
            "technical": technical,
            "functional": functional,
            "data_flow": data_flow,
            "test_cases": test_cases,
            "acceptance_criteria": acceptance,
        }

