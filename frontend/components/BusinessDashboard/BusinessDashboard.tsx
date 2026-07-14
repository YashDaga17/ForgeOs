"use client";

interface BusinessDashboardProps {
  business: {
    stars: number;
    forks: number;
    contributors: number;
    openIssues: number;
    watchers: number;
    releaseCadence: string;
    dependencyHealth: string;
    communityActivity: string;
    executiveSummary: string;
    source: string;
    repositoryOwner: string;
    repositoryName: string;
    primaryLanguage: string;
    license: string;
    topics: string[];
    competitorSnapshot: {
      name: string;
      stars: number;
      forks: number;
      description: string;
    }[];
    lastUpdated: string;
    aiStatus: string;
    aiModel: string;
    aiMessage: string;
    aiProductThesis: string;
    aiEngineeringRisk: string;
    aiNextMove: string;
    aiConfidence: number;
  };
}

export function BusinessDashboard({ business }: BusinessDashboardProps) {
  const hasData = business.source !== "" || business.executiveSummary !== "";
  const isGitHub = business.source === "github";
  const aiLive = business.aiStatus === "completed";
  const aiFailed = business.aiStatus === "failed";

  const metrics = [
    { label: "Stars", value: business.stars.toLocaleString(), icon: "⭐", color: "var(--accent-amber)" },
    { label: "Forks", value: business.forks.toLocaleString(), icon: "🔱", color: "var(--accent-blue)" },
    { label: "Contributors", value: business.contributors.toLocaleString(), icon: "👥", color: "var(--accent-purple)" },
    { label: "Watchers", value: business.watchers.toLocaleString(), icon: "👀", color: "var(--accent-cyan)" },
  ];

  const details = [
    { label: "Open Issues", value: business.openIssues.toLocaleString(), icon: "📋" },
    { label: "Language", value: business.primaryLanguage, icon: "🧭" },
    { label: "License", value: business.license, icon: "📜" },
    { label: "Release Cadence", value: business.releaseCadence, icon: "📦" },
    { label: "Dependency Health", value: business.dependencyHealth, icon: "🔗" },
    { label: "Community", value: business.communityActivity, icon: "💬" },
  ];

  return (
    <div className="card" style={{ height: "100%" }}>
      <div className="card-header">
        <span>📊</span>
        Business Intelligence
        {hasData && (
          <div style={{ display: "flex", alignItems: "center", gap: "6px", marginLeft: "auto" }}>
            <span className={`status-badge ${isGitHub ? "status-completed" : "status-waiting"}`}>
              {isGitHub ? "GitHub live" : "Local signals"}
            </span>
            <span className={`status-badge ${aiLive ? "status-completed" : aiFailed ? "status-failed" : "status-waiting"}`}>
              {aiLive ? "AI brief live" : aiFailed ? "AI brief failed" : "AI brief gated"}
            </span>
          </div>
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
            Business intelligence pending...
          </div>
        ) : (
          <>
            {(business.repositoryName || business.repositoryOwner) && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: "12px",
                  marginBottom: "12px",
                }}
              >
                <div>
                  <div
                    style={{
                      fontSize: "13px",
                      fontWeight: 800,
                      fontFamily: "var(--font-mono)",
                    }}
                  >
                    {business.repositoryOwner
                      ? `${business.repositoryOwner}/${business.repositoryName}`
                      : business.repositoryName}
                  </div>
                  {business.lastUpdated && (
                    <div
                      style={{
                        fontSize: "10px",
                        color: "var(--fg-muted)",
                        marginTop: "2px",
                      }}
                    >
                      Updated {business.lastUpdated.slice(0, 10)}
                    </div>
                  )}
                </div>
                {business.topics.length > 0 && (
                  <div
                    style={{
                      display: "flex",
                      gap: "4px",
                      flexWrap: "wrap",
                      justifyContent: "flex-end",
                    }}
                  >
                    {business.topics.slice(0, 3).map((topic) => (
                      <span
                        key={topic}
                        style={{
                          padding: "2px 8px",
                          border: "1px solid #d1d5db",
                          borderRadius: "999px",
                          fontSize: "10px",
                          fontWeight: 700,
                          color: "var(--fg-secondary)",
                        }}
                      >
                        {topic}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Metric cards */}
            <div
              className="business-metrics"
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(4, 1fr)",
                gap: "10px",
                marginBottom: "16px",
              }}
            >
              {metrics.map((m) => (
                <div
                  key={m.label}
                  style={{
                    padding: "12px",
                    border: "1.5px solid #e5e5e5",
                    borderRadius: "var(--radius-sm)",
                    textAlign: "center",
                  }}
                >
                  <div style={{ fontSize: "18px", marginBottom: "4px" }}>
                    {m.icon}
                  </div>
                  <div
                    style={{
                      fontSize: "20px",
                      fontWeight: 800,
                      color: m.color,
                      fontFamily: "var(--font-mono)",
                    }}
                  >
                    {m.value}
                  </div>
                  <div
                    style={{
                      fontSize: "10px",
                      textTransform: "uppercase",
                      letterSpacing: "0.06em",
                      color: "var(--fg-muted)",
                      fontWeight: 600,
                      marginTop: "2px",
                    }}
                  >
                    {m.label}
                  </div>
                </div>
              ))}
            </div>

            {/* Detail rows */}
            <div className="business-details" style={{ marginBottom: "16px" }}>
              {details
                .filter((d) => d.value)
                .map((d, i) => (
                  <div
                    key={d.label}
                    className="business-detail-row"
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "8px 0",
                      borderBottom:
                        i <
                        details.filter((dd) => dd.value).length - 1
                          ? "1px solid #f0f0f0"
                          : "none",
                    }}
                  >
                    <span
                      className="business-detail-value"
                      style={{
                        fontSize: "12px",
                        color: "var(--fg-secondary)",
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                      }}
                    >
                      {d.icon} {d.label}
                    </span>
                    <span
                      style={{
                        fontSize: "12px",
                        fontWeight: 600,
                        color: "var(--fg-primary)",
                      }}
                    >
                      {d.value}
                    </span>
                  </div>
                ))}
            </div>

            {/* Executive summary */}
            {business.executiveSummary && (
              <div
                style={{
                  padding: "12px",
                  background: "#f8fafc",
                  border: "1.5px solid #e2e8f0",
                  borderRadius: "var(--radius-sm)",
                  fontSize: "12px",
                  lineHeight: 1.6,
                  color: "var(--fg-secondary)",
                }}
              >
                <div
                  style={{
                    fontSize: "11px",
                    fontWeight: 700,
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                    color: "var(--fg-muted)",
                    marginBottom: "6px",
                  }}
                >
                  Executive Summary
                </div>
                {business.executiveSummary}
              </div>
            )}

            <section style={{ borderTop: "2px solid #0a0a0a", paddingTop: "12px", marginTop: "14px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "8px" }}>
                <strong style={{ fontSize: "12px" }}>AI Decision Brief</strong>
                {business.aiModel && <code style={{ fontSize: "9px", color: "var(--fg-muted)" }}>{business.aiModel}</code>}
              </div>
              {aiLive ? (
                <div style={{ display: "grid", gap: "8px", marginTop: "9px" }}>
                  <BriefRow label="Product thesis" value={business.aiProductThesis} />
                  <BriefRow label="Engineering risk" value={business.aiEngineeringRisk} />
                  <BriefRow label="Next move" value={business.aiNextMove} />
                  <div style={{ fontSize: "10px", color: "var(--fg-muted)", fontFamily: "var(--font-mono)" }}>
                    Evidence confidence: {(business.aiConfidence * 100).toFixed(0)}%
                  </div>
                </div>
              ) : (
                <p style={{ margin: "7px 0 0", fontSize: "11px", lineHeight: 1.45, color: aiFailed ? "var(--accent-red)" : "var(--fg-secondary)" }}>
                  {business.aiMessage || "The deterministic GitHub and engineering summary remains available."}
                </p>
              )}
            </section>

            {business.competitorSnapshot.length > 0 && (
              <div style={{ marginTop: "14px" }}>
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
                  Competitor Snapshot
                </div>
                <div style={{ display: "grid", gap: "8px" }}>
                  {business.competitorSnapshot.slice(0, 3).map((competitor) => (
                    <div
                      key={competitor.name}
                      style={{
                        padding: "10px",
                        border: "1.5px solid #e5e5e5",
                        borderRadius: "var(--radius-sm)",
                        background: "#ffffff",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          gap: "8px",
                          marginBottom: "4px",
                        }}
                      >
                        <span
                          style={{
                            fontSize: "12px",
                            fontWeight: 800,
                            fontFamily: "var(--font-mono)",
                          }}
                        >
                          {competitor.name}
                        </span>
                        <span
                          style={{
                            fontSize: "11px",
                            color: "var(--fg-muted)",
                            fontFamily: "var(--font-mono)",
                            whiteSpace: "nowrap",
                          }}
                        >
                          ⭐ {competitor.stars.toLocaleString()} / 🔱{" "}
                          {competitor.forks.toLocaleString()}
                        </span>
                      </div>
                      {competitor.description && (
                        <div
                          style={{
                            fontSize: "11px",
                            lineHeight: 1.5,
                            color: "var(--fg-secondary)",
                          }}
                        >
                          {competitor.description}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function BriefRow({ label, value }: { label: string; value: string }) {
  if (!value) return null;
  return (
    <div style={{ fontSize: "11px", lineHeight: 1.45, color: "var(--fg-secondary)" }}>
      <strong style={{ color: "var(--fg-primary)", display: "block", fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: "2px" }}>
        {label}
      </strong>
      {value}
    </div>
  );
}
