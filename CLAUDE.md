# CLAUDE.md

This repo uses the AI work harness in `ai/`. Follow it for every task.

1. Read `ai/context/PROJECT.md` (architecture, API contract, domain rules) and `ai/context/KNOWN_ISSUES.md` first.
2. Follow `ai/workflows/standard-loop.md`: record a task (`python ai/harness.py new-task "title"`) → plan → implement via the matching subagent (backend / frontend / data-analyst) → `python ai/harness.py check` → `reviewer` → commit.
3. Never commit model weights (*.pt, *.gguf), raw utterance data, node_modules, or secrets. Utterance data is personal data of elderly users.
4. Agent definitions are edited in `ai/agents/`, then `python ai/harness.py sync-agents` (never edit `.claude/agents/` directly).
5. Explain to the user in Korean; write code, commands, and identifiers in English.
