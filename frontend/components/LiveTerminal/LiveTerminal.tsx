"use client";

import { useEffect, useRef } from "react";
import type { TerminalLine } from "@/types/pipeline";

interface LiveTerminalProps {
  lines: TerminalLine[];
}

export function LiveTerminal({ lines }: LiveTerminalProps) {
  const bodyRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [lines]);

  return (
    <div className="terminal">
      <div className="terminal-header">
        <div className="terminal-dot" style={{ background: "#ef4444" }} />
        <div className="terminal-dot" style={{ background: "#f59e0b" }} />
        <div className="terminal-dot" style={{ background: "#22c55e" }} />
        <span
          style={{
            marginLeft: "8px",
            fontSize: "12px",
            fontWeight: 600,
            color: "#94a3b8",
            textTransform: "uppercase",
            letterSpacing: "0.06em",
          }}
        >
          Live Terminal
        </span>
        <span
          style={{
            marginLeft: "auto",
            fontSize: "11px",
            color: "#64748b",
            fontFamily: "var(--font-mono)",
          }}
        >
          {lines.length} lines
        </span>
      </div>
      <div className="terminal-body" ref={bodyRef}>
        {lines.length === 0 ? (
          <div
            style={{
              color: "#64748b",
              fontStyle: "italic",
              padding: "20px 0",
              textAlign: "center",
            }}
          >
            Awaiting pipeline execution...
          </div>
        ) : (
          lines.map((line) => {
            let className = "terminal-line";
            if (line.is_error) className += " error";
            else if (line.source === "supervisor") className += " supervisor";

            return (
              <div
                key={line.id}
                className={className}
                style={{ animation: "fadeIn 100ms both" }}
              >
                {line.content}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
