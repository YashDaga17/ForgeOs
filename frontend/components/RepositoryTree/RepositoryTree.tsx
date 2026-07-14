"use client";

import type { FileInfo } from "@/types/events";

interface RepositoryTreeProps {
  files: FileInfo[];
}

const FILE_ICONS: Record<string, string> = {
  source: "📄",
  test: "🧪",
  config: "⚙️",
  docs: "📖",
  ci: "🔄",
};

const TYPE_COLORS: Record<string, string> = {
  source: "var(--accent-blue)",
  test: "var(--accent-green)",
  config: "var(--accent-amber)",
  docs: "var(--accent-purple)",
  ci: "var(--accent-cyan)",
};

export function RepositoryTree({ files }: RepositoryTreeProps) {
  return (
    <div className="card" style={{ height: "100%" }}>
      <div className="card-header">
        <span>🌲</span>
        File Tree
        {files.length > 0 && (
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
            {files.length} files
          </span>
        )}
      </div>
      <div
        className="card-body"
        style={{ maxHeight: "300px", overflowY: "auto", padding: "8px 16px" }}
      >
        {files.length === 0 ? (
          <div
            style={{
              padding: "20px",
              textAlign: "center",
              color: "var(--fg-muted)",
              fontSize: "13px",
            }}
          >
            File tree will populate after analysis...
          </div>
        ) : (
          files.map((file, i) => (
            <div
              key={file.path}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "6px 4px",
                borderBottom:
                  i < files.length - 1 ? "1px solid #f5f5f5" : "none",
                fontSize: "12px",
                animation: `fadeIn 100ms ${i * 30}ms both`,
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  fontFamily: "var(--font-mono)",
                  color: "var(--fg-primary)",
                  fontWeight: 500,
                }}
              >
                <span style={{ fontSize: "14px" }}>
                  {FILE_ICONS[file.type] || "📄"}
                </span>
                {file.path}
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span
                  style={{
                    fontSize: "10px",
                    color: TYPE_COLORS[file.type] || "var(--fg-muted)",
                    fontWeight: 600,
                    textTransform: "uppercase",
                    letterSpacing: "0.04em",
                  }}
                >
                  {file.type}
                </span>
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "11px",
                    color: "var(--fg-muted)",
                    minWidth: "40px",
                    textAlign: "right",
                  }}
                >
                  {file.lines}L
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
