"""FastAPI HTTP server."""

from __future__ import annotations

from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="Web Automator API", version="0.1.0")


class RunRequest(BaseModel):
    task: str
    provider: Optional[str] = None
    model: Optional[str] = None


class StepOut(BaseModel):
    step_number: int
    tool_name: str
    tool_args: dict
    tool_result: str
    success: bool


class RunResponse(BaseModel):
    result: str
    steps: list[StepOut]
    success: bool
    error: Optional[str] = None


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/run", response_model=RunResponse)
async def run_task(req: RunRequest) -> RunResponse:
    from web_automator.agent import Agent, build_provider

    try:
        provider = build_provider(req.provider, req.model)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    agent = Agent(provider=provider)
    result = await agent.run(req.task)

    return RunResponse(
        result=result.result,
        steps=[
            StepOut(
                step_number=s.step_number,
                tool_name=s.tool_name,
                tool_args=s.tool_args,
                tool_result=s.tool_result,
                success=s.success,
            )
            for s in result.steps
        ],
        success=result.success,
        error=result.error,
    )
