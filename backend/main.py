from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .demo_data import dashboard_data
from .jira_client import JiraApiError, JiraClient

load_dotenv(Path(__file__).parent / ".env")


def env_flag(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


def jira_client() -> JiraClient | None:
    values = [
        os.getenv("JIRA_BASE_URL", "").strip(),
        os.getenv("JIRA_EMAIL", "").strip(),
        os.getenv("JIRA_API_TOKEN", "").strip(),
    ]
    return JiraClient(*values) if all(values) else None


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(title="Tempo Jira API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class WorklogInput(BaseModel):
    issue_key: str = Field(min_length=2, max_length=50)
    seconds: int = Field(gt=0, le=86400)
    started: datetime
    comment: str | None = Field(default=None, max_length=1000)


def project_color(project_name: str) -> str:
    colors = ["#2563eb", "#14b8a6", "#f97316", "#eab308", "#db2777"]
    return colors[sum(ord(char) for char in project_name) % len(colors)]


def plain_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if not isinstance(value, dict):
        return ""
    texts: list[str] = []
    for node in value.get("content", []):
        if isinstance(node, dict):
            if node.get("text"):
                texts.append(node["text"])
            texts.append(plain_text(node))
    return " ".join(filter(None, texts)).strip()


@app.get("/api/status")
async def status() -> dict[str, Any]:
    if env_flag("DEMO_MODE"):
        return {"connected": False, "demo": True, "user": "Modo demonstracao"}
    client = jira_client()
    if not client:
        return {"connected": False, "demo": True, "user": "Modo demonstracao"}
    try:
        user = await client.current_user()
        return {"connected": True, "demo": False, "user": user.get("displayName")}
    except JiraApiError as error:
        raise HTTPException(error.status_code, str(error)) from error
    finally:
        await client.close()


@app.get("/api/dashboard")
async def dashboard(
    start: date = Query(),
    end: date = Query(),
    project: str | None = Query(default=None),
    account_id: str | None = Query(default=None),
) -> dict[str, Any]:
    if start > end or (end - start).days > 92:
        raise HTTPException(400, "O periodo deve ter no maximo 93 dias.")

    client = jira_client()
    if not client or env_flag("DEMO_MODE"):
        return {**dashboard_data(start, end), "demo": True}

    try:
        issues = await client.issues_with_worklogs(start, end, project)
        worklog_groups = await asyncio.gather(
            *(client.issue_worklogs(issue["key"]) for issue in issues)
        )
        entries: list[dict[str, Any]] = []
        for issue, worklogs in zip(issues, worklog_groups, strict=True):
            fields = issue["fields"]
            project_name = fields["project"]["name"]
            for worklog in worklogs:
                worklog_date = date.fromisoformat(worklog["started"][:10])
                author = worklog.get("author", {})
                if not start <= worklog_date <= end:
                    continue
                if account_id and author.get("accountId") != account_id:
                    continue
                display_name = author.get("displayName", "Usuario Jira")
                entries.append(
                    {
                        "id": worklog["id"],
                        "issueKey": issue["key"],
                        "summary": fields.get("summary", "Sem titulo"),
                        "project": project_name,
                        "projectColor": project_color(project_name),
                        "author": display_name,
                        "initials": "".join(part[0] for part in display_name.split()[:2]).upper(),
                        "date": worklog_date.isoformat(),
                        "seconds": worklog["timeSpentSeconds"],
                        "hours": round(worklog["timeSpentSeconds"] / 3600, 2),
                        "comment": plain_text(worklog.get("comment")) or "Sem comentario",
                    }
                )
        return {
            "entries": sorted(entries, key=lambda item: item["date"], reverse=True),
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "demo": False,
        }
    except JiraApiError as error:
        raise HTTPException(error.status_code, str(error)) from error
    finally:
        await client.close()


@app.post("/api/worklogs", status_code=201)
async def create_worklog(payload: WorklogInput) -> dict[str, Any]:
    client = jira_client()
    if not client or env_flag("DEMO_MODE"):
        raise HTTPException(503, "Configure as credenciais do Jira para registrar horas.")
    started = payload.started.strftime("%Y-%m-%dT%H:%M:%S.000%z")
    try:
        result = await client.add_worklog(
            payload.issue_key.upper(), payload.seconds, started, payload.comment
        )
        return {"id": result.get("id"), "issueKey": payload.issue_key.upper()}
    except JiraApiError as error:
        raise HTTPException(error.status_code, str(error)) from error
    finally:
        await client.close()


DIST_DIR = Path(__file__).resolve().parents[1] / "dist"
if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

    @app.get("/{path:path}")
    async def frontend(path: str) -> FileResponse:
        candidate = DIST_DIR / path
        return FileResponse(candidate if candidate.is_file() else DIST_DIR / "index.html")