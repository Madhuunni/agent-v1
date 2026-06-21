from __future__ import annotations
import os
from pathlib import Path
import typer
from dotenv import load_dotenv
from rich.console import Console
from app.config import RUN_LOGS_DIR, get_settings
from app.graph.builder import build_graph
from app.graph.state import initial_state
from app.utils.logging import configure_logging
from app.utils.paths import timestamp

cli = typer.Typer(); console = Console()

@cli.command()
def run(prompt: str, model: str = typer.Option(None, "--model"), max_retries: int = 2, headless: bool = True, verbose: bool = False) -> None:
    load_dotenv(); configure_logging(verbose)
    if model: os.environ['LOCAL_LLM_MODEL'] = model
    os.environ['HEADLESS'] = 'true' if headless else 'false'
    get_settings()
    result = build_graph().invoke(initial_state(prompt, max_retries=max_retries))
    report = result.get('final_report') or 'No final report generated.'
    console.print(report)
    path = RUN_LOGS_DIR / f"final_report_{timestamp()}.md"; path.write_text(report)
    console.print(f"[green]Saved report:[/green] {path}")

if __name__ == '__main__':
    cli()
