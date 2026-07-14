"use client";

import type { PlannerTask } from "@/types/events";

interface PlannerPanelProps {
  planner: {
    phase: string;
    tasks: PlannerTask[];
    currentTask: string;
    message: string;
  };
}

const TYPE_COLORS: Record<string, string> = {
  deterministic: "var(--accent-green)",
  ai_repair: "var(--accent-purple)",
  test_failure: "var(--accent-amber)",
};

export function PlannerPanel({ planner }: PlannerPanelProps) {
  const hasPlan = planner.tasks.length > 0 || planner.message !== "";

  return (
    <div className="card" style={{ height: "100%" }}>
      <div className="card-header">
        <span>🧭</span>
        Repair Plan
        {hasPlan && (
          <span
            style={{
              marginLeft: "auto",
              fontSize: "11px",
              color: "var(--fg-muted)",
              fontFamily: "var(--font-mono)",
              textTransform: "none",
            }}
          >
            {planner.tasks.length} tasks
          </span>
        )}
      </div>
      <div className="card-body">
        {!hasPlan ? (
          <div
            style={{
              padding: "20px",
              textAlign: "center",
              color: "var(--fg-muted)",
              fontSize: "13px",
            }}
          >
            Planner awaiting pytest evidence...
          </div>
        ) : (
          <>
            <div
              style={{
                padding: "10px",
                background: "#f8fafc",
                border: "1.5px solid #e2e8f0",
                borderRadius: "var(--radius-sm)",
                marginBottom: "12px",
              }}
            >
              <div
                style={{
                  fontSize: "11px",
                  fontWeight: 800,
                  color: "var(--fg-muted)",
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                  marginBottom: "4px",
                }}
              >
                {planner.phase || "Planning"}
              </div>
              <div style={{ fontSize: "12px", lineHeight: 1.5 }}>
                {planner.message || planner.currentTask}
              </div>
            </div>

            <div style={{ display: "grid", gap: "8px" }}>
              {planner.tasks.map((task, index) => (
                <div
                  key={task.id}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "24px 1fr",
                    gap: "8px",
                    padding: "10px",
                    border: "1.5px solid #e5e5e5",
                    borderRadius: "var(--radius-sm)",
                    animation: `fadeIn 150ms ${index * 60}ms both`,
                  }}
                >
                  <div
                    style={{
                      width: "22px",
                      height: "22px",
                      borderRadius: "50%",
                      border: "1.5px solid #0a0a0a",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: "11px",
                      fontWeight: 900,
                      background: TYPE_COLORS[task.type] || "var(--accent-blue)",
                      color: "#fff",
                    }}
                  >
                    {task.id}
                  </div>
                  <div>
                    <div style={{ fontSize: "12px", fontWeight: 800 }}>
                      {task.title}
                    </div>
                    <div
                      style={{
                        display: "flex",
                        gap: "8px",
                        flexWrap: "wrap",
                        marginTop: "5px",
                        fontSize: "10px",
                        fontFamily: "var(--font-mono)",
                        color: "var(--fg-muted)",
                      }}
                    >
                      <span>{task.type}</span>
                      <span>{task.priority}</span>
                      {task.file && <span>{task.file}</span>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

