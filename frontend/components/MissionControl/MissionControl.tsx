"use client";

/**
 * MissionControl — Main dashboard layout
 *
 * Assembles all panels into the ForgeOS Mission Control grid.
 * All state is derived from the SSE event stream.
 */

import { useCallback, useState } from "react";
import { usePipelineState } from "@/hooks/usePipelineState";
import { useEventStream } from "@/hooks/useEventStream";
import { analyzeRepository } from "@/services/api";
import { RepositoryInput } from "@/components/RepositoryInput/RepositoryInput";
import { AgentPanel } from "@/components/AgentCards/AgentPanel";
import { Timeline } from "@/components/Timeline/Timeline";
import { LiveTerminal } from "@/components/LiveTerminal/LiveTerminal";
import { DiffViewer } from "@/components/DiffViewer/DiffViewer";
import { HealthDashboard } from "@/components/HealthDashboard/HealthDashboard";
import { BusinessDashboard } from "@/components/BusinessDashboard/BusinessDashboard";
import { RepositoryOverview } from "@/components/RepositoryOverview/RepositoryOverview";
import { RepositoryTree } from "@/components/RepositoryTree/RepositoryTree";
import { RepositoryGraph } from "@/components/RepositoryGraph/RepositoryGraph";
import { PlannerPanel } from "@/components/PlannerPanel/PlannerPanel";
import { DecisionLog } from "@/components/DecisionLog/DecisionLog";
import { ReasoningTrace } from "@/components/ReasoningTrace/ReasoningTrace";

export function MissionControl() {
  const { state, handleEvent, reset, setConnected } = usePipelineState();
  const [launchError, setLaunchError] = useState<string | null>(null);

  const { connect } = useEventStream({
    onEvent: handleEvent,
    onConnect: () => setConnected(true),
    onDisconnect: () => setConnected(false),
  });

  const handleAnalyze = useCallback(
    async (url: string) => {
      reset();
      setLaunchError(null);
      try {
        const response = await analyzeRepository(url);
        connect(response.session_id);
      } catch (e) {
        console.error("Failed to start analysis:", e);
        setLaunchError(
          e instanceof Error && e.message !== "Failed to fetch"
            ? `Could not launch analysis: ${e.message}`
            : "ForgeOS could not reach the backend. Confirm it is running, then retry."
        );
      }
    },
    [reset, connect]
  );

  const progress =
    state.totalStages > 0
      ? Math.round((state.stageIndex / state.totalStages) * 100)
      : 0;

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "var(--bg-primary)",
        fontFamily: "var(--font-sans)",
      }}
    >
      {/* Header */}
      <header
        className="mission-header"
        style={{
          borderBottom: "var(--border-thick)",
          background: "var(--bg-card)",
          padding: "0 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          height: "64px",
          boxShadow: "0 2px 0 #0a0a0a",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div
            style={{
              width: "36px",
              height: "36px",
              background: "#0a0a0a",
              borderRadius: "var(--radius-sm)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "18px",
            }}
          >
            🔨
          </div>
          <div>
            <h1
              style={{
                fontSize: "20px",
                fontWeight: 900,
                letterSpacing: "-0.02em",
                margin: 0,
                lineHeight: 1.2,
              }}
            >
              ForgeOS
            </h1>
            <p
              style={{
                fontSize: "11px",
                color: "var(--fg-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                margin: 0,
                fontWeight: 600,
              }}
            >
              Mission Control
            </p>
          </div>
        </div>

        {/* Pipeline progress indicator */}
        <div className="mission-header__status" style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          {state.isRunning && (
            <div
              className="mission-header__progress"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "10px",
                animation: "fadeIn 300ms both",
              }}
            >
              <span
                className="mission-header__stage"
                style={{
                  fontSize: "12px",
                  fontWeight: 600,
                  color: "var(--fg-secondary)",
                }}
              >
                {state.currentStage}
              </span>
              <div
                className="mission-header__progress-bar"
                style={{
                  width: "120px",
                  height: "8px",
                  background: "#e5e5e5",
                  borderRadius: "4px",
                  border: "1.5px solid #0a0a0a",
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: `${progress}%`,
                    height: "100%",
                    background: "var(--accent-blue)",
                    borderRadius: "4px",
                    transition: "width 300ms ease",
                  }}
                />
              </div>
              <span
                style={{
                  fontSize: "12px",
                  fontWeight: 700,
                  color: "var(--accent-blue)",
                  fontFamily: "var(--font-mono)",
                }}
              >
                {progress}%
              </span>
            </div>
          )}
          {state.isCompleted && (
            <span
              className={`status-badge ${state.completion?.success ? "status-completed" : state.completion?.requiresReview ? "status-review" : "status-failed"}`}
              style={{ animation: "scaleIn 300ms both" }}
            >
              {state.completion?.success ? "✓ Complete" : "! Review required"}
            </span>
          )}
          <div
            style={{
              width: "10px",
              height: "10px",
              borderRadius: "50%",
              background: state.isConnected
                ? "var(--accent-green)"
                : state.isRunning
                ? "var(--accent-amber)"
                : "#ccc",
              border: "1.5px solid #0a0a0a",
              transition: "background var(--transition-fast)",
            }}
          />
        </div>
      </header>

      {/* Input bar */}
      <div className="mission-input-bar" style={{ padding: "16px 24px 0" }}>
        <RepositoryInput
          onAnalyze={handleAnalyze}
          isRunning={state.isRunning}
        />
      </div>
      {launchError && (
        <div className="mission-launch-error" role="alert" aria-live="polite">
          <span aria-hidden="true">⚠️</span>
          <span>{launchError}</span>
        </div>
      )}

      {/* Dashboard Grid */}
      <div className="mission-grid" style={{ padding: "16px 24px" }}>
        {/* Row 1: Overview + Agents */}
        <div style={{ gridColumn: "1 / 2" }}>
          <RepositoryOverview
            repository={state.repository}
            architecture={state.architecture}
            metrics={state.metrics}
            health={state.health}
          />
        </div>

        <div style={{ gridColumn: "2 / 4" }}>
          <AgentPanel agents={state.agents} activities={state.aiActivities} />
        </div>

        {/* Row 2: Terminal + Timeline */}
        <div style={{ gridColumn: "1 / 3" }}>
          <LiveTerminal lines={state.terminalLines} />
        </div>

        <div style={{ gridColumn: "3 / 4" }}>
          <Timeline
            currentStage={state.currentStage}
            stageIndex={state.stageIndex}
            totalStages={state.totalStages}
            isCompleted={state.isCompleted}
          />
        </div>

        {/* Row 3: Graph + Planner + File Tree */}
        <div style={{ gridColumn: "1 / 2" }}>
          <RepositoryGraph
            architecture={state.architecture}
            impact={state.impact}
          />
        </div>

        <div style={{ gridColumn: "2 / 3" }}>
          <PlannerPanel planner={state.planner} />
        </div>

        <div style={{ gridColumn: "3 / 4" }}>
          <RepositoryTree files={state.repository.files} />
        </div>

        {/* Row 4: Diff */}
        <div style={{ gridColumn: "1 / 3" }}>
          <DiffViewer diffs={state.diffs} />
        </div>

        <div style={{ gridColumn: "3 / 4" }}>
          <HealthDashboard health={state.health} />
        </div>

        {/* Row 5: Reasoning is the why behind the operational pipeline timeline */}
        <div style={{ gridColumn: "1 / 4" }}>
          <ReasoningTrace steps={state.reasoningSteps} />
        </div>

        {/* Row 6: Structured decision record */}
        <div style={{ gridColumn: "1 / 4" }}>
          <DecisionLog decisions={state.decisions} />
        </div>

        {/* Row 7: Business */}
        <div style={{ gridColumn: "1 / 4" }}>
          <BusinessDashboard business={state.business} />
        </div>
      </div>

      {/* Completion Banner */}
      {state.completion && (
        <div
          className="mission-completion"
          style={{
            margin: "0 24px 24px",
            padding: "20px 24px",
            background: state.completion.success
              ? "#dcfce7"
              : state.completion.requiresReview
              ? "#fef3c7"
              : "#fee2e2",
            border: "var(--border-thick)",
            borderRadius: "var(--radius-md)",
            boxShadow: "var(--shadow-offset)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            animation: "scaleIn 400ms both",
          }}
        >
          <div>
            <h3
              style={{
                fontSize: "16px",
                fontWeight: 800,
                margin: "0 0 4px",
              }}
            >
              {state.completion.success
                ? "🎉 Mission Complete"
                : state.completion.requiresReview
                ? "🔎 Mission Requires Review"
                : "⚠️ Pipeline Failed"}
            </h3>
            <p
              style={{
                fontSize: "13px",
                color: "var(--fg-secondary)",
                margin: 0,
              }}
            >
              {state.completion.summary}
            </p>
          </div>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontWeight: 700,
              fontSize: "14px",
            }}
          >
            {state.completion.durationSeconds.toFixed(1)}s
          </span>
        </div>
      )}
    </div>
  );
}
