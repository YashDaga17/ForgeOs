# Security

## Credentials

Keep `OPENAI_API_KEY` and `GITHUB_TOKEN` in ignored local environment files. Rotate a credential if it was exposed, copied to a public location, or committed accidentally. Never place secrets in `frontend/.env*` using a `NEXT_PUBLIC_` name.

ForgeOS reports safe OpenAI telemetry such as request IDs and token counts, but it should not log API keys or raw prompts.

## Repository Execution

ForgeOS clones repositories into per-session workspaces, but repository-owned test commands still execute on the local host. Treat unknown repositories as untrusted code. Run ForgeOS in a disposable development environment for external repositories until stronger process isolation is available.

## Model Boundaries

OpenAI receives bounded repair evidence or deterministic business facts, never an unconstrained repository dump by design. Returned repairs must satisfy structured schema validation, stay inside the supplied source-file boundary, and pass workspace verification before they are retained.

## Git Safety

Push and pull-request creation are disabled by default. Enable them only with a scoped GitHub token and a repository where the configured identity has the intended write permission. ForgeOS commits only inside its workspace clone.

## Reporting

Do not publish vulnerabilities or credentials in a public issue. Follow the contact guidance in [SECURITY.md](../SECURITY.md) for private reporting.
