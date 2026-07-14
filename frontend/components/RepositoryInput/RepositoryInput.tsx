"use client";

import { useState } from "react";

interface RepositoryInputProps {
  onAnalyze: (url: string) => void;
  isRunning: boolean;
}

export function RepositoryInput({ onAnalyze, isRunning }: RepositoryInputProps) {
  const [url, setUrl] = useState("https://github.com/example/fastapi-demo");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim() && !isRunning) {
      onAnalyze(url.trim());
    }
  };

  return (
    <form
      className="repository-input"
      onSubmit={handleSubmit}
      style={{
        display: "flex",
        gap: "12px",
        alignItems: "stretch",
      }}
    >
      <div
        style={{
          flex: 1,
          border: "var(--border-thick)",
          borderRadius: "var(--radius-md)",
          background: "var(--bg-card)",
          boxShadow: "var(--shadow-offset-sm)",
          display: "flex",
          alignItems: "center",
          padding: "0 16px",
          transition: "box-shadow var(--transition-fast)",
        }}
      >
        <span style={{ fontSize: "18px", marginRight: "10px" }}>📦</span>
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Enter repository URL..."
          disabled={isRunning}
          style={{
            flex: 1,
            border: "none",
            outline: "none",
            fontSize: "14px",
            fontWeight: 500,
            padding: "14px 0",
            background: "transparent",
            fontFamily: "var(--font-mono)",
            color: "var(--fg-primary)",
          }}
        />
      </div>
      <button
        type="submit"
        disabled={isRunning || !url.trim()}
        style={{
          padding: "0 32px",
          background: isRunning ? "var(--fg-muted)" : "#0a0a0a",
          color: "#ffffff",
          border: "var(--border-thick)",
          borderRadius: "var(--radius-md)",
          boxShadow: "var(--shadow-offset-sm)",
          fontSize: "14px",
          fontWeight: 800,
          letterSpacing: "0.02em",
          cursor: isRunning ? "not-allowed" : "pointer",
          transition: "all var(--transition-fast)",
          textTransform: "uppercase",
          display: "flex",
          alignItems: "center",
          gap: "8px",
        }}
      >
        {isRunning ? (
          <>
            <span
              style={{
                width: "14px",
                height: "14px",
                border: "2px solid #ffffff40",
                borderTopColor: "#ffffff",
                borderRadius: "50%",
                animation: "spin 0.8s linear infinite",
                display: "inline-block",
              }}
            />
            Analyzing...
          </>
        ) : (
          <>🚀 Launch Analysis</>
        )}
      </button>
    </form>
  );
}
