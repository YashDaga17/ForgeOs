"use client";

import { useState } from "react";
import type { DiffUpdateEvent } from "@/types/events";

interface DiffViewerProps {
  diffs: DiffUpdateEvent[];
}

export function DiffViewer({ diffs }: DiffViewerProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const currentDiff = diffs[selectedIndex];

  return (
    <div className="card" style={{ height: "100%" }}>
      <div className="card-header">
        <span>📝</span>
        Code Changes
        {diffs.length > 0 && (
          <span
            style={{
              marginLeft: "auto",
              display: "flex",
              gap: "8px",
              textTransform: "none",
            }}
          >
            {diffs.map((d, i) => (
              <button
                key={i}
                onClick={() => setSelectedIndex(i)}
                style={{
                  padding: "2px 10px",
                  background:
                    i === selectedIndex ? "#0a0a0a" : "transparent",
                  color: i === selectedIndex ? "#fff" : "var(--fg-secondary)",
                  border: "1.5px solid #0a0a0a",
                  borderRadius: "4px",
                  fontSize: "11px",
                  fontWeight: 600,
                  cursor: "pointer",
                  fontFamily: "var(--font-mono)",
                  transition: "all var(--transition-fast)",
                }}
              >
                {d.file_path.split("/").pop()}
              </button>
            ))}
          </span>
        )}
      </div>
      <div className="card-body" style={{ padding: 0 }}>
        {diffs.length === 0 ? (
          <div
            style={{
              padding: "40px",
              textAlign: "center",
              color: "var(--fg-muted)",
              fontSize: "13px",
            }}
          >
            No code changes yet — diffs will appear here when patches are applied.
          </div>
        ) : currentDiff ? (
          <div>
            {/* Diff header info */}
            <div
              style={{
                padding: "12px 16px",
                borderBottom: "1px solid #e5e5e5",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <div>
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "13px",
                    fontWeight: 600,
                  }}
                >
                  {currentDiff.file_path}
                </span>
                <p
                  style={{
                    margin: "4px 0 0",
                    fontSize: "12px",
                    color: "var(--fg-secondary)",
                  }}
                >
                  {currentDiff.explanation}
                </p>
              </div>
              <div
                style={{
                  display: "flex",
                  gap: "8px",
                  alignItems: "center",
                }}
              >
                <span
                  className={`status-badge ${
                    currentDiff.risk === "low"
                      ? "status-completed"
                      : currentDiff.risk === "medium"
                      ? "status-waiting"
                      : "status-failed"
                  }`}
                >
                  {currentDiff.risk} risk
                </span>
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "12px",
                    fontWeight: 700,
                    color: "var(--accent-green)",
                  }}
                >
                  {(currentDiff.confidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>

            {/* Diff content */}
            <div
              style={{
                maxHeight: "280px",
                overflowY: "auto",
                background: "#fafafa",
              }}
            >
              {currentDiff.diff.split("\n").map((line, i) => {
                let className = "diff-line";
                if (line.startsWith("+") && !line.startsWith("+++"))
                  className += " diff-add";
                else if (line.startsWith("-") && !line.startsWith("---"))
                  className += " diff-remove";
                else if (line.startsWith("@@") || line.startsWith("---") || line.startsWith("+++"))
                  className += " diff-header";

                return (
                  <div key={i} className={className}>
                    {line}
                  </div>
                );
              })}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
