from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.code_parser import CodeParser, FileMetadata
from app.rag_engine import RAGEngine
from app.repo_loader import RepoLoadResult, RepoLoader


@dataclass
class RepositoryAnalysis:
    load_result: RepoLoadResult
    file_index: list[FileMetadata]
    chunk_count: int


class RepoAnalyzer:
    def __init__(
        self,
        repo_loader: RepoLoader | None = None,
        code_parser: CodeParser | None = None,
        rag_engine: RAGEngine | None = None,
    ) -> None:
        self.repo_loader = repo_loader or RepoLoader()
        self.code_parser = code_parser or CodeParser()
        self.rag_engine = rag_engine or RAGEngine()

    def process_repository(self, repo_url: str) -> RepositoryAnalysis:
        load_result = self.repo_loader.clone_or_get_repo(repo_url)
        file_index = self.code_parser.build_file_index(load_result.local_path)
        chunks = self.rag_engine.chunk_codebase(load_result.local_path, file_index)
        embeddings = self.rag_engine.create_embeddings(chunks)
        self.rag_engine.store_vectors(chunks, embeddings)

        return RepositoryAnalysis(
            load_result=load_result,
            file_index=file_index,
            chunk_count=len(chunks),
        )

    def get_repository_summary(self, file_index: list[FileMetadata]) -> dict[str, Any]:
        return {
            "total_files": len(file_index),
            "total_methods": sum(len(item.methods) for item in file_index),
            "languages": sorted({item.language for item in file_index}),
        }

    def get_file_content(self, repo_path: str | Path, relative_file_path: str) -> str:
        file_path = Path(repo_path) / relative_file_path
        return file_path.read_text(encoding="utf-8", errors="ignore")

