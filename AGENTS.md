# AGENTS.md — required repository entry point

For any coding assistant or agent operating in this repository:

1. **Before editing, evaluating firmware status, or choosing a build baseline**, read [docs/CURRENT-HANDOFF.md](docs/CURRENT-HANDOFF.md), the README, relevant source, and the latest Git commits/branches. Prior chat summaries are not the source of truth.
2. Record the **exact baseline commit SHA and branch** before changes. Confirm whether a later committed fix supersedes the handoff; reconcile any stale notes.
3. As work proceeds, commit coherent source-only work to a development branch **before** long tests or analysis. Keep the intervals between useful commits short. Document failures and unfinished work as well as successes. Never leave the only copy of progress in a Work/chat sandbox.
4. Explicitly separate **proposed**, **edited**, **source-checked**, **assembled**, **bench-flashed**, **bench-verified**, and **vehicle-verified** states. Do not present a successful assembly as hardware validation.
5. **Do not build, package, release, or flash** firmware without the project owner's explicit authorization. Conversation, design approval, or an instruction to preserve progress is not authorization for a build.
6. On interrupted sessions: retrieve GitHub state first; compare both `main` and relevant development branches. Say clearly when uncommitted Work edits are unavailable, and never invent their contents.
7. Preserve working behavior, firmware signatures, tuning compatibility, source checks, and protected MCU addresses. Make the smallest testable change; avoid unrelated refactoring.

The existing fuel-only project does not use spark output. The current handoff identifies an unresolved MSnS spark-output configuration check and a Work session interrupted in the middle of investigating it. **Read the handoff and actual source before attempting that fix.**

This file is agent guidance, not executable project code. It must not be considered permission to build or flash.
