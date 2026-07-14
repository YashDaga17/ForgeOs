# Business Intelligence

ForgeOS treats GitHub as the primary business-data source. The goal is not to invent market claims; it is to combine observable repository signals with a concise, constrained interpretation.

## Data Sources

For a GitHub URL, ForgeOS requests:

- Repository metadata: stars, forks, watchers, open issues, language, license, topics, update time.
- Contributor count.
- Releases and release cadence.
- A small topic/language-based competitor snapshot when GitHub returns enough data.
- Local dependency-manifest signals from the isolated workspace.

If GitHub metadata cannot be retrieved, ForgeOS falls back to repository-derived signals and labels the result `local` rather than presenting it as GitHub data.

## OpenAI Business Brief

When `OPENAI_API_KEY` is configured, Oracle sends only collected facts to the OpenAI Responses API. The brief is structurally validated and may contain:

- Executive summary
- Product thesis
- Engineering risk
- Recommended next move
- Confidence

The prompt explicitly forbids unsupported claims about users, revenue, market share, security findings, or test coverage. A failed or invalid response leaves the deterministic summary in place and records a failed AI status.

## Dashboard Evidence

The Business Dashboard displays the source, GitHub metrics, brief content, and model status. The Agent Panel also receives an `ai_activity` event for Oracle with the operation status, model, safe request ID metadata, and token totals when the provider returns them.

## Limits

Competitor relevance is heuristic: a topic or language match is not proof that projects compete. GitHub availability, private repositories, and rate limits can reduce available facts. Interpret all business output as an engineering decision aid, not an investment recommendation.
