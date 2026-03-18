from __future__ import annotations

import os
import re
import shutil
import stat
from pathlib import Path
from urllib.parse import urlparse


SUPPORTED_EXTENSIONS = {".py", ".cs", ".js", ".ts", ".sql"}


def ensure_directory(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def delete_directory(path: str | Path) -> None:
    target = Path(path)
    if target.exists():
        shutil.rmtree(target, onerror=_handle_remove_readonly)


def _handle_remove_readonly(func, path, exc_info) -> None:
    error = exc_info[1]
    if not isinstance(error, PermissionError):
        raise error

    os.chmod(path, stat.S_IWRITE)
    func(path)


def sanitize_repo_name(repo_url: str) -> str:
    parsed = urlparse(repo_url)
    repo_name = Path(parsed.path).stem or "repository"
    clean_name = re.sub(r"[^A-Za-z0-9._-]+", "-", repo_name).strip("-")
    return clean_name or "repository"


def scan_repository_files(repo_path: str | Path, extensions: set[str]) -> list[Path]:
    repo_root = Path(repo_path)
    files: list[Path] = []
    for path in repo_root.rglob("*"):
        if path.is_file() and path.suffix.lower() in extensions:
            files.append(path)
    return sorted(files)


def read_text_file(file_path: str | Path) -> str:
    return Path(file_path).read_text(encoding="utf-8", errors="ignore")
