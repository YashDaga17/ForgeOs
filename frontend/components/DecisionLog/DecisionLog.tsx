"use client";

/**
 * DecisionLog — Real-time engineering decision reasoning log
 *
 * Streams and records decisions made by specialized agents across stages.
 * Pins the latest decision expanded at the top, and displays previous
 * decisions in a collapsible list below.
 */

import { useState } from "react";
import type { DecisionEvent } from "@/types/events";
import { AGENT_CONFIG } from "@/types/pipeline";
import { Mascot } from "@/components/Mascot/Mascot";

interface DecisionLogProps {
  decisions: DecisionEvent[];
}

export function DecisionLog({ decisions }: DecisionLogProps) {
  const [expandedIds, setExpandedIds] = useState<Record<string, boolean>>({});

  if (decisions.length === 0) {
    return (
      <div className="card" style={{ height: "100%" }}>
        <div className="card-header">
          <span>🧠</span>
          Decision Log
        </div>
        <div
          className="card-body"
          style={{
            padding: "24px",
            textAlign: "center",
            color: "var(--fg-muted)",
            fontSize: "14px",
            fontWeight: 500,
          }}
        >
          Awaiting pipeline decisions...
        </div>
      </div>
    );
  }

  // Newest decision is the last one in the list (or we sort by timestamp)
  const sortedDecisions = [...decisions].sort(
    (a, b) =>
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime() ||
      decisionId(a).localeCompare(decisionId(b))
  );

  const latestDecision = sortedDecisions[0];
  const previousDecisions = sortedDecisions.slice(1);

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  return (
    <div className="card" style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div className="card-header">
        <span>🧠</span>
        Decision Log
        <span
          style={{
            marginLeft: "auto",
            fontSize: "11px",
            fontWeight: 600,
            color: "var(--accent-blue)",
            background: "#dbeafe",
            border: "1.5px solid #0a0a0a",
            padding: "2px 8px",
            borderRadius: "12px",
            textTransform: "none",
            fontFamily: "var(--font-mono)",
          }}
        >
          {decisions.length} Decisions Logged
        </span>
      </div>

      <div
        className="card-body"
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "16px",
          maxHeight: "550px",
          overflowY: "auto",
          padding: "16px",
          background: "var(--bg-elevated)",
        }}
      >
        {/* Pinned Latest Decision */}
        <div style={{ animation: "fadeIn var(--transition-spring) both" }}>
          <div
            style={{
              fontSize: "10px",
              fontWeight: 800,
              color: "var(--accent-red)",
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              marginBottom: "6px",
              display: "flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            📌 Pinned (Latest Decision)
          </div>
          <DecisionCard
            decision={latestDecision}
            isPinned={true}
          />
        </div>

        {/* Collapsible Previous Decisions */}
        {previousDecisions.length > 0 && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "12px",
              marginTop: "8px",
              borderTop: "2px dashed #0a0a0a",
              paddingTop: "16px",
            }}
          >
            <div
              style={{
                fontSize: "11px",
                fontWeight: 800,
                color: "var(--fg-secondary)",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                marginBottom: "4px",
              }}
            >
              Previous Reasoning History
            </div>
            {previousDecisions.map((decision) => {
              const id = decisionId(decision);
              const isExpanded = !!expandedIds[id];
              return (
                <div
                  key={id}
                  style={{
                    animation: "fadeIn var(--transition-base) both",
                  }}
                >
                  <DecisionCard
                    decision={decision}
                    isPinned={false}
                    isExpanded={isExpanded}
                    onToggle={() => toggleExpand(id)}
                  />
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function decisionId(decision: DecisionEvent): string {
  return [
    decision.timestamp,
    decision.stage,
    decision.agent,
    decision.status,
    decision.action_taken,
    decision.reason,
  ].join("|");
}

// Sub-component for individual Decision Card
interface DecisionCardProps {
  decision: DecisionEvent;
  isPinned: boolean;
  isExpanded?: boolean;
  onToggle?: () => void;
}

function DecisionCard({
  decision,
  isPinned,
  isExpanded = true,
  onToggle,
}: DecisionCardProps) {
  const config = AGENT_CONFIG[decision.agent] || { emoji: "🤖", label: decision.agent };

  // Custom stage colors for styling borders & tags
  const getStageColor = (agent: string) => {
    switch (agent) {
      case "Supervisor":
        return "var(--accent-purple)";
      case "Repository Analyst":
        return "var(--accent-blue)";
      case "Planner":
        return "var(--accent-amber)";
      case "Repair":
        return "var(--accent-orange)";
      case "QA":
        return "var(--accent-green)";
      case "Security":
        return "var(--accent-cyan)";
      case "Performance":
        return "var(--accent-pink)";
      case "Business":
        return "var(--accent-pink)";
      default:
        return "var(--fg-primary)";
    }
  };

  const stageColor = getStageColor(decision.agent);
  const formattedTime = new Date(decision.timestamp).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  return (
    <div
      style={{
        background: "var(--bg-card)",
        border: isPinned ? "3px solid #0a0a0a" : "2px solid #0a0a0a",
        borderRadius: "var(--radius-md)",
        boxShadow: isPinned ? "var(--shadow-offset)" : "var(--shadow-offset-sm)",
        transition: "all var(--transition-fast)",
        overflow: "hidden",
      }}
    >
      {/* Top Card Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "10px 14px",
          background: isPinned ? `${stageColor}20` : "transparent",
          borderBottom: isExpanded ? "2px solid #0a0a0a" : "none",
          cursor: !isPinned ? "pointer" : "default",
        }}
        onClick={!isPinned ? onToggle : undefined}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{ width: "32px", height: "32px", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Mascot name={decision.agent} state={decision.status} />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span style={{ fontSize: "13px", fontWeight: 800 }}>{config.label}</span>
              <span
                style={{
                  fontSize: "9px",
                  fontWeight: 700,
                  color: "#ffffff",
                  background: stageColor,
                  border: "1px solid #0a0a0a",
                  padding: "1px 6px",
                  borderRadius: "4px",
                  fontFamily: "var(--font-mono)",
                }}
              >
                {decision.stage}
              </span>
            </div>
            {!isExpanded && (
              <div
                style={{
                  fontSize: "11px",
                  color: "var(--fg-secondary)",
                  marginTop: "2px",
                  fontWeight: 500,
                  maxWidth: "350px",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {decision.action_taken}
              </div>
            )}
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "11px",
              fontWeight: 600,
              color: "var(--fg-muted)",
            }}
          >
            {formattedTime}
          </span>
          {!isPinned && (
            <button
              style={{
                background: "transparent",
                border: "none",
                fontSize: "14px",
                fontWeight: 800,
                cursor: "pointer",
                padding: "2px 6px",
                transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)",
                transition: "transform var(--transition-fast)",
              }}
            >
              ▼
            </button>
          )}
        </div>
      </div>

      {/* Expanded Card Body */}
      {isExpanded && (
        <div style={{ padding: "14px", display: "flex", flexDirection: "column", gap: "12px" }}>
          {/* Discussion Reasoning Bubble */}
          <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
            <span
              style={{
                fontSize: "11px",
                fontWeight: 700,
                color: "var(--fg-secondary)",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              Reasoning Description
            </span>
            <div
              style={{
                position: "relative",
                background: `${stageColor}08`,
                border: `1.5px solid ${stageColor}`,
                borderRadius: "var(--radius-sm)",
                padding: "10px 12px",
                fontSize: "12.5px",
                lineHeight: 1.5,
                color: "var(--fg-primary)",
                fontWeight: 500,
              }}
            >
              {decision.reason}
            </div>
          </div>

          {/* Details Section */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            {/* Action Taken */}
            <div
              style={{
                background: "#fafafa",
                border: "1.5px solid #0a0a0a",
                borderRadius: "var(--radius-sm)",
                padding: "10px",
                boxShadow: "1.5px 1.5px 0px #0a0a0a",
              }}
            >
              <div
                style={{
                  fontSize: "10px",
                  fontWeight: 800,
                  color: "var(--fg-secondary)",
                  textTransform: "uppercase",
                  marginBottom: "4px",
                }}
              >
                Decision / Action Taken
              </div>
              <div style={{ fontSize: "12px", fontWeight: 700, color: "var(--accent-blue)" }}>
                {decision.action_taken}
              </div>
            </div>

            {/* Expected Outcome */}
            {decision.expected_outcome && (
              <div
                style={{
                  background: "#fafafa",
                  border: "1.5px solid #0a0a0a",
                  borderRadius: "var(--radius-sm)",
                  padding: "10px",
                  boxShadow: "1.5px 1.5px 0px #0a0a0a",
                }}
              >
                <div
                  style={{
                    fontSize: "10px",
                    fontWeight: 800,
                    color: "var(--fg-secondary)",
                    textTransform: "uppercase",
                    marginBottom: "4px",
                  }}
                >
                  Expected Impact / Outcome
                </div>
                <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--fg-primary)" }}>
                  {decision.expected_outcome}
                </div>
              </div>
            )}
          </div>

          {/* Evidence and Confidence */}
          <div
            style={{
              background: "#ffffff",
              border: "1.5px solid #e5e5e5",
              borderRadius: "var(--radius-sm)",
              padding: "10px 12px",
              display: "flex",
              flexDirection: "column",
              gap: "8px",
            }}
          >
            <div>
              <span
                style={{
                  fontSize: "10px",
                  fontWeight: 800,
                  color: "var(--fg-secondary)",
                  textTransform: "uppercase",
                  display: "block",
                  marginBottom: "2px",
                }}
              >
                Evidence
              </span>
              <code
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "11px",
                  color: "var(--fg-primary)",
                  background: "#f1f5f9",
                  padding: "2px 6px",
                  borderRadius: "4px",
                  display: "inline-block",
                  wordBreak: "break-word",
                }}
              >
                {decision.evidence}
              </code>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                borderTop: "1px solid #f1f5f9",
                paddingTop: "8px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ fontSize: "11px", fontWeight: 600, color: "var(--fg-secondary)" }}>
                  Confidence
                </span>
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "12px",
                    fontWeight: 800,
                    color:
                      decision.confidence >= 0.9
                        ? "var(--accent-green)"
                        : decision.confidence >= 0.7
                        ? "var(--accent-amber)"
                        : "var(--accent-red)",
                  }}
                >
                  {(decision.confidence * 100).toFixed(0)}%
                </span>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <span style={{ fontSize: "11px", fontWeight: 600, color: "var(--fg-secondary)" }}>
                  Status:
                </span>
                <span
                  style={{
                    fontSize: "9px",
                    fontWeight: 800,
                    textTransform: "uppercase",
                    padding: "2px 8px",
                    borderRadius: "12px",
                    border: "1px solid #0a0a0a",
                    background:
                      decision.status.toLowerCase() === "completed"
                        ? "#dcfce7"
                        : decision.status.toLowerCase() === "failed"
                        ? "#fee2e2"
                        : "#fef3c7",
                    color:
                      decision.status.toLowerCase() === "completed"
                        ? "var(--accent-green)"
                        : decision.status.toLowerCase() === "failed"
                        ? "var(--accent-red)"
                        : "var(--accent-amber)",
                  }}
                >
                  {decision.status}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
