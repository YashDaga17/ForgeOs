"use client";

import { useMemo, useState } from "react";
import type { GraphEdge, GraphNode } from "@/types/events";

interface RepositoryGraphProps {
  architecture: {
    graphNodes: GraphNode[];
    graphEdges: GraphEdge[];
    graphTruncated: boolean;
  };
  impact: {
    focus_files: string[];
    affected_files: string[];
    inbound_dependents: number;
    outbound_dependencies: number;
    risk: "low" | "medium" | "high";
    message: string;
  };
}

interface PositionedNode extends GraphNode {
  x: number;
  y: number;
}

const KIND_COLORS: Record<string, string> = {
  source: "#0ea5e9",
  test: "#16a34a",
  config: "#d97706",
  docs: "#9333ea",
  ci: "#ea580c",
};

const RISK_COLORS = {
  low: "#0284c7",
  medium: "#d97706",
  high: "#dc2626",
};

function graphLabel(value: string, limit = 20) {
  return value.length > limit ? `${value.slice(0, limit - 1)}...` : value;
}

function nodeColor(node: GraphNode) {
  return KIND_COLORS[node.kind] ?? "#475569";
}

export function RepositoryGraph({ architecture, impact }: RepositoryGraphProps) {
  const [selectedNodeId, setSelectedNodeId] = useState("");
  const graph = useMemo(() => {
    const count = architecture.graphNodes.length;
    const columns = Math.min(5, Math.max(2, Math.ceil(Math.sqrt(Math.max(count, 1)))));
    const rows = Math.max(1, Math.ceil(count / columns));
    const width = Math.max(440, columns * 176 + 32);
    const height = Math.max(150, rows * 88 + 28);
    const nodes: PositionedNode[] = architecture.graphNodes.map((node, index) => ({
      ...node,
      x: 84 + (index % columns) * 176,
      y: 48 + Math.floor(index / columns) * 88,
    }));
    const byId = new Map(nodes.map((node) => [node.id, node]));
    const edges = architecture.graphEdges.filter(
      (edge) => byId.has(edge.from) && byId.has(edge.to)
    );
    return { nodes, byId, edges, width, height };
  }, [architecture.graphEdges, architecture.graphNodes]);

  const activeSelectedNodeId = graph.byId.has(selectedNodeId)
    ? selectedNodeId
    : graph.nodes[0]?.id ?? "";
  const selectedNode = graph.byId.get(activeSelectedNodeId);
  const focusFiles = new Set(impact.focus_files);
  const affectedFiles = new Set(impact.affected_files);
  const selectedInbound = graph.edges.filter((edge) => edge.to === activeSelectedNodeId);
  const selectedOutbound = graph.edges.filter((edge) => edge.from === activeSelectedNodeId);

  return (
    <div className="card" style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div className="card-header">
        <span aria-hidden="true">[Graph]</span>
        Repository Graph
        <span
          style={{
            marginLeft: "auto",
            fontSize: "11px",
            color: "var(--fg-muted)",
            textTransform: "none",
            fontFamily: "var(--font-mono)",
          }}
        >
          {graph.nodes.length} files / {graph.edges.length} imports
        </span>
      </div>

      <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: "14px", flexGrow: 1 }}>
        {graph.nodes.length === 0 ? (
          <div
            style={{
              padding: "28px 12px",
              textAlign: "center",
              color: "var(--fg-muted)",
              fontSize: "12px",
              lineHeight: 1.5,
            }}
          >
            Source graph pending. ForgeOS only renders dependencies discovered from the selected repository.
          </div>
        ) : (
          <>
            <div
              style={{
                background: "#f8fafc",
                border: "2px solid #0a0a0a",
                borderRadius: "var(--radius-sm)",
                overflowX: "auto",
                boxShadow: "var(--shadow-offset-sm)",
              }}
            >
              <svg
                viewBox={`0 0 ${graph.width} ${graph.height}`}
                style={{ minWidth: "440px", width: "100%", height: "auto", display: "block" }}
              >
                <defs>
                  <marker
                    id="repository-graph-arrow"
                    viewBox="0 0 10 10"
                    refX="9"
                    refY="5"
                    markerWidth="6"
                    markerHeight="6"
                    orient="auto"
                  >
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569" />
                  </marker>
                </defs>

                {graph.edges.map((edge) => {
                  const from = graph.byId.get(edge.from);
                  const to = graph.byId.get(edge.to);
                  if (!from || !to) return null;
                  const active =
                    edge.from === activeSelectedNodeId ||
                    edge.to === activeSelectedNodeId ||
                    focusFiles.has(edge.from) ||
                    focusFiles.has(edge.to);
                  return (
                    <line
                      key={`${edge.from}-${edge.to}`}
                      x1={from.x + 62}
                      y1={from.y}
                      x2={to.x - 62}
                      y2={to.y}
                      stroke={active ? RISK_COLORS[impact.risk] : "#94a3b8"}
                      strokeWidth={active ? 2.5 : 1.25}
                      strokeDasharray={active ? "none" : "4 4"}
                      opacity={active ? 0.95 : 0.45}
                      markerEnd="url(#repository-graph-arrow)"
                    >
                      <title>{`${edge.from} imports ${edge.to}`}</title>
                    </line>
                  );
                })}

                {graph.nodes.map((node) => {
                  const isSelected = node.id === activeSelectedNodeId;
                  const isFocus = focusFiles.has(node.id);
                  const isAffected = affectedFiles.has(node.id);
                  const fill = isFocus
                    ? RISK_COLORS[impact.risk]
                    : isSelected
                    ? nodeColor(node)
                    : isAffected
                    ? "#e0f2fe"
                    : "#ffffff";
                  const textFill = isSelected || isFocus ? "#ffffff" : "#0f172a";
                  return (
                    <g
                      key={node.id}
                      role="button"
                      tabIndex={0}
                      aria-label={`Inspect ${node.path}`}
                      onClick={() => setSelectedNodeId(node.id)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          setSelectedNodeId(node.id);
                        }
                      }}
                      style={{ cursor: "pointer", outline: "none" }}
                    >
                      <rect
                        x={node.x - 66}
                        y={node.y - 23}
                        width="132"
                        height="46"
                        rx="5"
                        fill="#0a0a0a"
                      />
                      <rect
                        x={node.x - 68}
                        y={node.y - 25}
                        width="132"
                        height="46"
                        rx="5"
                        fill={fill}
                        stroke="#0a0a0a"
                        strokeWidth={isFocus ? 3 : 2}
                      />
                      <text x={node.x} y={node.y - 5} textAnchor="middle" fontSize="8" fontWeight="800" fill={textFill}>
                        {graphLabel(node.label)}
                      </text>
                      <text x={node.x} y={node.y + 10} textAnchor="middle" fontSize="6.5" fill={textFill}>
                        {node.kind}{node.entry_point ? " / entry" : ""}
                      </text>
                      <title>{`${node.path} (${node.lines} lines)`}</title>
                    </g>
                  );
                })}
              </svg>
            </div>

            {architecture.graphTruncated && (
              <div style={{ color: "var(--fg-muted)", fontSize: "10px", marginTop: "-6px" }}>
                Showing the highest-signal 48 source files from the repository scan.
              </div>
            )}

            <section style={{ borderTop: "2px solid #0a0a0a", paddingTop: "11px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "8px" }}>
                <div style={{ fontSize: "12px", fontWeight: 900 }}>Blast Radius Navigator</div>
                <span
                  style={{
                    color: RISK_COLORS[impact.risk],
                    fontSize: "10px",
                    fontWeight: 800,
                    fontFamily: "var(--font-mono)",
                    textTransform: "uppercase",
                  }}
                >
                  {impact.risk} risk
                </span>
              </div>
              <p style={{ margin: "5px 0 8px", fontSize: "11px", color: "var(--fg-secondary)", lineHeight: 1.45 }}>
                {impact.message || "Waiting for a test failure or repair target to resolve against this graph."}
              </p>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "8px" }}>
                <div style={{ fontSize: "11px", color: "var(--fg-secondary)" }}>
                  <strong style={{ color: "var(--fg-primary)" }}>{impact.inbound_dependents}</strong> dependents
                </div>
                <div style={{ fontSize: "11px", color: "var(--fg-secondary)" }}>
                  <strong style={{ color: "var(--fg-primary)" }}>{impact.outbound_dependencies}</strong> dependencies
                </div>
              </div>
              {(impact.focus_files.length > 0 || impact.affected_files.length > 0) && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: "5px", marginTop: "9px" }}>
                  {[...impact.focus_files, ...impact.affected_files].slice(0, 7).map((file) => (
                    <button
                      key={file}
                      type="button"
                      onClick={() => setSelectedNodeId(file)}
                      style={{
                        appearance: "none",
                        border: "1px solid #0a0a0a",
                        borderRadius: "3px",
                        background: focusFiles.has(file) ? "#fee2e2" : "#f1f5f9",
                        color: "#0f172a",
                        cursor: graph.byId.has(file) ? "pointer" : "default",
                        fontFamily: "var(--font-mono)",
                        fontSize: "9px",
                        padding: "3px 5px",
                      }}
                    >
                      {graphLabel(file, 28)}
                    </button>
                  ))}
                </div>
              )}
            </section>

            {selectedNode && (
              <section style={{ borderTop: "1px solid #cbd5e1", paddingTop: "10px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "7px" }}>
                  <span
                    style={{ width: "9px", height: "9px", background: nodeColor(selectedNode), border: "1px solid #0a0a0a" }}
                  />
                  <strong style={{ fontSize: "12px" }}>{selectedNode.label}</strong>
                  {selectedNode.entry_point && <span style={{ fontSize: "9px", color: "var(--fg-muted)" }}>entry point</span>}
                </div>
                <code style={{ display: "block", marginTop: "5px", fontSize: "10px", color: "var(--fg-secondary)", overflowWrap: "anywhere" }}>
                  {selectedNode.path}
                </code>
                <div style={{ display: "flex", gap: "16px", marginTop: "8px", fontSize: "10px", color: "var(--fg-secondary)" }}>
                  <span>{selectedNode.lines} lines</span>
                  <span>{selectedInbound.length} inbound</span>
                  <span>{selectedOutbound.length} outbound</span>
                </div>
              </section>
            )}
          </>
        )}
      </div>
    </div>
  );
}
