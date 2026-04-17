"""CLI entry point — `dab` command."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import click
from dotenv import load_dotenv

# Load .env from project root automatically
load_dotenv(Path(__file__).parent.parent / ".env")
from rich.console import Console
from rich.table import Table

console = Console()


def _get_registry():
    from .core.registry import TaskRegistry
    tasks_dir = Path(__file__).parent.parent / "tasks"
    return TaskRegistry(tasks_dir)


@click.group()
@click.version_option(package_name="realdataagentbench")
def cli():
    """DataAgentBench — benchmark LLM agents on data science tasks."""


@cli.command("list")
@click.option("--difficulty", "-d", type=click.Choice(["easy", "medium", "hard"]), default=None)
@click.option("--category", "-c", default=None)
def list_tasks(difficulty, category):
    """List all available tasks."""
    registry = _get_registry()
    tasks = registry.filter(difficulty=difficulty, category=category)

    table = Table(title="DataAgentBench Tasks", show_lines=True)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title")
    table.add_column("Difficulty", style="bold")
    table.add_column("Category")
    table.add_column("Tags")

    diff_colors = {"easy": "green", "medium": "yellow", "hard": "red"}
    for task in tasks:
        color = diff_colors.get(task.difficulty, "white")
        table.add_row(
            task.task_id,
            task.title,
            f"[{color}]{task.difficulty}[/{color}]",
            task.category,
            ", ".join(task.tags),
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(tasks)} tasks[/dim]")


@cli.command("inspect")
@click.argument("task_id")
def inspect_task(task_id):
    """Show full details for a task."""
    registry = _get_registry()
    task = registry.get(task_id)

    console.print(f"\n[bold cyan]{task.task_id}[/bold cyan] — {task.title}")
    console.print(f"[dim]Difficulty:[/dim] {task.difficulty}  |  [dim]Category:[/dim] {task.category}")
    console.print(f"\n[bold]Description:[/bold]\n{task.description}")
    console.print(f"\n[bold]Dataset:[/bold]")
    console.print(f"  Generator: {task.dataset.generator}  |  Rows: {task.dataset.n_rows}  |  Seed: {task.dataset.seed}")
    console.print(f"  Columns: {', '.join(task.dataset.columns)}")
    if task.dataset.injected_issues:
        console.print(f"  Injected issues: {', '.join(task.dataset.injected_issues)}")
    console.print(f"\n[bold]Scoring weights:[/bold]")
    s = task.scoring
    console.print(
        f"  Correctness {s.correctness_weight}  "
        f"Code Quality {s.code_quality_weight}  "
        f"Efficiency {s.efficiency_weight}  "
        f"Stat Validity {s.stat_validity_weight}"
    )
    console.print(f"\n[bold]Evaluation:[/bold]")
    console.print(f"  Max steps: {task.evaluation.max_steps}  |  Timeout: {task.evaluation.timeout_seconds}s")
    console.print(f"  Allowed tools: {', '.join(task.evaluation.allowed_tools)}")


@cli.command("run")
@click.argument("task_id", required=False)
@click.option("--all", "run_all", is_flag=True, help="Run all tasks")
@click.option("--difficulty", "-d", type=click.Choice(["easy", "medium", "hard"]), default=None)
@click.option("--model", "-m", default="claude-sonnet-4-6", show_default=True)
@click.option("--output-dir", "-o", default="outputs", show_default=True)
@click.option("--dry-run", is_flag=True, help="Load dataset and validate without calling API")
@click.option(
    "--budget",
    type=float,
    default=None,
    metavar="USD",
    help="Stop the run if estimated cost exceeds this amount in USD (e.g. --budget 0.05).",
)
@click.option(
    "--max-steps",
    "max_steps",
    type=int,
    default=None,
    metavar="N",
    help="Override the task YAML's max_steps limit (useful for models that need more steps).",
)
def run(task_id, run_all, difficulty, model, output_dir, dry_run, budget, max_steps):
    """Run a task (or all tasks) through the agent."""
    from .core.registry import TaskRegistry
    from .harness.runner import Runner

    tasks_dir = Path(__file__).parent.parent / "tasks"
    registry = TaskRegistry(tasks_dir)

    if budget is not None:
        console.print(f"[dim]Budget cap: ${budget:.2f} per task[/dim]")
    if max_steps is not None:
        console.print(f"[dim]Max steps override: {max_steps}[/dim]")

    runner = Runner(
        registry=registry,
        model=model,
        output_dir=output_dir,
        dry_run=dry_run,
        budget=budget,
        max_steps_override=max_steps,
    )

    if run_all:
        console.print(f"[bold]Running all tasks[/bold] (model={model}, dry_run={dry_run})")
        results = runner.run_all(difficulty=difficulty)
        console.print(f"\n[green]Done.[/green] {len(results)} tasks completed.")
        return

    if not task_id:
        console.print("[red]Provide a TASK_ID or use --all[/red]")
        sys.exit(1)

    console.print(f"[bold]Running[/bold] {task_id} (model={model}, dry_run={dry_run})")
    result = runner.run_task(task_id)

    if dry_run:
        console.print_json(json.dumps(result, indent=2))
    else:
        trace = result.get("trace", {})
        console.print(f"\n[green]Complete.[/green]")
        console.print(f"  Steps: {trace.get('num_steps')}  |  Tokens: {trace.get('total_input_tokens', 0) + trace.get('total_output_tokens', 0)}")
        if trace.get("error"):
            console.print(f"  [red]Error:[/red] {trace['error']}")


@cli.command("score")
@click.argument("result_file")
@click.option("--task-id", "-t", default=None, help="Override task ID from result file")
def score(result_file, task_id):
    """Score a result JSON file and print a scorecard."""
    from .core.registry import TaskRegistry
    from .scoring.composite import CompositeScorer

    result_path = Path(result_file)
    if not result_path.exists():
        console.print(f"[red]File not found:[/red] {result_file}")
        sys.exit(1)

    data = json.loads(result_path.read_text())
    tid = task_id or data.get("task_id")
    if not tid:
        console.print("[red]Cannot determine task_id from result file[/red]")
        sys.exit(1)

    tasks_dir = Path(__file__).parent.parent / "tasks"
    registry = TaskRegistry(tasks_dir)
    task = registry.get(tid)

    scorer = CompositeScorer()
    card = scorer.score(task, data)

    table = Table(title=f"ScoreCard — {card.task_id}", show_lines=True)
    table.add_column("Dimension", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Weight", justify="right")
    table.add_column("Contribution", justify="right")

    rows = [
        ("Correctness", card.correctness, card.weights["correctness"]),
        ("Code Quality", card.code_quality, card.weights["code_quality"]),
        ("Efficiency", card.efficiency, card.weights["efficiency"]),
        ("Stat Validity", card.stat_validity, card.weights["stat_validity"]),
    ]
    for name, score_val, weight in rows:
        contrib = score_val * weight
        table.add_row(name, f"{score_val:.3f}", f"{weight:.2f}", f"{contrib:.3f}")

    table.add_section()
    table.add_row(
        "[bold]DAB Score[/bold]",
        f"[bold]{card.dab_score:.3f}[/bold]",
        "1.00",
        f"[bold]{card.dab_score:.3f}[/bold]",
    )

    console.print(table)


@cli.command("models")
def list_models():
    """Show supported models and which API keys are configured."""
    from .harness.providers import ANTHROPIC_MODELS, GROQ_MODELS, OPENAI_MODELS

    table = Table(title="Supported Models", show_lines=True)
    table.add_column("Model", style="cyan")
    table.add_column("Provider")
    table.add_column("API Key")
    table.add_column("Free tier?")

    ant_key = "✓ set" if os.environ.get("ANTHROPIC_API_KEY") else "[red]✗ missing[/red]"
    oai_key = "✓ set" if os.environ.get("OPENAI_API_KEY") else "[red]✗ missing[/red]"
    groq_key = "✓ set" if os.environ.get("GROQ_API_KEY") else "[red]✗ missing[/red]"

    _aliases = {"claude", "sonnet", "opus", "haiku", "gpt4o",
                "groq", "llama", "llama-70b", "llama-8b", "mixtral"}

    for m in sorted(ANTHROPIC_MODELS - _aliases):
        table.add_row(m, "Anthropic", ant_key, "No")
    for m in sorted(OPENAI_MODELS - _aliases):
        table.add_row(m, "OpenAI", oai_key, "No")
    for m in sorted(GROQ_MODELS - _aliases):
        table.add_row(m, "Groq", groq_key, "[green]Yes[/green]")

    console.print(table)
    console.print("\n[dim]Groq free tier: https://console.groq.com — no credit card needed[/dim]")
    console.print("[dim]Usage: dab run eda_001 --model groq --budget 0.05[/dim]")


if __name__ == "__main__":
    cli()
