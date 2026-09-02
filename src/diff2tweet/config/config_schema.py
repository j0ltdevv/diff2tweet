from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LlmProvider(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


class DiffToTweetConfig(BaseModel):
    """Validated non-secret project configuration loaded from YAML."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    provider: LlmProvider = LlmProvider.OPENAI
    model: str = Field(min_length=1)
    project_name: str = Field(default="")
    project_summary: str = Field(default="")
    project_audience: str = Field(default="")
    project_stage: Literal["prototype", "beta", "launched"] = "prototype"
    project_tone: Literal["technical", "founder", "casual"] = "technical"
    project_key_terms: list[str] = Field(default_factory=list)
    custom_instructions: str = Field(default="")
    forced_hashtags: list[str] = Field(default_factory=list)
    character_limit: int = Field(default=280, ge=1, le=10000)
    num_candidates: int = Field(default=1, ge=1, le=10)
    lookback_commits: int = Field(default=5, ge=1)
    commit_subject_min_chars: int = Field(default=20, ge=0)
    readme_max_chars: int = Field(default=0, ge=0)
    context_max_chars: int = Field(default=12000, ge=1)
    max_doc_diff_sections: int = Field(default=3, ge=0)
    max_doc_section_chars: int = Field(default=1000, ge=0)
    diff_ignore_patterns: list[str] = Field(
        default_factory=lambda: [
            # Dependency lock files
            "*.lock",
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "poetry.lock",
            "Pipfile.lock",
            "go.sum",
            # Go module file (version bumps only, rarely tweetable)
            "go.mod",
            # Minified / compiled assets
            "*.min.js",
            "*.min.css",
            "*.d.ts",
            # Build output
            "dist/**",
            "build/**",
            # Test files
            "test_*.py",
            "*_test.py",
            "*.test.js",
            "*.test.ts",
            "*.spec.js",
            "*.spec.ts",
            "*.vitest.ts",
            "tests/**",
            "test/**",
            "**/tests/**",
            "**/__tests__/**",
            # Noisy config / tooling files
            ".prettierrc",
            ".eslintrc",
            ".eslintignore",
            ".editorconfig",
            # CI / GitHub config (action bumps are rarely tweetable)
            ".github/**",
            # Generated changelogs and release notes (assembled content, not novel)
            "CHANGELOG.md",
            "CHANGELOG",
            "CHANGES.md",
            "HISTORY.md",
            "CHANGES",
            "release-notes.md",
            "release_notes.md",
        ]
    )
    diff_ignore_patterns_extra: list[str] = Field(default_factory=list)
    output_folder: Path = Field(default=Path(".diff2tweet"))
    auto_tweet: bool = Field(default=False)
    # --- DUAL PATCH ---
    judge_enabled: bool = Field(default=False)
    judge_threshold: int = Field(default=7, ge=1, le=10)
    dual_mode: bool = Field(default=False)
    style_viral_path: Path = Field(default=Path(".diff2tweet/STYLE_VIRAL.md"))
    style_humble_path: Path = Field(default=Path(".diff2tweet/STYLE_HUMBLE.md"))
    x_auto_post: bool = Field(default=False)
    telegram_enabled: bool = Field(default=False)

    @field_validator("forced_hashtags")
    @classmethod
    def validate_forced_hashtags(cls, hashtags: list[str]) -> list[str]:
        normalized: list[str] = []
        for hashtag in hashtags:
            cleaned = hashtag.strip()
            if not cleaned:
                raise ValueError("forced_hashtags cannot contain empty values")
            if not cleaned.startswith("#"):
                raise ValueError("forced_hashtags entries must start with '#'")
            normalized.append(cleaned)
        return normalized

    @field_validator("diff_ignore_patterns")
    @classmethod
    def validate_diff_ignore_patterns(cls, patterns: list[str]) -> list[str]:
        normalized: list[str] = []
        for pattern in patterns:
            cleaned = pattern.strip()
            if not cleaned:
                raise ValueError("diff_ignore_patterns cannot contain empty values")
            normalized.append(cleaned)
        return normalized

    @field_validator("diff_ignore_patterns_extra")
    @classmethod
    def validate_diff_ignore_patterns_extra(cls, patterns: list[str]) -> list[str]:
        normalized: list[str] = []
        for pattern in patterns:
            cleaned = pattern.strip()
            if not cleaned:
                raise ValueError("diff_ignore_patterns_extra cannot contain empty values")
            normalized.append(cleaned)
        return normalized

    @field_validator("project_key_terms")
    @classmethod
    def validate_project_key_terms(cls, key_terms: list[str]) -> list[str]:
        normalized: list[str] = []
        for key_term in key_terms:
            cleaned = key_term.strip()
            if not cleaned:
                raise ValueError("project_key_terms cannot contain empty values")
            normalized.append(cleaned)
        return normalized

    @field_validator("output_folder")
    @classmethod
    def validate_output_folder(cls, output_folder: Path) -> Path:
        if output_folder.is_absolute():
            raise ValueError("output_folder must be a relative path")
        return output_folder
