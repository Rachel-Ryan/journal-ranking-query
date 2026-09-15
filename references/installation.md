# Cross-platform Installation

Keep the entire `journal-ranking-query` directory together. The runtime needs `SKILL.md`, `scripts/query_journal.py`, and `assets/journal_rankings.sqlite3`; the `references` directory documents behavior, and `agents/openai.yaml` adds OpenAI-specific display metadata without changing the portable core.

## Codex

Copy the complete directory into the user's Codex skills directory so the final path is:

```text
~/.codex/skills/journal-ranking-query/SKILL.md
```

Restart or refresh the Agent's skill discovery if required by the current Codex surface. Invoke it explicitly as `$journal-ranking-query`, or ask for a journal's JCR/SSCI/CCF/FMS/CSSCI information.

## Claude Code

For a project-scoped skill, copy the complete directory to:

```text
<project>/.claude/skills/journal-ranking-query/SKILL.md
```

For a personal skill, copy it to:

```text
~/.claude/skills/journal-ranking-query/SKILL.md
```

## Other Agent platforms

For an Agent Skills-compatible platform, import or copy this directory without changing its internal layout. For a platform that supports only prompt skills, point its skill definition at `SKILL.md` and ensure it can execute a local Python 3 process with read access to the whole directory.

The package does not require network access, third-party Python packages, Excel software, or access to the original source workbooks. If a platform cannot run local scripts or preserve the bundled SQLite asset, it cannot provide the same deterministic behavior; use that platform's local-tool or desktop-agent mode if available.
