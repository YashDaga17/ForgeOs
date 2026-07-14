# ForgeOS Frontend Architecture & Features

ForgeOS frontend is a high-performance, single-page dashboard built using **Next.js 15 (App Router)** and **TypeScript**. It serves as an observability and interaction panel ("Mission Control") for the autonomous engineering pipeline, displaying real-time data driven entirely by a Server-Sent Events (SSE) stream.

---

## 📂 Frontend Project Structure

The frontend source code is located in the [frontend](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend) directory, organized as follows:

*   **[frontend/app/](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/app)**
    *   **[page.tsx](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/app/page.tsx)**: Entry route rendering the main MissionControl dashboard.
    *   **[layout.tsx](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/app/layout.tsx)**: Root template. Sets up typography (Inter & JetBrains Mono) and loads global style utilities.
    *   **[globals.css](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/app/globals.css)**: Implements the custom design system tokens, themes, layouts, and card transitions.
*   **[frontend/components/](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/components)**
    *   **[MissionControl/](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/components/MissionControl)**: Main dashboard assembly grid ([MissionControl.tsx](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/components/MissionControl/MissionControl.tsx)).
    *   **[RepositoryInput/](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/components/RepositoryInput)**: Repository search bar with execution triggers.
    *   **[AgentCards/](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/components/AgentCards)**: Multi-agent monitoring panels displaying specialist details, confidence, and speech bubbles.
    *   **[Mascot/](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/components/Mascot)**: Animated SVG illustration cards ([Mascot.tsx](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/components/Mascot/Mascot.tsx)) for each of the 6 agent personas.
    *   **[DecisionLog/](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/components/DecisionLog)**: Real-time reasoning stream logging engineering decisions for each stage with speech bubble discussions and collapsible history.
    *   **[ReasoningTrace/](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/components/ReasoningTrace)**: Animated evidence-backed explanation of why the pipeline takes each repair action.
    *   **[Timeline/](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/components/Timeline)**: Interactive 14-stage vertical pipeline indicator.
    *   **[LiveTerminal/](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/components/LiveTerminal)**: Auto-scroll console window logging output streams.
    *   **[DiffViewer/](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/components/DiffViewer)**: Syntax-highlighted unified patch browser.
    *   **[HealthDashboard/](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/components/HealthDashboard)**: Visual health charts with dynamic grade card and executive summary text blocks.
    *   **[BusinessDashboard/](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/components/BusinessDashboard)**: Displays business-relevant open-source stats and market context.
    *   **[RepositoryOverview/](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/components/RepositoryOverview)**: Repository Intelligence dashboard displaying 9 dynamic code quality metrics.
    *   **[RepositoryGraph/](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/components/RepositoryGraph)**: Interactive Neo-Brutalist SVG dependency flow diagram mapping frontend, backend, test, and model layers.
    *   **[RepositoryTree/](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/components/RepositoryTree)**: Workspace file list directory browser.
    *   **[PlannerPanel/](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/components/PlannerPanel)**: Visual list of the structured tasks and objectives generated for the repair plan.
*   **[frontend/hooks/](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/hooks)**
    *   **[useEventStream.ts](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/hooks/useEventStream.ts)**: EventSource wrapper connecting to the `/api/stream` endpoint.
    *   **[usePipelineState.ts](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/hooks/usePipelineState.ts)**: Central state manager employing dynamic legacy agent name normalization.
*   **[frontend/services/](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/services)**
    *   **[api.ts](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/services/api.ts)**: REST API services mapping `/api/analyze` request triggers.
*   **[frontend/types/](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/types)**
    *   **[events.ts](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/types/events.ts)**: Discriminated unions defining Pydantic event payloads.
    *   **[pipeline.ts](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/types/pipeline.ts)**: Structures defining local state models and defaults.

---

## 🎨 Design Language: Neo-Brutalist Theme

The application uses a distinctive, high-fidelity **Neo-Brutalist** design language defined in [globals.css](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/app/globals.css). Key styling tokens include:

*   **Borders**: Thick solid borders (`3px solid #0a0a0a`) on cards, buttons, inputs, and layout frames.
*   **Shadows**: Rigid, hard offset drop shadows (`5px 5px 0px #0a0a0a`) instead of soft blurs.
*   **Palette**: A flat light background (`#f0f0f0`) offset by high-contrast primary text (`#0a0a0a`) and bright accent tags:
    *   `--accent-blue`: `#2563eb` (primary links & execution state)
    *   `--accent-green`: `#16a34a` (success state & passed tests)
    *   `--accent-amber`: `#d97706` (warning state & executing tasks)
    *   `--accent-red`: `#dc2626` (error logs & failed tests)
    *   `--accent-purple`: `#7c3aed` (supervisor agent commands)
*   **Micro-animations**: Dynamic interactive visual states:
    *   `fadeIn`: Fades elements into view as pipeline stages change.
    *   `scaleIn`: Renders status indicators and completion overlays smoothly.
    *   `agentPulse`: A breathing scale shift applied to the active agent card.
    *   `buttonClick`: Visual translation offset (`translate(2px, 2px)`) on card hovers and active click states.

## 🖥️ Mission Control Dashboard Panels

The dashboard features **14 specialized panels** designed to map the backend pipeline outputs:

```
+----------------------------------------------------------------------------------------+
|                               [Header & Global Progress Bar]                           |
|                                - Stage name & Progress % -                             |
+----------------------------------------------------------------------------------------+
|                               [Repository URL Input Bar]                               |
+-----------------------------+----------------------------------------------------------+
|   [Repository Intelligence] |                                                          |
|   - Hero health rating %    |                     [Agent Panel]                        |
|   - 8 code quality metrics  | - 6 Specialist Agents with animated SVG Mascots          |
|   - Complexity & Team sizes | - Live speech log, confidence scores, progress indicators|
+-----------------------------+-----------------------------+----------------------------+
|                             |                             |                            |
|      [Live Terminal]        |    [Repository Graph]       |        [Timeline]          |
|  - Subprocess stdout logs   | - Interactive layers flow   | - 14-stage process status  |
|  - Command level feedback   | - Codebase file highlight   | - Current action tracker   |
+-----------------------------+-----------------------------+----------------------------+
|                             |                             |                            |
|       [Diff Viewer]         |      [Planner Panel]        |      [Repository Tree]     |
|  - Unified patch browser    | - Tasks, priorities, files  | - Cloned project files     |
|  - Tabbed file selector     | - Active objective status   | - Navigable tree folders   |
+-----------------------------+-----------------------------+----------------------------+
|      [Health Dashboard]     |                   [Business Dashboard]                   |
|  - 7-dimension bar metrics  | - GitHub Stars, forks, and watchers                      |
|  - Executive summary block  | - Competitor snapshots & AI Product Thesis               |
+----------------------------------------------------------------------------------------+
|                                   [Reasoning Trace]                                    |
|  - Animated evidence-backed explanation of why the pipeline takes each repair action   |
+----------------------------------------------------------------------------------------+
|                                     [Decision Log]                                     |
|  - real-time engineering reasoning explaining stage decisions with speech bubbles      |
|  - Pinned Latest card, Collapsible history, dynamic AI Reasoning Flow timeline         |
+----------------------------------------------------------------------------------------+
```

### 1. Header & Global Progress
Displays the active stage name, overall percentage progress, connection state, and run duration.

### 2. Repository Input Bar
Provides an input box to target a Git repository URL (or run in demo mode) and trigger/launch the analysis run.

### 3. Repository Intelligence (CTO Dashboard)
Renders a high-fidelity summary including:
*   A hero health rating gauge.
*   A grid of 8 structural metrics: complexity level, design patterns, ecosystem health, framework maturity, documentation status, team size recommendation, test coverage, and deployment safety.

### 4. Agent Panel
Shows 6 autonomous agent personas, each with dynamic SVG mascot illustrations:
*   **Atlas**: Directs execution, handles stage routing, and prints global plans.
*   **Forge**: Generates patch files and applies patches to workspace code.
*   **Pulse**: Runs test subprocesses and validates output codes.
*   **Sentinel**: Scans library assets and evaluates safety.
*   **Nitro**: Measures runtimes and latency flags.
*   **Oracle**: Outlines codebase architecture blueprints, parses syntax, and runs business data scrapes.
Mascots support `Idle` (bouncing), `Working` (spinning/shaking), and `Celebration` (dancing) keyframe animations.

### 5. Live Terminal
Streams logs directly from backend subprocesses. Displays real command-line output from `git clone` or `pytest` runs. It features auto-scrolling (which can be locked) and tags lines by source (e.g., red text for test errors, purple for supervisor messages).

### 6. Repository Graph
An interactive SVG block illustrating the dependency architecture: `Frontend` ➔ `API` ➔ `Services` ➔ `Models` ➔ `Tests` ➔ `External APIs`. Node click selections filter and list matching codebase files. Connects to `currentStage` to highlight active layers dynamically.

### 7. Timeline
A vertical tracker showing the execution history of the 14-step pipeline. Completed stages are marked with checks, running stages pulse, and upcoming stages are disabled.

### 8. Planner Panel
Lists the structured tasks generated for the repair plan, complete with title, type, priority, and target file. Highlights the currently active task in real time.

### 9. Diff Viewer
Renders unified git patches created by the AI Repair engine. Integrates a tabbed selector for multi-file patches, line additions (green) and deletions (red) highlighting, and metadata badges showing estimated file risk.

### 10. Repository Tree
An interactive folder file browser. Renders the workspace project structure with custom file icons, line counts, and extensions.

### 11. Health Dashboard
Plots the code quality assessment. Visualizes scores across 7 dimensions (Testing, Security, Architecture, Performance, Documentation, Maintainability, Deployment Readiness) alongside dynamic Executive Summary text.

### 12. Business Dashboard
Displays open-source stars, forks, contributors, open issues, watchers, registry health tags, competitor comparison matrix, and AI-driven business briefings (Thesis, Risks, Next Moves).

### 13. Reasoning Trace
Animates `reasoning_update` events for steps such as reading tracebacks, comparing stack traces, identifying root causes, generating patches, verifying assumptions, and approving patches.

### 14. Decision Log
Streams the core engineering decisions made by agents during each of the 14 pipeline stages:
*   **Pinned Card**: Keeps the latest stage decision fully expanded at the top.
*   **Discussion Bubbles**: Renders the decision reason like an active engineering discussion.
*   **Collapsible List**: Collapses older decisions sequentially in a historical list.
*   **Evidence Record**: Shows the reason, evidence, action, expected outcome, confidence, and final status for each decision.

---

## 🔄 State Management & SSE Sync

The frontend's state is driven entirely by Server-Sent Events (SSE). It relies on two main hooks:

1.  **[useEventStream.ts](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/hooks/useEventStream.ts)**:
    *   Initiates an `EventSource` connection to `GET /api/stream?session_id=<session_id>`.
    *   Triggers callbacks for connection state changes (`onConnect`, `onDisconnect`).
    *   Parses incoming SSE JSON payloads and forwards them to the state reducer (`onEvent`).
2.  **[usePipelineState.ts](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/hooks/usePipelineState.ts)**:
    *   Maintains the global `PipelineState` object.
    *   Implements a state reducer function `reduceEvent(state, event)` that matches incoming SSE `event` types and updates the corresponding slice of state.
    *   Features legacy agent name normalization (using a `LEGACY_AGENT_MAP`) mapping old agent names to the 6 new dynamic SVGs.
    *   Ensures state mutations are pure and components re-render selectively based on updated variables.
    *   Because the backend buffers up to 200 events per session, reloading the page or reconnecting to a session immediately replays all events, fully restoring the UI state.
