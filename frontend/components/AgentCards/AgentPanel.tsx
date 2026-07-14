"use client";

import type { AIActivityEvent, AgentName } from "@/types/events";
import type { AgentState } from "@/types/pipeline";
import { AGENT_CONFIG } from "@/types/pipeline";
import { Mascot } from "@/components/Mascot/Mascot";

interface AgentCardProps {
  agent: AgentState;
}

export function AgentCard({ agent }: AgentCardProps) {
  const config = AGENT_CONFIG[agent.name];
  const label = config?.label ?? agent.name ?? "Agent";
  const statusClass = agent.status.toLowerCase();

  return (
    <div className={`agent-card ${statusClass}`}>
      {/* Header row */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "8px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Mascot name={agent.name} state={agent.status} />
          <div>
            <div style={{ fontSize: "13px", fontWeight: 700 }}>
              {label}
            </div>
          </div>
        </div>
        <span className={`status-badge status-${statusClass}`}>
          {agent.status}
        </span>
      </div>

      {/* Progress bar */}
      <div className="progress-bar" style={{ marginBottom: "8px" }}>
        <div
          className={`progress-fill ${agent.status === "Completed" ? "completed" : ""}`}
          style={{ width: `${agent.progress}%` }}
        />
      </div>

      {/* Confidence */}
      {agent.confidence > 0 && (
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "4px",
          }}
        >
          <span
            style={{
              fontSize: "11px",
              color: "var(--fg-muted)",
              fontWeight: 500,
            }}
          >
            Confidence
          </span>
          <span
            style={{
              fontSize: "12px",
              fontWeight: 700,
              fontFamily: "var(--font-mono)",
              color:
                agent.confidence >= 0.9
                  ? "var(--accent-green)"
                  : agent.confidence >= 0.7
                  ? "var(--accent-amber)"
                  : "var(--accent-red)",
            }}
          >
            {(agent.confidence * 100).toFixed(0)}%
          </span>
        </div>
      )}

      {/* Speech bubble */}
      {agent.message && agent.message !== "Awaiting mission..." && (
        <div className="speech-bubble">{agent.message}</div>
      )}
    </div>
  );
}

interface AgentPanelProps {
  agents: Record<AgentName, AgentState>;
  activities?: AIActivityEvent[];
}

const ACTIVITY_COLORS: Record<AIActivityEvent["status"], string> = {
  running: "var(--accent-blue)",
  completed: "var(--accent-green)",
  blocked: "var(--accent-amber)",
  failed: "var(--accent-red)",
};

function activityTitle(capability: string) {
  return capability.replaceAll("_", " ");
}

export function AgentPanel({ agents, activities = [] }: AgentPanelProps) {
  const agentList = Object.values(agents);

  return (
    <div className="card">
      <div className="card-header">
        <span>🤖</span>
        Agent Panel
        <span
          style={{
            marginLeft: "auto",
            fontSize: "11px",
            fontWeight: 500,
            color: "var(--fg-muted)",
            textTransform: "none",
          }}
        >
          {agentList.filter((a) => a.status === "Completed").length}/
          {agentList.length} Complete
        </span>
      </div>
      <div
        className="agent-grid card-body"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "12px",
        }}
      >
        {agentList.map((agent, index) => (
          <AgentCard key={`${agent.name || "agent"}-${index}`} agent={agent} />
        ))}

        {activities.length > 0 && (
          <section
            style={{
              gridColumn: "1 / -1",
              borderTop: "2px solid #0a0a0a",
              paddingTop: "10px",
              marginTop: "2px",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "8px",
                marginBottom: "7px",
              }}
            >
              <strong style={{ fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                Model Activity
              </strong>
              <span style={{ fontSize: "10px", color: "var(--fg-muted)", fontFamily: "var(--font-mono)" }}>
                {activities.length} operation{activities.length === 1 ? "" : "s"}
              </span>
            </div>
            <div style={{ display: "grid", gap: "6px" }}>
              {activities.map((activity) => (
                <div
                  key={activity.operation_id}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "auto minmax(0, 1fr) auto",
                    alignItems: "center",
                    gap: "8px",
                    padding: "7px 0",
                    borderTop: "1px solid #e2e8f0",
                  }}
                >
                  <span
                    style={{
                      width: "8px",
                      height: "8px",
                      borderRadius: "50%",
                      background: ACTIVITY_COLORS[activity.status],
                      border: "1px solid #0a0a0a",
                    }}
                    aria-label={activity.status}
                  />
                  <div style={{ minWidth: 0 }}>
                    <div style={{ display: "flex", alignItems: "baseline", gap: "7px", flexWrap: "wrap" }}>
                      <strong style={{ fontSize: "11px", textTransform: "capitalize" }}>
                        {activityTitle(activity.capability)}
                      </strong>
                      {activity.agent && (
                        <span
                          style={{
                            fontSize: "9px",
                            fontWeight: 800,
                            color: "#0a0a0a",
                            border: "1px solid #0a0a0a",
                            padding: "1px 4px",
                            borderRadius: "3px",
                          }}
                        >
                          {activity.agent}
                        </span>
                      )}
                      <code style={{ fontSize: "9px", color: "var(--fg-muted)" }}>{activity.model}</code>
                    </div>
                    <div style={{ fontSize: "10px", color: "var(--fg-secondary)", lineHeight: 1.35, marginTop: "2px" }}>
                      {activity.message}
                    </div>
                  </div>
                  <div style={{ textAlign: "right", fontSize: "9px", color: "var(--fg-muted)", fontFamily: "var(--font-mono)" }}>
                    {activity.input_tokens || activity.output_tokens
                      ? `${activity.input_tokens}/${activity.output_tokens} tok`
                      : activity.request_id
                      ? `req ${activity.request_id.slice(-8)}`
                      : activity.status}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
