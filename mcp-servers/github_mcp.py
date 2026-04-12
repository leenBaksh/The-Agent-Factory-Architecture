"""
GitHub MCP Server for Digital FTEs

Provides tool access for:
- Repository management
- Issue tracking
- Pull request operations
- File operations
"""

import os
import logging
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    "github-server",
    description="GitHub API integration for repository management",
    dependencies=["httpx"],
)

# Configuration
GITHUB_TOKEN = os.getenv("MCP_GITHUB_TOKEN")
GITHUB_API = "https://api.github.com"

if not GITHUB_TOKEN:
    logger.warning("MCP_GITHUB_TOKEN not set - GitHub MCP server will fail on API calls")


async def get_headers() -> dict:
    """Get authorization headers for GitHub API."""
    if not GITHUB_TOKEN:
        raise ValueError("MCP_GITHUB_TOKEN environment variable not set")
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


@mcp.tool()
async def get_repo_info(
    owner: str,
    repo: str,
) -> dict:
    """
    Get repository information and metadata.

    Args:
        owner: Repository owner (user or org)
        repo: Repository name

    Returns:
        dict with repository details
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{GITHUB_API}/repos/{owner}/{repo}",
                headers=await get_headers(),
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()

            return {
                "success": True,
                "name": data["full_name"],
                "description": data.get("description", ""),
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "open_issues": data.get("open_issues_count", 0),
                "language": data.get("language"),
                "default_branch": data.get("default_branch"),
                "visibility": data.get("visibility"),
                "updated_at": data.get("updated_at"),
            }
        except httpx.HTTPError as e:
            logger.error(f"GitHub repo info failed: {e}")
            return {"success": False, "error": str(e)}


@mcp.tool()
async def list_issues(
    owner: str,
    repo: str,
    state: str = "open",
    limit: int = 10,
    labels: Optional[str] = None,
) -> dict:
    """
    List repository issues.

    Args:
        owner: Repository owner
        repo: Repository name
        state: Issue state (open, closed, all)
        limit: Maximum issues to return (default: 10)
        labels: Comma-separated label filter

    Returns:
        dict with list of issues
    """
    params = {"state": state, "per_page": min(limit, 100)}
    if labels:
        params["labels"] = labels

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/issues",
                headers=await get_headers(),
                params=params,
                timeout=10.0,
            )
            response.raise_for_status()
            issues = response.json()[:limit]

            return {
                "success": True,
                "count": len(issues),
                "issues": [
                    {
                        "number": i["number"],
                        "title": i["title"],
                        "state": i["state"],
                        "labels": [l["name"] for l in i.get("labels", [])],
                        "created_at": i["created_at"],
                        "url": i["html_url"],
                    }
                    for i in issues
                ],
            }
        except httpx.HTTPError as e:
            logger.error(f"GitHub issues list failed: {e}")
            return {"success": False, "error": str(e)}


@mcp.tool()
async def create_issue(
    owner: str,
    repo: str,
    title: str,
    body: str,
    labels: Optional[list[str]] = None,
) -> dict:
    """
    Create a new issue in a repository.

    Args:
        owner: Repository owner
        repo: Repository name
        title: Issue title
        body: Issue description (markdown supported)
        labels: Optional list of labels

    Returns:
        dict with issue details
    """
    payload = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{GITHUB_API}/repos/{owner}/{repo}/issues",
                headers=await get_headers(),
                json=payload,
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()

            return {
                "success": True,
                "number": data["number"],
                "url": data["html_url"],
                "title": data["title"],
            }
        except httpx.HTTPError as e:
            logger.error(f"GitHub issue creation failed: {e}")
            return {"success": False, "error": str(e)}


@mcp.tool()
async def get_pull_requests(
    owner: str,
    repo: str,
    state: str = "open",
    limit: int = 10,
) -> dict:
    """
    List pull requests in a repository.

    Args:
        owner: Repository owner
        repo: Repository name
        state: PR state (open, closed, all)
        limit: Maximum PRs to return

    Returns:
        dict with list of pull requests
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/pulls",
                headers=await get_headers(),
                params={"state": state, "per_page": min(limit, 100)},
                timeout=10.0,
            )
            response.raise_for_status()
            prs = response.json()[:limit]

            return {
                "success": True,
                "count": len(prs),
                "pull_requests": [
                    {
                        "number": pr["number"],
                        "title": pr["title"],
                        "state": pr["state"],
                        "user": pr["user"]["login"],
                        "created_at": pr["created_at"],
                        "url": pr["html_url"],
                    }
                    for pr in prs
                ],
            }
        except httpx.HTTPError as e:
            logger.error(f"GitHub PR list failed: {e}")
            return {"success": False, "error": str(e)}


@mcp.tool()
async def get_file_content(
    owner: str,
    repo: str,
    path: str,
    ref: Optional[str] = None,
) -> dict:
    """
    Get file content from a repository.

    Args:
        owner: Repository owner
        repo: Repository name
        path: File path in the repo
        ref: Branch or tag name (default: default branch)

    Returns:
        dict with file content and metadata
    """
    params = {"ref": ref} if ref else {}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}",
                headers={**await get_headers(), "Accept": "application/vnd.github.raw+json"},
                params=params,
                timeout=10.0,
            )
            response.raise_for_status()

            # Check if it's a file or directory
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                data = response.json()
                if isinstance(data, list):
                    return {
                        "success": True,
                        "type": "directory",
                        "path": path,
                        "files": [item["name"] for item in data],
                    }
                else:
                    import base64
                    content = base64.b64decode(data.get("content", "")).decode("utf-8")
                    return {
                        "success": True,
                        "type": "file",
                        "path": path,
                        "content": content,
                        "sha": data.get("sha"),
                        "size": data.get("size"),
                    }
            else:
                return {
                    "success": True,
                    "type": "file",
                    "path": path,
                    "content": response.text,
                }
        except httpx.HTTPError as e:
            logger.error(f"GitHub file content failed: {e}")
            return {"success": False, "error": str(e)}


@mcp.tool()
async def search_repos(
    query: str,
    sort: str = "stars",
    order: str = "desc",
    limit: int = 10,
) -> dict:
    """
    Search GitHub repositories.

    Args:
        query: Search query (e.g., "language:python stars:>1000")
        sort: Sort field (stars, forks, updated)
        order: Sort order (asc, desc)
        limit: Maximum results

    Returns:
        dict with search results
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{GITHUB_API}/search/repositories",
                headers=await get_headers(),
                params={
                    "q": query,
                    "sort": sort,
                    "order": order,
                    "per_page": min(limit, 100),
                },
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()

            return {
                "success": True,
                "total_count": data.get("total_count", 0),
                "results": [
                    {
                        "name": r["full_name"],
                        "description": r.get("description", ""),
                        "stars": r.get("stargazers_count", 0),
                        "language": r.get("language"),
                        "url": r["html_url"],
                    }
                    for r in data.get("items", [])[:limit]
                ],
            }
        except httpx.HTTPError as e:
            logger.error(f"GitHub repo search failed: {e}")
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    mcp.run()
