from __future__ import annotations

from pathlib import Path

import typer
from pydantic import ValidationError

from .artifacts import write_markdown
from .config import load_config
from .git import GitDiscoveryError, InsufficientCommitsError, NoNewCommitsError, discover_git_context, find_repo_root
from .logs import LogWriteError, current_utc_timestamp, write_approval_entry, write_run_entry
from .notes import discover_notes
from .prompt import build_prompt, build_prompt_for_style
from .judge import judge_score
from .providers import ProviderError, get_provider

app = typer.Typer(
    add_completion=False,
    help="Generate tweet drafts from recent committed git changes.",
    invoke_without_command=True,
    no_args_is_help=False,
)


@app.callback()
def generate_tweets(
    force: bool = typer.Option(
        False,
        "--force",
        help="Skip prompts when no new commits exist or fewer commits exist than lookback_commits.",
    ),
) -> None:
    """Auto-discover repo context, generate tweet candidates, and log the run."""

    try:
        repo_root = find_repo_root(Path.cwd())
        config = load_config(repo_root / "diff2tweet.yaml")
        try:
            git_context = discover_git_context(config, cwd=repo_root)
        except NoNewCommitsError as exc:
            typer.echo("No new commits since the last run.")
            if not force and not typer.confirm(
                f"Generate a tweet using the last {exc.lookback_commits} commit(s) anyway?"
            ):
                return
            git_context = discover_git_context(config, cwd=repo_root, force_lookback=True)
        except InsufficientCommitsError as exc:
            typer.echo(
                f"Only {exc.available} commit(s) available, but lookback_commits is set to {exc.requested}."
            )
            if not force and not typer.confirm(
                f"Use the last {exc.available} commit(s) to generate a tweet anyway?"
            ):
                return
            git_context = discover_git_context(
                config.model_copy(update={"lookback_commits": exc.available}),
                cwd=repo_root,
            )
        notes_text = discover_notes(cwd=repo_root)
        # --- PATCH DUAL + JUDGE ---
        from diff2tweet.judge import judge_score
        score, reason = judge_score(config, git_context)
        typer.echo(f"Judge: {score}/10 - {reason}")
        # dual generation
        tweets = []
        styles = ["viral", "humble"] if getattr(config, "dual_mode", False) else ["humble"]
        for style in styles:
            prompt_text = build_prompt_for_style(config, git_context, notes_text, style)
            t = get_provider(config).generate_tweets(prompt_text, config)
            tweets.extend([f"[{style.upper()}] {x}" for x in t])
        # auto-post X if enabled and score high
        if getattr(config, "x_auto_post", False) and score >= getattr(config, "judge_threshold", 7):
            try:
                from .publisher import post_to_x
                for tw in tweets:
                    clean = tw.split("] ",1)[-1] if "] " in tw else tw
                    tid = post_to_x(clean)
                    typer.echo(f"Posted to X: {tid}")
            except Exception as e:
                typer.echo(f"X post failed: {e}", err=True)
        # --- TELEGRAM VALIDATION ---
        if getattr(config, "telegram_enabled", False):
            try:
                from .telegram import send_to_telegram
                header = f"🚀 diff2tweet {git_context.commit_range} | Judge {score}/10 - {reason}

"
                body = "
---
".join(tweets)
                # ajoute les fichiers pour validation X manuelle
                send_to_telegram(header + body + "

✅ Réponds 1 ou 2 pour poster sur X")
                typer.echo("Sent to Telegram for validation")
            except Exception as e:
                typer.echo(f"Telegram failed: {e}", err=True)
        # -------------------------
        output_folder = repo_root / config.output_folder
        run_entry = write_run_entry(output_folder, git_context, tweets)
    except (GitDiscoveryError, LogWriteError, ProviderError, ValidationError, FileNotFoundError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(_format_candidates_output(git_context.commit_range, tweets))
    approvals = _prompt_for_approvals(len(tweets), config.auto_tweet)
    approval_timestamp = current_utc_timestamp() if approvals is not None else None

    try:
        if approvals is not None:
            write_approval_entry(
                output_folder,
                run_entry.generation_timestamp,
                approvals,
                approval_timestamp,
            )
        write_markdown(
            output_folder,
            run_entry.generation_timestamp,
            git_context.commit_range,
            tweets,
            approvals,
            approval_timestamp,
        )
    except LogWriteError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


def _format_candidates_output(commit_range: str, tweets: list[str]) -> str:
    lines = [
        "diff2tweet candidates",
        f"commit_range: {commit_range}",
    ]
    for index, tweet in enumerate(tweets, start=1):
        lines.append(f"{index}. {tweet}")
    return "\n".join(lines)


def _prompt_for_approvals(tweet_count: int, auto_tweet: bool) -> dict[int, bool] | None:
    if not auto_tweet:
        return None
    return {
        index: typer.confirm(f"Approve tweet {index}?", prompt_suffix=" [y/n]: ")
        for index in range(1, tweet_count + 1)
    }


