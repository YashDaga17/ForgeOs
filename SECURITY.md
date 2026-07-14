# Security Policy

## Supported Deployment Model

ForgeOS is intended for local or controlled development environments. It clones repositories, inspects their source, and may execute repository-owned test commands. It is not currently a hardened multi-tenant code-execution service.

## Report a Vulnerability

Do not disclose vulnerabilities in public issues. Report them privately to the project maintainer through the repository's configured security contact. Before publishing ForgeOS, replace this placeholder with a monitored address:

```text
security@example.com
```

Include the affected version, reproduction steps, impact, and any proof of concept needed to understand the issue.

## Credentials

- Keep `.env`, `.env.local`, GitHub tokens, and OpenAI API keys out of git.
- Rotate any credential that was ever committed, pasted into a public channel, or exposed in an artifact.
- Use least-privilege GitHub tokens. PR creation needs repository write access; business intelligence does not.
- Keep `FORGEOS_ENABLE_GIT_PUSH=false` unless push and PR finalization are explicitly intended.

## Repository Execution

- Treat submitted repositories and their tests as untrusted code.
- Run ForgeOS in a disposable machine or isolated environment for unknown repositories.
- Do not expose the local API publicly without authentication and network controls.
- Review patches and artifact bundles before enabling push or PR creation.

See [docs/security.md](docs/security.md) for the full data-flow, OpenAI, git, and operational guidance.
