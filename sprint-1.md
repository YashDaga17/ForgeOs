# ForgeOS Feature Sprint 1 — Decision Log Implementation Plan

Implement a world-class Decision Log that details and explains every engineering decision made by ForgeOS throughout the 14-stage execution pipeline.

## User Review Required

> [!IMPORTANT]
> **Dashboard Placement**: The Decision Log is designed as a core experience panel. We propose placing it in the main dashboard grid as a new full-width row (`gridColumn: "1 / 4"`) just above the final results banner, or adjacent to the Diff Viewer. This ensures it's highly visible and provides an immediate summary of the reasoning sequence.
>
> **Styling Palette**: We will styling the decisions using a Neo-Brutalist design (thick borders, offset hard shadows, bright emoji labels) color-coded by the stage agent persona (e.g., Purple for Supervisor, Blue for Analyst, Green for QA, etc.).

## Open Questions

None. The requirements specify structured backend schemas, SSE transmission, and a collapsible, animated timeline front-end component, which we cover fully below.

## Proposed Changes

---

### Backend Components

#### [MODIFY] [events.py](file:///Users/yashdaga/Desktop/dev/ForgeOs/backend/app/models/events.py)
- Add `"decision_event"` to the `EventType` enum.
- Define the `DecisionEvent` Pydantic model containing:
  - `stage`: `str`
  - `agent`: `AgentName`
  - `reason`: `str`
  - `evidence`: `str`
  - `action_taken`: `str`
  - `expected_outcome`: `str | None`
  - `confidence`: `float`
  - `status`: `str`

#### [NEW] [decision_engine.py](file:///Users/yashdaga/Desktop/dev/ForgeOs/backend/app/pipeline/decision_engine.py)
- Create a `DecisionEngine` that inspects the current `PipelineContext` and generates structured, stage-specific `DecisionEvent` payloads dynamically (without hardcoding raw static templates).
- It will evaluate context fields such as:
  - Framework type (`fastapi`, etc.)
  - Test outcomes (`tests_passed`, `tests_failed`, `failures`)
  - Health scores and recommendations
  - AI repair patch status and confidence levels
  - BI repository metrics (stars, forks)

#### [MODIFY] [orchestrator.py](file:///Users/yashdaga/Desktop/dev/ForgeOs/backend/app/pipeline/orchestrator.py)
- Import `DecisionEngine` and `DecisionEvent`.
- At the end of every executed stage in the stage loop inside `_execute_pipeline()`, call `DecisionEngine.generate_decision(ctx, stage)` and publish the resulting `DecisionEvent` via the `event_manager`.

---

### Frontend Components

#### [MODIFY] [events.ts](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/types/events.ts)
- Add `"decision_event"` to the `EventType` type union.
- Define `DecisionEvent` typescript interface matching the backend schema.
- Add `DecisionEvent` to `ForgeOSEvent` type union.

#### [MODIFY] [pipeline.ts](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/types/pipeline.ts)
- Add `decisions: DecisionEvent[]` to `PipelineState` interface and `INITIAL_PIPELINE_STATE`.

#### [MODIFY] [usePipelineState.ts](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/hooks/usePipelineState.ts)
- Add `case "decision_event"` handler to `reduceEvent()` that appends the event to the `decisions` array.

#### [NEW] [DecisionLog.tsx](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/components/DecisionLog/DecisionLog.tsx)
- Implement `DecisionLog` component holding:
  - `DecisionTimeline`: The vertical container for decision logs.
  - `DecisionCard`: Neo-Brutalist card for each decision:
    - Display Mascot emoji, Agent label, Stage, Timestamp, Reason, Evidence, Decision/Action taken, Expected Outcome, Confidence, and Status.
    - Render speech bubbles for comments.
    - Apply stage color-coding using Neo-Brutalist theme variables.
  - `DecisionDetails`: Collapsible detail toggle containing full evidence and expected outcome tables.
- Pinned Mode:
  - Keep the newest decision highlighted/pinned, while previous decisions animate and collapse into summaries.

#### [NEW] [ReasoningTrace.tsx](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/components/ReasoningTrace/ReasoningTrace.tsx)
- Render the separate "why" stream from `reasoning_update` events.
- Animate each stable reasoning step through running, completed, blocked, and failed states.
- Show the agent, phase, evidence, confidence, and the exact rationale for repair actions.

#### [MODIFY] [MissionControl.tsx](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/components/MissionControl/MissionControl.tsx)
- Import and mount `DecisionLog` into the grid layout (`gridColumn: "1 / 4"`).

---

## Verification Plan

### Automated Tests
- We will run the backend dev servers and execute pipeline session runs, ensuring the event stream prints `"event": "decision_event"` payloads.

### Manual Verification
- Trigger repository analysis via the Frontend URL input.
- Observe each pipeline stage complete and verify:
  1. A new Decision Card slides/animates into view.
  2. The latest decision remains pinned open.
  3. Previous decisions collapse but can be expanded manually.
  4. The information displayed matches the actual pipeline details (FastAPI detected, failed tests identified, AI patch applied, health score calculated).
  5. The Reasoning Trace visibly differs from the Timeline: it explains why each action happened while the Timeline records what happened.
  6. The Decision Log renders speech-bubble style discussions with Neo-Brutalist borders and offset shadows.
