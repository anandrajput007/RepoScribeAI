from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from git import Git, Repo

from utils.file_utils import delete_directory, ensure_directory, sanitize_repo_name


@dataclass
class RepoLoadResult:
    repo_name: str
    repo_url: str
    local_path: Path
    branch: Optional[str]
    cloned: bool
    message: str


@dataclass
class LocalRepository:
    repo_name: str
    repo_url: str
    branch: str
    local_path: Path


class RepoLoader:
    def __init__(self, base_dir: str | Path = "repos", max_repositories: int = 3) -> None:
        self.base_dir = Path(base_dir)
        self.max_repositories = max_repositories
        ensure_directory(self.base_dir)

    def clone_or_get_repo(self, repo_url: str, branch: str | None = None) -> RepoLoadResult:
        repo_name = sanitize_repo_name(repo_url)
        target_path = self.base_dir / repo_name
        requested_branch = (branch or "").strip()

        local_repositories = self.list_local_repositories()
        is_existing_repo = any(item.repo_name == repo_name for item in local_repositories)
        if not is_existing_repo and len(local_repositories) >= self.max_repositories:
            raise RuntimeError(
                f"Already {self.max_repositories} repositories are downloaded locally. "
                "Remove one before processing another repository."
            )

        if target_path.exists():
            try:
                repo = Repo(target_path)
                current_branch = self._get_active_branch(repo)
                if requested_branch and current_branch != requested_branch:
                    delete_directory(target_path)
                    return self._clone_repository(repo_name, repo_url, target_path, requested_branch)
                return RepoLoadResult(
                    repo_name=repo_name,
                    repo_url=repo_url,
                    local_path=target_path,
                    branch=current_branch,
                    cloned=False,
                    message="Repository already exists locally. Reusing cached copy.",
                )
            except Exception as exc:
                raise RuntimeError(f"Existing repository path is invalid: {exc}") from exc

        return self._clone_repository(repo_name, repo_url, target_path, requested_branch or None)

    def _clone_repository(
        self,
        repo_name: str,
        repo_url: str,
        target_path: Path,
        branch: str | None,
    ) -> RepoLoadResult:
        try:
            clone_kwargs: dict[str, str | bool] = {"single_branch": True}
            if branch:
                clone_kwargs["branch"] = branch
            repo = Repo.clone_from(repo_url, target_path, **clone_kwargs)
            active_branch = self._get_active_branch(repo)
            return RepoLoadResult(
                repo_name=repo_name,
                repo_url=repo_url,
                local_path=target_path,
                branch=active_branch,
                cloned=True,
                message="Repository cloned successfully." if not branch else f"Repository cloned successfully for branch '{active_branch}'.",
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to clone repository: {exc}") from exc

    def get_remote_branches(self, repo_url: str) -> list[str]:
        try:
            output = Git().ls_remote("--heads", repo_url)
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch branches: {exc}") from exc

        branches: list[str] = []
        for line in output.splitlines():
            if "refs/heads/" in line:
                branches.append(line.split("refs/heads/")[-1].strip())
        return sorted(set(branches))

    def list_local_repositories(self) -> list[LocalRepository]:
        repositories: list[LocalRepository] = []
        for path in sorted(self.base_dir.iterdir()):
            if not path.is_dir():
                continue
            try:
                repo = Repo(path)
                remote_url = next(repo.remote().urls, "")
                repositories.append(
                    LocalRepository(
                        repo_name=path.name,
                        repo_url=remote_url,
                        branch=self._get_active_branch(repo),
                        local_path=path,
                    )
                )
            except Exception:
                continue
        return repositories

    def delete_local_repository(self, repo_name: str) -> None:
        delete_directory(self.base_dir / repo_name)

    def _get_active_branch(self, repo: Repo) -> str:
        if repo.head.is_detached:
            return "detached"
        return repo.active_branch.name
