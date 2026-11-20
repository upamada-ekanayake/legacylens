import asyncio
import os
import re
from collections import deque

import httpx

from .models import GraphPayload
from .parser import build_graph, is_supported

API_ROOT = "https://api.github.com"
NO_SOURCE_MESSAGE = "No supported source files found (.py, .ts, .js). Try the sample project."
SKIP_DIRS = {
    ".git", "node_modules", "vendor", "dist", "build", "__pycache__",
    ".venv", "venv", "env", ".next", "coverage", "site-packages",
}
MAX_FILE_BYTES = 200_000
TOTAL_TIMEOUT_SECONDS = 10.0

_REPO_URL = re.compile(
    r"^https?://(?:www\.)?github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?(?:/.*)?/?$"
)


class FetchError(Exception):
    """User-facing ingestion error (maps to HTTP 400)."""


def parse_repo_url(url: str) -> tuple[str, str]:
    match = _REPO_URL.match(url.strip())
    if not match:
        raise FetchError("Invalid GitHub URL. Use the form https://github.com/<owner>/<repo>.")
    return match.group("owner"), match.group("repo")


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "legacylens"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _raise_for_status(response: httpx.Response, owner: str, repo: str) -> None:
    if response.status_code == 200:
        return
    if response.status_code == 404:
        raise FetchError(f"Repository {owner}/{repo} was not found or is private. Only public repos are supported.")
    if response.status_code in (403, 429):
        raise FetchError("GitHub API rate limit reached. Try again later or use the sample project.")
    raise FetchError(f"GitHub returned an unexpected status ({response.status_code}). Try the sample project.")


async def _list_source_files(
    client: httpx.AsyncClient, owner: str, repo: str, max_files: int, max_depth: int
) -> tuple[list[dict], bool]:
    """Breadth-first directory walk. Returns (file entries, truncated). Stops once max_files + 1 are seen."""
    found: list[dict] = []
    queue: deque[tuple[str, int]] = deque([("", 0)])
    while queue:
        directory, depth = queue.popleft()
        url = f"{API_ROOT}/repos/{owner}/{repo}/contents/{directory}".rstrip("/")
        response = await client.get(url)
        _raise_for_status(response, owner, repo)
        entries = response.json()
        if not isinstance(entries, list):
            continue
        for entry in sorted(entries, key=lambda e: e.get("path", "")):
            kind, path = entry.get("type"), entry.get("path", "")
            if kind == "dir":
                if entry.get("name") not in SKIP_DIRS and depth < max_depth:
                    queue.append((path, depth + 1))
            elif kind == "file" and is_supported(path) and entry.get("size", 0) <= MAX_FILE_BYTES:
                if entry.get("download_url"):
                    found.append(entry)
                    if len(found) > max_files:
                        return found[:max_files], True
    return found, False


async def _download(client: httpx.AsyncClient, sem: asyncio.Semaphore, entry: dict) -> tuple[str, str | None]:
    async with sem:
        try:
            response = await client.get(entry["download_url"])
            if response.status_code == 200:
                return entry["path"], response.text
        except httpx.HTTPError:
            pass
    return entry["path"], None


async def _fetch(repo_url: str, max_files: int, max_depth: int) -> GraphPayload:
    owner, repo = parse_repo_url(repo_url)
    async with httpx.AsyncClient(headers=_headers(), timeout=8.0, follow_redirects=True) as client:
        entries, truncated = await _list_source_files(client, owner, repo, max_files, max_depth)
        if not entries:
            raise FetchError(NO_SOURCE_MESSAGE)
        sem = asyncio.Semaphore(10)
        results = await asyncio.gather(*(_download(client, sem, e) for e in entries))

    files = {path: text for path, text in results if text is not None}
    if not files:
        raise FetchError("Could not download any source files from GitHub. Try the sample project.")

    nodes, edges, cycles = build_graph(files)
    notice = (
        f"Repository has more than {max_files} supported source files; analyzed the first {max_files} "
        f"found breadth-first (directory depth <= {max_depth})."
        if truncated
        else None
    )
    return GraphPayload(
        source_type="github",
        repo_name=f"{owner}/{repo}",
        truncated=truncated,
        truncation_notice=notice,
        nodes=nodes,
        edges=edges,
        cycles=cycles,
    )


async def fetch_github_graph(repo_url: str, max_files: int = 50, max_depth: int = 3) -> GraphPayload:
    """Fetch via the GitHub Contents API (no git clone) and build the graph within a 10s budget."""
    try:
        return await asyncio.wait_for(_fetch(repo_url, max_files, max_depth), timeout=TOTAL_TIMEOUT_SECONDS)
    except asyncio.TimeoutError as exc:
        raise FetchError("GitHub fetch timed out. Try a smaller repo or use the sample project.") from exc
    except httpx.HTTPError as exc:
        raise FetchError("Could not reach GitHub. Check your connection or use the sample project.") from exc
