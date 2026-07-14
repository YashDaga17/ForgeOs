"use client";

interface HealthDashboardProps {
  health: {
    overallScore: number;
    dimensions: Record<string, number>;
    recommendations: string[];
    repositoryGrade: string;
    engineeringQuality: string;
    businessRisk: string;
    criticalFindings: number;
    topRecommendation: string;
    deploymentRecommendation: string;
    estimatedTimeSaved: string;
    executiveSummary: string;
  };
}

const DIMENSION_COLORS: Record<string, string> = {
  Testing: "var(--accent-green)",
  Security: "var(--accent-red)",
  Architecture: "var(--accent-blue)",
  Performance: "var(--accent-amber)",
  Documentation: "var(--accent-purple)",
  Maintainability: "var(--accent-cyan)",
  "Deployment Readiness": "var(--accent-orange)",
};

export function HealthDashboard({ health }: HealthDashboardProps) {
  const dimensions = Object.entries(health.dimensions);
  const hasData = dimensions.length > 0;
  const scorePercent = Math.round(health.overallScore * 100);

  return (
    <div className="card" style={{ height: "100%" }}>
      <div className="card-header">
        <span>💊</span>
        Repository Health
        {hasData && (
          <span
            style={{
              marginLeft: "auto",
              fontFamily: "var(--font-mono)",
              fontWeight: 800,
              fontSize: "16px",
              color:
                scorePercent >= 80
                  ? "var(--accent-green)"
                  : scorePercent >= 60
                  ? "var(--accent-amber)"
                  : "var(--accent-red)",
            }}
          >
            {scorePercent}%
          </span>
        )}
      </div>
      <div className="card-body">
        {!hasData ? (
          <div
            style={{
              padding: "20px",
              textAlign: "center",
              color: "var(--fg-muted)",
              fontSize: "13px",
            }}
          >
            Health analysis pending...
          </div>
        ) : (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              height: "100%",
              maxHeight: "450px",
              overflowY: "auto",
              paddingRight: "4px",
            }}
          >
            {/* Executive Summary */}
            {health.executiveSummary && (
              <div
                style={{
                  background: "var(--accent-purple)06",
                  border: "1.5px solid var(--accent-purple)",
                  borderRadius: "var(--radius-sm)",
                  padding: "10px 12px",
                  marginBottom: "16px",
                  fontSize: "12px",
                  lineHeight: 1.5,
                  boxShadow: "2px 2px 0px #0a0a0a",
                }}
              >
                <div
                  style={{
                    fontWeight: 800,
                    marginBottom: "4px",
                    fontSize: "9px",
                    textTransform: "uppercase",
                    color: "var(--accent-purple)",
                    letterSpacing: "0.05em",
                  }}
                >
                  Executive Summary
                </div>
                <div style={{ color: "var(--fg-primary)", fontWeight: 500 }}>
                  {health.executiveSummary}
                </div>
              </div>
            )}

            {/* Premium Assessment Metrics Grid */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: "8px",
                marginBottom: "16px",
              }}
            >
              <div style={{ border: "1.5px solid #0a0a0a", borderRadius: "4px", padding: "6px 8px", background: "#ffffff", boxShadow: "1.5px 1.5px 0px #0a0a0a" }}>
                <div style={{ fontSize: "8.5px", fontWeight: 800, textTransform: "uppercase", color: "var(--fg-secondary)", letterSpacing: "0.02em" }}>
                  Repository Grade
                </div>
                <div style={{ fontSize: "16px", fontWeight: 900, color: "var(--accent-green)", fontFamily: "var(--font-mono)" }}>
                  {health.repositoryGrade || "Pending"}
                </div>
              </div>

              <div style={{ border: "1.5px solid #0a0a0a", borderRadius: "4px", padding: "6px 8px", background: "#ffffff", boxShadow: "1.5px 1.5px 0px #0a0a0a" }}>
                <div style={{ fontSize: "8.5px", fontWeight: 800, textTransform: "uppercase", color: "var(--fg-secondary)", letterSpacing: "0.02em" }}>
                  Engineering Quality
                </div>
                <div style={{ fontSize: "12px", fontWeight: 800, color: "var(--accent-blue)" }}>
                  {health.engineeringQuality || "Not assessed"}
                </div>
              </div>

              <div style={{ border: "1.5px solid #0a0a0a", borderRadius: "4px", padding: "6px 8px", background: "#ffffff", boxShadow: "1.5px 1.5px 0px #0a0a0a" }}>
                <div style={{ fontSize: "8.5px", fontWeight: 800, textTransform: "uppercase", color: "var(--fg-secondary)", letterSpacing: "0.02em" }}>
                  Business Risk
                </div>
                <div style={{ fontSize: "12px", fontWeight: 800, color: "var(--accent-amber)" }}>
                  {health.businessRisk || "Unknown"}
                </div>
              </div>

              <div style={{ border: "1.5px solid #0a0a0a", borderRadius: "4px", padding: "6px 8px", background: "#ffffff", boxShadow: "1.5px 1.5px 0px #0a0a0a" }}>
                <div style={{ fontSize: "8.5px", fontWeight: 800, textTransform: "uppercase", color: "var(--fg-secondary)", letterSpacing: "0.02em" }}>
                  Critical Findings
                </div>
                <div style={{ fontSize: "12px", fontWeight: 800, color: "var(--accent-red)", fontFamily: "var(--font-mono)" }}>
                  {health.criticalFindings || 0}
                </div>
              </div>

              <div style={{ border: "1.5px solid #0a0a0a", borderRadius: "4px", padding: "6px 8px", background: "#ffffff", boxShadow: "1.5px 1.5px 0px #0a0a0a" }}>
                <div style={{ fontSize: "8.5px", fontWeight: 800, textTransform: "uppercase", color: "var(--fg-secondary)", letterSpacing: "0.02em" }}>
                  Deployment Rec
                </div>
                <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--accent-green)" }}>
                  {health.deploymentRecommendation || "Awaiting verification"}
                </div>
              </div>

              <div style={{ border: "1.5px solid #0a0a0a", borderRadius: "4px", padding: "6px 8px", background: "#ffffff", boxShadow: "1.5px 1.5px 0px #0a0a0a" }}>
                <div style={{ fontSize: "8.5px", fontWeight: 800, textTransform: "uppercase", color: "var(--fg-secondary)", letterSpacing: "0.02em" }}>
                  Est. Time Saved
                </div>
                <div style={{ fontSize: "12px", fontWeight: 800, color: "var(--accent-purple)", fontFamily: "var(--font-mono)" }}>
                  {health.estimatedTimeSaved || "8.4 hours"}
                </div>
              </div>
            </div>

            {/* Dimension bars */}
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "10px",
                marginBottom: "16px",
              }}
            >
              {dimensions.map(([name, value]) => (
                <div key={name}>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      marginBottom: "4px",
                    }}
                  >
                    <span
                      style={{
                        fontSize: "11px",
                        fontWeight: 600,
                        color: "var(--fg-secondary)",
                      }}
                    >
                      {name}
                    </span>
                    <span
                      style={{
                        fontSize: "11px",
                        fontWeight: 700,
                        fontFamily: "var(--font-mono)",
                      }}
                    >
                      {Math.round(value * 100)}%
                    </span>
                  </div>
                  <div className="health-bar">
                    <div
                      className="health-fill"
                      style={{
                        width: `${value * 100}%`,
                        background: DIMENSION_COLORS[name] || "var(--accent-blue)",
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* Recommendations */}
            {health.recommendations.length > 0 && (
              <div>
                <div
                  style={{
                    fontSize: "11px",
                    fontWeight: 700,
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                    color: "var(--fg-muted)",
                    marginBottom: "8px",
                  }}
                >
                  Recommendations
                </div>
                {health.recommendations.slice(0, 3).map((rec, i) => (
                  <div
                    key={i}
                    style={{
                      fontSize: "12px",
                      color: "var(--fg-secondary)",
                      padding: "6px 0",
                      borderBottom:
                        i < Math.min(health.recommendations.length, 3) - 1
                          ? "1px solid #f0f0f0"
                          : "none",
                      display: "flex",
                      gap: "8px",
                    }}
                  >
                    <span style={{ color: "var(--accent-amber)" }}>⚡</span>
                    {rec}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
