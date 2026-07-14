"use client";

/**
 * RepositoryOverview — Premium CTO Repository Intelligence Dashboard
 *
 * Replaces basic stats with a high-fidelity GitHub Insights-style dashboard.
 * Displays repository health and deterministic repository signals in a clean
 * Neo-Brutalist layout. Values come from the active SSE session.
 */

import type { FileInfo, ModuleInfo, DependencyLink } from "@/types/events";

interface RepositoryOverviewProps {
  repository: {
    name: string;
    url: string;
    language: string;
    framework: string;
    testFramework: string;
    totalFiles: number;
    totalLines: number;
    files: FileInfo[];
  };
  architecture: {
    summary: string;
    modules: ModuleInfo[];
    dependencies: DependencyLink[];
    entryPoints: string[];
  };
  metrics: {
    testsTotal: number;
    testsPassed: number;
    testsFailed: number;
    testsSkipped: number;
    testStatus: string;
    issuesFound: number;
    issuesFixed: number;
  };
  health: {
    overallScore: number;
    dimensions: Record<string, number>;
  };
}

interface MetricTile {
  label: string;
  value: string | number;
  color: string;
  icon: string;
  desc: string;
}

export function RepositoryOverview({
  repository,
  architecture,
  metrics,
  health,
}: RepositoryOverviewProps) {
  const hasRepo = repository.name !== "";
  const healthPercent = health.overallScore > 0 ? Math.round(health.overallScore * 100) : null;
  const deploymentReadiness = health.dimensions["Deployment Readiness"];
  const documentationFiles = repository.files.filter((file) => file.type === "docs").length;
  const sourceFiles = repository.files.filter((file) => file.type === "source").length;
  const testReadiness =
    metrics.testStatus === "passed" || metrics.testStatus === "failed"
      ? `${Math.round((metrics.testsPassed / Math.max(metrics.testsTotal, 1)) * 100)}%`
      : metrics.testStatus === "no_tests"
        ? "No suite"
        : metrics.testStatus === "error"
          ? "Blocked"
          : "Pending";
  const structuralSize = repository.totalLines > 10000 ? "Large" : repository.totalLines > 3000 ? "Medium" : "Small";
  const intelligenceMetrics: MetricTile[] = [
    {
      label: "Deployment Readiness",
      value: deploymentReadiness === undefined ? "Pending" : `${Math.round(deploymentReadiness * 100)}%`,
      color: "var(--accent-cyan)",
      icon: "🚀",
      desc: "Evidence-based health dimension.",
    },
    {
      label: "Test Verification",
      value: testReadiness,
      color: metrics.testStatus === "passed" ? "var(--accent-green)" : "var(--accent-orange)",
      icon: "🧪",
      desc: metrics.testStatus === "no_tests" ? "No runnable tests discovered." : "Observed pytest result.",
    },
    {
      label: "Structural Size",
      value: structuralSize,
      color: "var(--accent-orange)",
      icon: "🌀",
      desc: `${repository.totalLines.toLocaleString()} analyzed lines.`,
    },
    {
      label: "Architecture",
      value: `${architecture.modules.length} modules`,
      color: "var(--accent-purple)",
      icon: "🏗️",
      desc: `${architecture.entryPoints.length} detected entry points.`,
    },
    {
      label: "Local Dependencies",
      value: `${architecture.dependencies.length} links`,
      color: "var(--accent-green)",
      icon: "📦",
      desc: "AST-derived internal import links.",
    },
    {
      label: "Detected Framework",
      value: repository.framework || "Unknown",
      color: "var(--accent-blue)",
      icon: "⚙️",
      desc: "Detected from repository files.",
    },
    {
      label: "Documentation",
      value: `${documentationFiles} files`,
      color: "var(--accent-amber)",
      icon: "📄",
      desc: "Markdown or reStructuredText files found.",
    },
    {
      label: "Source Files",
      value: `${sourceFiles} files`,
      color: "var(--accent-pink)",
      icon: "🧰",
      desc: "Files classified as source code.",
    },
  ];

  return (
    <div className="card" style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div className="card-header">
        <span>📊</span>
        Repository Intelligence
      </div>
      <div
        className="card-body"
        style={{
          padding: "16px",
          display: "flex",
          flexDirection: "column",
          gap: "14px",
          flexGrow: 1,
        }}
      >
        {!hasRepo ? (
          <div
            style={{
              padding: "32px 16px",
              textAlign: "center",
              color: "var(--fg-muted)",
              fontSize: "13px",
              fontWeight: 500,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "8px",
              flexGrow: 1,
              justifyContent: "center",
            }}
          >
            <span>🌐</span>
            Awaiting repository context. Run analysis to compile intelligence metrics.
          </div>
        ) : (
          <>
            {/* Header info */}
            <div>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "4px" }}>
                <span
                  style={{
                    fontSize: "10px",
                    fontWeight: 800,
                    color: "var(--fg-muted)",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                  }}
                >
                  GitHub Insights
                </span>
                <span
                  style={{
                    fontSize: "9px",
                    fontWeight: 700,
                    color: "var(--accent-blue)",
                    background: "#dbeafe",
                    border: "1px solid #0a0a0a",
                    borderRadius: "4px",
                    padding: "1px 6px",
                    fontFamily: "var(--font-mono)",
                  }}
                >
                  CTO Snapshot
                </span>
              </div>
              <h3
                style={{
                  fontSize: "18px",
                  fontWeight: 900,
                  margin: "0 0 6px 0",
                  letterSpacing: "-0.02em",
                  color: "var(--fg-primary)",
                  wordBreak: "break-all",
                }}
              >
                {repository.name}
              </h3>
            </div>

            {/* Hero Tile: repository health from the latest health event */}
            <div
              style={{
                background: "var(--accent-green)10",
                border: "2px solid #0a0a0a",
                borderRadius: "var(--radius-sm)",
                padding: "12px 14px",
                boxShadow: "var(--shadow-offset-sm)",
                position: "relative",
                overflow: "hidden",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div>
                  <span
                    style={{
                      fontSize: "9px",
                      fontWeight: 800,
                      color: "var(--fg-secondary)",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                    }}
                  >
                    Repository Health
                  </span>
                  <div
                    style={{
                      fontSize: "30px",
                      fontWeight: 950,
                      color: "var(--accent-green)",
                      fontFamily: "var(--font-mono)",
                      lineHeight: 1.1,
                      margin: "4px 0",
                    }}
                  >
                    {healthPercent === null ? "Pending" : `${healthPercent}%`}
                  </div>
                  <span style={{ fontSize: "11px", color: "var(--fg-secondary)", fontWeight: 500 }}>
                    Evidence-derived health score
                  </span>
                </div>
                <div
                  style={{
                    fontSize: "36px",
                    opacity: 0.9,
                    transform: "rotate(-5deg)",
                  }}
                >
                  ❤️
                </div>
              </div>
              {/* Mini Health Bar */}
              <div
                style={{
                  height: "8px",
                  background: "#ffffff",
                  border: "1.5px solid #0a0a0a",
                  borderRadius: "4px",
                  overflow: "hidden",
                  marginTop: "10px",
                }}
              >
                <div
                  style={{
                    width: `${healthPercent ?? 0}%`,
                    height: "100%",
                    background: healthPercent !== null && healthPercent >= 70 ? "var(--accent-green)" : "var(--accent-orange)",
                  }}
                />
              </div>
            </div>

            {/* Metrics Grid (2 columns) */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: "10px",
              }}
            >
              {intelligenceMetrics.map((tile) => (
                <div
                  key={tile.label}
                  style={{
                    background: "#ffffff",
                    border: "2px solid #0a0a0a",
                    borderRadius: "var(--radius-sm)",
                    padding: "10px",
                    boxShadow: "1.5px 1.5px 0px #0a0a0a",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "space-between",
                    gap: "6px",
                    transition: "transform var(--transition-fast)",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = "translate(-1px, -1px)";
                    e.currentTarget.style.boxShadow = "2.5px 2.5px 0px #0a0a0a";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = "none";
                    e.currentTarget.style.boxShadow = "1.5px 1.5px 0px #0a0a0a";
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <span
                      style={{
                        fontSize: "9px",
                        fontWeight: 800,
                        color: "var(--fg-secondary)",
                        textTransform: "uppercase",
                        letterSpacing: "0.03em",
                      }}
                    >
                      {tile.label}
                    </span>
                    <span style={{ fontSize: "14px" }}>{tile.icon}</span>
                  </div>

                  <div>
                    <span
                      style={{
                        fontSize: "15px",
                        fontWeight: 900,
                        color: tile.color,
                        fontFamily: "var(--font-mono)",
                        display: "block",
                        lineHeight: 1,
                      }}
                    >
                      {tile.value}
                    </span>
                    <span
                      style={{
                        fontSize: "9px",
                        color: "var(--fg-muted)",
                        fontWeight: 500,
                        lineHeight: 1.2,
                        display: "block",
                        marginTop: "2px",
                      }}
                    >
                      {tile.desc}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* Architecture Details Summary Footer */}
            {architecture.summary && (
              <div
                style={{
                  fontSize: "11.5px",
                  color: "var(--fg-secondary)",
                  lineHeight: 1.5,
                  padding: "10px 12px",
                  background: "#f8fafc",
                  border: "1.5px solid #0a0a0a",
                  borderRadius: "var(--radius-sm)",
                  boxShadow: "var(--shadow-offset-sm)",
                  marginTop: "2px",
                }}
              >
                <div style={{ fontWeight: 800, marginBottom: "4px", color: "var(--fg-primary)", fontSize: "10px", textTransform: "uppercase" }}>
                  🏗️ Structure Analysis Summary
                </div>
                {architecture.summary}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
