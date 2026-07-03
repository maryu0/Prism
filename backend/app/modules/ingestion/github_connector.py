import shutil
import stat
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import git

SUPPORTED_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx"}
IGNORED_DIR_NAMES = {
    ".git",
    "node_modules",
    "__pycache__",
    "venv",
    ".venv",
    "dist",
    "build",
    ".next",
}


def build_authenticated_url(github_url: str, access_token: str | None) -> str:
    """Embeds the token in the clone URL so `git clone` can authenticate to a
    private repo without a credential prompt. Never logged, never persisted —
    only used transiently to construct the clone command."""
    if not access_token:
        return github_url
    parsed = urlparse(github_url)
    return parsed._replace(netloc=f"{access_token}@{parsed.netloc}").geturl()


def clone_repository(github_url: str, access_token: str | None, branch: str = "main") -> Path:
    workdir = Path(tempfile.mkdtemp(prefix="prism-clone-"))
    clone_url = build_authenticated_url(github_url, access_token)
    # depth=1: a shallow clone — we only need the current file contents to
    # parse structure, not the commit history, so there's no reason to pull it.
    git.Repo.clone_from(clone_url, workdir, branch=branch, depth=1)
    return workdir


def discover_source_files(repo_path: Path) -> list[Path]:
    files = []
    for path in repo_path.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORED_DIR_NAMES for part in path.parts):
            continue
        if path.suffix in SUPPORTED_EXTENSIONS:
            files.append(path)
    return files


def _force_writable_and_retry(func, path, _exc_info):
    """Git writes some objects read-only on disk; shutil.rmtree chokes on
    those on Windows unless we clear the read-only bit first."""
    Path(path).chmod(stat.S_IWRITE)
    func(path)


def cleanup_clone(repo_path: Path) -> None:
    shutil.rmtree(repo_path, onerror=_force_writable_and_retry)
