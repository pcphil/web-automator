"""Typer CLI entry point."""

from __future__ import annotations

import asyncio
from typing import Optional

import typer
from dotenv import load_dotenv

load_dotenv()

app = typer.Typer(
    name="web-automator",
    help="LLM-powered web automation agent.",
    add_completion=False,
    invoke_without_command=True,
)


@app.callback()
def root_callback(
    ctx: typer.Context,
    task: Optional[str] = typer.Argument(None, help="Natural-language task to perform in the browser."),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="LLM provider: anthropic | openai"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model ID override"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Print each step"),
) -> None:
    """Run a task directly, or use a subcommand (e.g. `serve`)."""
    if ctx.invoked_subcommand is not None:
        return  # a subcommand (like `serve`) was given — let it handle things

    if not task:
        typer.echo(ctx.get_help())
        raise typer.Exit()

    from web_automator.agent import Agent, build_provider

    async def _run() -> None:
        prov = build_provider(provider, model)
        agent = Agent(provider=prov)
        typer.echo(f"Running task: {task}")
        result = await agent.run(task)

        if verbose and result.steps:
            typer.echo("\n--- Steps ---")
            for step in result.steps:
                status = "OK" if step.success else "ERR"
                typer.echo(f"  [{status}] {step.tool_name}({step.tool_args}) -> {step.tool_result!r}")
            typer.echo("--- End Steps ---\n")

        if result.success:
            typer.echo(f"\nResult:\n{result.result}")
        else:
            typer.echo(f"\nFailed: {result.error}\n{result.result}", err=True)
            raise typer.Exit(code=1)

    asyncio.run(_run())


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", help="Bind host"),
    port: int = typer.Option(8000, "--port", "-p", help="Bind port"),
    reload: bool = typer.Option(False, "--reload", help="Auto-reload on code changes"),
) -> None:
    """Start the FastAPI HTTP server."""
    import uvicorn
    typer.echo(f"Starting server at http://{host}:{port}")
    uvicorn.run(
        "web_automator.server:app",
        host=host,
        port=port,
        reload=reload,
    )


def main() -> None:
    app()


if __name__ == "__main__":
    main()
