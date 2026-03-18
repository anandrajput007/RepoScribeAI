from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb

from app.code_parser import FileMetadata
from utils.file_utils import ensure_directory, read_text_file


@dataclass
class CodeChunk:
    chunk_id: str
    file_path: str
    content: str
    metadata: dict[str, Any]


class RAGEngine:
    def __init__(self, storage_dir: str | Path = "vector_store") -> None:
        self.storage_dir = Path(storage_dir)
        ensure_directory(self.storage_dir)
        self.client = chromadb.PersistentClient(path=str(self.storage_dir))
        self.collection = self.client.get_or_create_collection(name="reposcribe_chunks")

    def chunk_codebase(self, repo_path: str | Path, file_index: list[FileMetadata]) -> list[CodeChunk]:
        repo_root = Path(repo_path)
        chunks: list[CodeChunk] = []

        for item in file_index:
            source_path = repo_root / item.path
            content = read_text_file(source_path)
            chunk_id = item.path.replace("/", "_")
            chunks.append(
                CodeChunk(
                    chunk_id=chunk_id,
                    file_path=item.path,
                    content=content[:4000],
                    metadata={
                        "path": item.path,
                        "language": item.language,
                        "method_count": len(item.methods),
                    },
                )
            )

        return chunks

    def create_embeddings(self, chunks: list[CodeChunk]) -> list[list[float]]:
        # Placeholder embedding generation. Replace with provider-specific embeddings later.
        return [[float(len(chunk.content)), float(len(chunk.file_path))] for chunk in chunks]

    def store_vectors(self, chunks: list[CodeChunk], embeddings: list[list[float]]) -> None:
        if not chunks:
            return

        self.collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.content for chunk in chunks],
            metadatas=[chunk.metadata for chunk in chunks],
            embeddings=embeddings,
        )

    def retrieve_relevant_code(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if self.collection.count() == 0:
            return []

        query_embedding = [[float(len(query)), float(sum(ord(char) for char in query) % 1000)]]
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
        )

        matches: list[dict[str, Any]] = []
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        for chunk_id, document, metadata in zip(ids, documents, metadatas):
            matches.append(
                {
                    "chunk_id": chunk_id,
                    "content": document,
                    "metadata": metadata,
                }
            )

        return matches

