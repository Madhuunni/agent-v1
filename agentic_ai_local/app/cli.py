from __future__ import annotations

import os
from typing import Optional

import typer
from dotenv import load_dotenv
from rich.console import Console

from app.config import RUN_LOGS_DIR, get_settings
from app.graph.builder import build_graph
from app.graph.state import initial_state
from app.utils.logging import configure_logging
from app.utils.paths import timestamp

cli = typer.Typer(no_args_is_help=True)
console = Console()


@cli.callback()
def main() -> None:
    """Run the local Selenium automation agent."""


def _parse_bool(value: bool | str) -> bool:
    if isinstance(value, bool):
        return value

    normalized = value.strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False

    raise typer.BadParameter("expected a boolean value (true/false)")


@cli.command()
def run(
    prompt: str,
    model: Optional[str] = typer.Option(None, "--model"),
    max_retries: int = typer.Option(2, "--max-retries"),
    headless: str = typer.Option(
        "true",
        "--headless",
        help="Run browser tests in headless mode. Accepts true/false.",
    ),
    verbose: bool = typer.Option(False, "--verbose"),
) -> None:
    load_dotenv()
    configure_logging(verbose)
    if model:
        os.environ["LOCAL_LLM_MODEL"] = model
    os.environ["HEADLESS"] = "true" if _parse_bool(headless) else "false"
    get_settings()
    result = build_graph().invoke(initial_state(prompt, max_retries=max_retries))
    report = result.get("final_report") or "No final report generated."
    console.print(report)
    path = RUN_LOGS_DIR / f"final_report_{timestamp()}.md"
    path.write_text(report)
    console.print(f"[green]Saved report:[/green] {path}")


if __name__ == "__main__":
    cli()
