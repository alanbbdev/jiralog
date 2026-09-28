from __future__ import annotations

from datetime import date
from typing import Any

import httpx


class JiraApiError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(message)


class JiraClient:
    def __init__(self, base_url: str, email: str, api_token: str) -> None:
        self.client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            auth=(email, api_token),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=30,
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        response = await self.client.request(method, path, **kwargs)
        if response.is_error:
            try:
                detail = response.json().get("errorMessages", [response.text])[0]
            except (ValueError, IndexError, AttributeError):
                detail = response.text or "Erro inesperado do Jira"
            raise JiraApiError(response.status_code, detail)
        return response.json() if response.content else {}

    async def current_user(self) -> dict[str, Any]:
        return await self._request("GET", "/rest/api/3/myself")

    async def issues_with_worklogs(
        self, start_date: date, end_date: date, project: str | None = None
    ) -> list[dict[str, Any]]:
        filters = [f'worklogDate >= "{start_date}"', f'worklogDate <= "{end_date}"']
        if project:
            safe_project = project.replace('"', '\\"')
            filters.append(f'project = "{safe_project}"')

        issues: list[dict[str, Any]] = []
        next_page_token: str | None = None
        while True:
            params: dict[str, Any] = {
                "jql": " AND ".join(filters) + " ORDER BY updated DESC",
                "fields": "summary,project,issuetype,status",
                "maxResults": 100,
            }
            if next_page_token:
                params["nextPageToken"] = next_page_token
            page = await self._request("GET", "/rest/api/3/search/jql", params=params)
            issues.extend(page.get("issues", []))
            next_page_token = page.get("nextPageToken")
            if page.get("isLast", not next_page_token):
                break
        return issues

    async def issue_worklogs(self, issue_key: str) -> list[dict[str, Any]]:
        worklogs: list[dict[str, Any]] = []
        start_at = 0
        while True:
            page = await self._request(
                "GET",
                f"/rest/api/3/issue/{issue_key}/worklog",
                params={"startAt": start_at, "maxResults": 100},
            )
            worklogs.extend(page.get("worklogs", []))
            start_at += len(page.get("worklogs", []))
            if start_at >= page.get("total", 0):
                break
        return worklogs

    async def add_worklog(
        self, issue_key: str, seconds: int, started: str, comment: str | None
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"timeSpentSeconds": seconds, "started": started}
        if comment:
            payload["comment"] = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": comment}],
                    }
                ],
            }
        return await self._request(
            "POST", f"/rest/api/3/issue/{issue_key}/worklog", json=payload
        )