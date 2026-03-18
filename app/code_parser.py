from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from utils.file_utils import SUPPORTED_EXTENSIONS, read_text_file, scan_repository_files


@dataclass
class MethodMetadata:
    name: str
    start_line: int
    end_line: int
    signature: str


@dataclass
class FileMetadata:
    path: str
    language: str
    size_bytes: int
    methods: list[MethodMetadata] = field(default_factory=list)


class CodeParser:
    def __init__(self) -> None:
        self._language_map = {
            ".py": "Python",
            ".cs": "C#",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".sql": "SQL",
        }

    def scan_files(self, repo_path: str | Path) -> list[Path]:
        return scan_repository_files(repo_path, SUPPORTED_EXTENSIONS)

    def build_file_index(self, repo_path: str | Path) -> list[FileMetadata]:
        repo_root = Path(repo_path)
        metadata_items: list[FileMetadata] = []

        for file_path in self.scan_files(repo_root):
            content = read_text_file(file_path)
            relative_path = file_path.relative_to(repo_root).as_posix()
            methods = self.extract_methods(file_path, content)
            metadata_items.append(
                FileMetadata(
                    path=relative_path,
                    language=self._language_map.get(file_path.suffix.lower(), "Unknown"),
                    size_bytes=file_path.stat().st_size,
                    methods=methods,
                )
            )

        return metadata_items

    def extract_methods(self, file_path: str | Path, content: str) -> list[MethodMetadata]:
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix == ".py":
            return self._extract_python_methods(content)
        return self._extract_generic_methods(content)

    def list_method_names(self, file_index: Iterable[FileMetadata], file_path: str) -> list[str]:
        for item in file_index:
            if item.path == file_path:
                return [method.name for method in item.methods]
        return []

    def _extract_python_methods(self, content: str) -> list[MethodMetadata]:
        methods: list[MethodMetadata] = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return methods

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end_line = getattr(node, "end_lineno", node.lineno)
                args = [arg.arg for arg in node.args.args]
                signature = f"{node.name}({', '.join(args)})"
                methods.append(
                    MethodMetadata(
                        name=node.name,
                        start_line=node.lineno,
                        end_line=end_line,
                        signature=signature,
                    )
                )
        return sorted(methods, key=lambda item: item.start_line)

    def _extract_generic_methods(self, content: str) -> list[MethodMetadata]:
        methods: list[MethodMetadata] = []
        pattern = re.compile(
            r"(?P<signature>(?:public|private|protected|internal|static|async|\s)+[\w<>\[\],\s]+\s+(?P<name>\w+)\s*\([^)]*\))"
        )
        lines = content.splitlines()

        for index, line in enumerate(lines, start=1):
            match = pattern.search(line)
            if match:
                methods.append(
                    MethodMetadata(
                        name=match.group("name"),
                        start_line=index,
                        end_line=index,
                        signature=" ".join(match.group("signature").split()),
                    )
                )

        return methods

