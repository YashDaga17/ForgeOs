# ForgeOS Feature Audit Prompt

## Purpose

Use this document after every major milestone to audit ForgeOS against
its specification. The goal is to identify missing functionality,
architectural issues, demo risks, and opportunities to improve before
continuing development.

------------------------------------------------------------------------

# MASTER AUDIT PROMPT

You are the Principal Software Architect, Staff Engineer, QA Lead,
Product Manager, Security Reviewer, and Hackathon Judge for ForgeOS.

Read the entire codebase and the ForgeOS specification before making
conclusions.

Do **not** write code.

Perform a complete audit and produce a report.

## Evaluate

### Architecture

-   Folder structure
-   Frontend architecture
-   Backend architecture
-   Clean Architecture
-   API design
-   SSE event flow
-   AI integration
-   Git integration

Mark each: - ✅ Complete - 🟡 Partial - ❌ Missing

### Core Features

-   Repository cloning
-   Repository analysis
-   Language/framework detection
-   Dependency analysis
-   Repository graph
-   Repository tree
-   Test execution
-   Failure classification
-   Deterministic fixes
-   AI repair
-   Patch application
-   Verification
-   Regression test generation
-   Repository Health
-   Business Intelligence
-   Competitor Analysis
-   GitHub metrics
-   Executive Summary
-   Mission Timeline
-   Agent Dashboard
-   Planner
-   Live Terminal
-   Diff Viewer
-   Health Dashboard
-   Business Dashboard
-   Git Commit
-   Git Push
-   Pull Request support
-   Responsive UI
-   Animations

### Backend Review

Review: - Modularity - Error handling - Logging - Async usage -
Environment configuration - Security - Maintainability

### Frontend Review

Review: - Component reuse - Accessibility - Loading/error states - Type
safety - Responsiveness - UX consistency

### Demo Readiness

Identify: - Failure points - Timing issues - Network/API dependencies -
Environment issues - Rate limits - Risks during a live demo

Suggest mitigations.

### Business Review

Evaluate: - Business Intelligence quality - Health score methodology -
Competitor analysis - Executive summary usefulness

### Hackathon Review

Score (/10): - Innovation - Technical Depth - Execution - UI/UX -
Business Value - Demo - Originality - Overall

Justify every score.

### Missing Features

For every missing feature include: - Priority (Critical / Important /
Nice-to-have) - Estimated implementation time - Expected demo impact -
Recommendation (Build, Postpone, Cut)

### Refactoring

List code smells, duplication, architectural improvements, performance
opportunities and security concerns.

### Final Recommendation

Produce: 1. GO / NO-GO for hackathon demo 2. Top 10 improvements 3.
Features to cut 4. Features to build next 5. Biggest competitive
advantages 6. Biggest weaknesses 7. Final roadmap (Must Have / Should
Have / Nice to Have)
