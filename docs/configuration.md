# Configuration

ForgeOS loads `.env.local`, then root `.env`, then `backend/.env`. Keep credentials in ignored local files. Do not place keys in frontend environment variables because `NEXT_PUBLIC_*` values are browser-visible.

## Backend Settings

| Variable | Required | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | For model operations | Enables guarded repair, regression-test, and business-brief requests. |
| `OPENAI_REPAIR_MODEL` | No | Model used for repair and regression candidates. Defaults to `gpt-5.6`. |
| `OPENAI_BI_MODEL` | No | Model used for business briefs. Defaults to `gpt-5.6-luna`. |
| `OPENAI_TIMEOUT_SECONDS` | No | OpenAI request timeout. Defaults to `15`. |
| `GITHUB_TOKEN` | Recommended | Raises GitHub API reliability/rate-limit headroom and is required for automated PR creation. |
| `GITHUB_API_BASE` | No | GitHub API base URL. Defaults to `https://api.github.com`. |
| `FORGEOS_ALLOW_DEMO_AI_FALLBACK` | No | Allows the bundled-demo fallback only when explicitly `true`. Defaults to `false`. |
| `FORGEOS_GIT_AUTHOR_NAME` | No | Author name for local repair commits. |
| `FORGEOS_GIT_AUTHOR_EMAIL` | No | Author email for local repair commits. |
| `FORGEOS_ENABLE_GIT_PUSH` | No | Enables push and pull-request creation after verified changes. Defaults to `false`. |

## Frontend Setting

Create `frontend/.env.local` when the API does not use the default address:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Example Local Setup

```env
# .env
OPENAI_API_KEY=...
GITHUB_TOKEN=...
FORGEOS_ENABLE_GIT_PUSH=false
FORGEOS_ALLOW_DEMO_AI_FALLBACK=false
```

Use a GitHub token with the minimum repository permissions needed for the intended action. Enabling push/PR behavior requires write access to the repository and a token permitted to create pull requests.
