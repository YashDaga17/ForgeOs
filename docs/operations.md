# Operations and Run Artifacts

## Workspaces

Every run gets an isolated workspace at:

```text
backend/app/workspaces/<session-id>/<repository-name>/
```

ForgeOS clones supported GitHub HTTP(S) URLs into this directory. The bundled demo is copied there instead. Patches, tests, commits, and potential rollbacks happen in the workspace, not in the original checkout.

## Run Artifacts

After a pipeline run, ForgeOS writes:

```text
backend/app/runs/run-YYYY-MM-DD-<session-id>/
├── summary.md
├── diff.patch
├── health.json
├── timeline.json
├── business.json
└── architecture.json
```

These files capture the final state of a run. `business.json` includes GitHub/local source information, AI status, and safe OpenAI telemetry metadata. Artifact generation is best-effort; a failure to write artifacts is logged and does not change the pipeline result.

## Git Finalization

When verified code changes exist, ForgeOS:

1. Creates or resets a `forgeos/repair-<repository>` branch in the workspace.
2. Creates a local `ForgeOS automated repair` commit.
3. Stops there unless `FORGEOS_ENABLE_GIT_PUSH=true`.
4. With push enabled, pushes the branch to `origin`.
5. With a valid GitHub token and GitHub remote, creates a pull request.

No changes means no commit. Failed verification triggers rollback before this finalization stage.

## Session Capacity and Recovery

- Maximum active runs: 4.
- Completed stream replay retention: 32 sessions for 15 minutes.
- Unknown explicit stream IDs return `404`.
- Capacity pressure returns `429` from `POST /api/analyze`.

Restarting FastAPI clears in-memory session replay buffers. Use the run artifacts for durable inspection.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Dashboard stays idle | Confirm FastAPI is running at `NEXT_PUBLIC_API_URL` and the browser can reach it. |
| `no_tests` | The repository does not expose a runnable supported test target. Add/declare one in the repository. |
| `error` test status | Review terminal output for collection, dependency, or command errors. The AI repair gate will remain closed. |
| AI activity blocked | Check the gate reason first; a key is not enough without valid repair evidence. |
| GitHub metrics fall back to local | Confirm the URL is public and `GITHUB_TOKEN` has appropriate access. |
| Push/PR skipped | Check `FORGEOS_ENABLE_GIT_PUSH`, the remote, and token permissions. |
