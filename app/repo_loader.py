from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from git import Repo

from utils.file_utils import ensure_directory, sanitize_repo_name


@dataclass
class RepoLoadResult:
    repo_url: str
    local_path: Path
    branch: Optional[str]
    cloned: bool
    message: str


class RepoLoader:
    def __init__(self, base_dir: str | Path = "repos") -> None:
        self.base_dir = Path(base_dir)
        ensure_directory(self.base_dir)

    def clone_or_get_repo(self, repo_url: str) -> RepoLoadResult:
        repo_name = sanitize_repo_name(repo_url)
        target_path = self.base_dir / repo_name

        if target_path.exists():
            try:
                repo = Repo(target_path)
                branch = None
                if not repo.head.is_detached:
                    branch = repo.active_branch.name
                return RepoLoadResult(
                    repo_url=repo_url,
                    local_path=target_path,
                    branch=branch,
                    cloned=False,
                    message="Repository already exists locally. Reusing cached copy.",
                )
            except Exception as exc:
                raise RuntimeError(f"Existing repository path is invalid: {exc}") from exc

        try:
            repo = Repo.clone_from(repo_url, target_path)
            branch = None
            if not repo.head.is_detached:
                branch = repo.active_branch.name
            return RepoLoadResult(
                repo_url=repo_url,
                local_path=target_path,
                branch=branch,
                cloned=True,
                message="Repository cloned successfully.",
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to clone repository: {exc}") from exc

