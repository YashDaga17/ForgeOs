"use client";

const PIPELINE_STAGES = [
  { name: "Clone Repository", icon: "📥" },
  { name: "Analyze Repository", icon: "🔍" },
  { name: "Detect Framework & Tests", icon: "🧪" },
  { name: "Run Tests", icon: "▶️" },
  { name: "Classify Failures", icon: "🏷️" },
  { name: "Try Deterministic Fixes", icon: "🔧" },
  { name: "AI Repair", icon: "🤖" },
  { name: "Apply Patch", icon: "📝" },
  { name: "Re-run Tests", icon: "🔄" },
  { name: "Mutation Check", icon: "🧬" },
  { name: "Generate Regression Test", icon: "🛡️" },
  { name: "Calculate Repository Health", icon: "💊" },
  { name: "Publish Business Intelligence", icon: "📊" },
  { name: "Stream Final Results", icon: "📡" },
];

interface TimelineProps {
  currentStage: string;
  stageIndex: number;
  totalStages: number;
  isCompleted: boolean;
}

export function Timeline({
  currentStage,
  stageIndex,
  totalStages,
  isCompleted,
}: TimelineProps) {
  return (
    <div className="card" style={{ height: "100%" }}>
      <div className="card-header">
        <span>📋</span>
        Pipeline Timeline
        <span
          style={{
            marginLeft: "auto",
            fontSize: "11px",
            fontWeight: 500,
            color: "var(--fg-muted)",
            textTransform: "none",
            fontFamily: "var(--font-mono)",
          }}
        >
          {isCompleted ? totalStages : stageIndex}/{totalStages}
        </span>
      </div>
      <div
        className="card-body"
        style={{ maxHeight: "360px", overflowY: "auto", padding: "12px 16px" }}
      >
        {PIPELINE_STAGES.map((stage, idx) => {
          const isActive = stage.name === currentStage;
          const isDone = isCompleted || idx < stageIndex;
          const isFuture = !isDone && !isActive;

          return (
            <div
              key={stage.name}
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: "10px",
                padding: "8px 0",
                opacity: isFuture ? 0.4 : 1,
                transition: "opacity var(--transition-base)",
              }}
            >
              {/* Dot and line */}
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  minWidth: "20px",
                }}
              >
                <div
                  style={{
                    width: "14px",
                    height: "14px",
                    borderRadius: "50%",
                    border: "2px solid",
                    borderColor: isDone
                      ? "var(--accent-green)"
                      : isActive
                      ? "var(--accent-blue)"
                      : "#d1d5db",
                    background: isDone
                      ? "var(--accent-green)"
                      : isActive
                      ? "var(--accent-blue)"
                      : "transparent",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "8px",
                    color: "#fff",
                    transition: "all var(--transition-base)",
                    flexShrink: 0,
                  }}
                >
                  {isDone && "✓"}
                </div>
                {idx < PIPELINE_STAGES.length - 1 && (
                  <div
                    style={{
                      width: "2px",
                      height: "24px",
                      background: isDone ? "var(--accent-green)" : "#e5e5e5",
                      transition: "background var(--transition-base)",
                    }}
                  />
                )}
              </div>

              {/* Label */}
              <div style={{ paddingTop: "0px" }}>
                <div
                  style={{
                    fontSize: "12px",
                    fontWeight: isActive ? 700 : 500,
                    color: isActive
                      ? "var(--accent-blue)"
                      : isDone
                      ? "var(--fg-primary)"
                      : "var(--fg-muted)",
                    transition: "color var(--transition-base)",
                  }}
                >
                  <span style={{ marginRight: "6px" }}>{stage.icon}</span>
                  {stage.name}
                </div>
                {isActive && (
                  <div
                    style={{
                      fontSize: "11px",
                      color: "var(--accent-blue)",
                      marginTop: "2px",
                      fontWeight: 500,
                      animation: "fadeIn 200ms both",
                    }}
                  >
                    In progress...
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
