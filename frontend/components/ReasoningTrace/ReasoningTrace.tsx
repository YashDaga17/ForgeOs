"use client";

import type { AgentStatus, ReasoningStatus, ReasoningUpdateEvent } from "@/types/events";
import { useEffect, useRef, type CSSProperties } from "react";
import { AGENT_CONFIG } from "@/types/pipeline";
import { Mascot } from "@/components/Mascot/Mascot";

interface ReasoningTraceProps {
  steps: ReasoningUpdateEvent[];
}

const STATUS_LABELS: Record<ReasoningStatus, string> = {
  running: "Active",
  completed: "Confirmed",
  blocked: "Gate held",
  failed: "Rejected",
};

function mascotStatus(status: ReasoningStatus): AgentStatus {
  if (status === "running") return "Running";
  if (status === "completed") return "Completed";
  if (status === "failed") return "Failed";
  return "Waiting";
}

function statusColor(status: ReasoningStatus): string {
  if (status === "running") return "var(--accent-blue)";
  if (status === "completed") return "var(--accent-green)";
  if (status === "failed") return "var(--accent-red)";
  return "var(--accent-amber)";
}

export function ReasoningTrace({ steps }: ReasoningTraceProps) {
  const traceBodyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const traceBody = traceBodyRef.current;
    if (traceBody) {
      traceBody.scrollTo({ top: traceBody.scrollHeight, behavior: "smooth" });
    }
  }, [steps]);

  return (
    <section className="card reasoning-trace" aria-labelledby="reasoning-trace-title">
      <div className="card-header">
        <span aria-hidden="true">WHY</span>
        <span id="reasoning-trace-title">Reasoning Trace</span>
        <span className="reasoning-trace__mode">Why ForgeOS took or withheld action</span>
      </div>

      {steps.length === 0 ? (
        <div className="card-body reasoning-trace__empty" aria-live="polite">
          <div className="reasoning-trace__empty-mark" aria-hidden="true">01</div>
          <div>
            <strong>Awaiting engineering rationale</strong>
            <p>Launch a repository analysis to watch ForgeOS explain each decision as it happens.</p>
          </div>
        </div>
      ) : (
        <div ref={traceBodyRef} className="card-body reasoning-trace__body" aria-live="polite">
          <div className="reasoning-trace__intro">
            <span>Pipeline = execution</span>
            <span>Reasoning = evidence + gate decision</span>
          </div>

          <ol className="reasoning-trace__list">
            {steps.map((step, index) => {
              const config = AGENT_CONFIG[step.agent];
              const color = statusColor(step.status);
              const isLast = index === steps.length - 1;

              return (
                <li
                  className={`reasoning-step reasoning-step--${step.status}`}
                  key={step.step_id}
                  style={{ "--reasoning-accent": color } as CSSProperties}
                >
                  <div className="reasoning-step__rail" aria-hidden="true">
                    <span className="reasoning-step__index">{String(index + 1).padStart(2, "0")}</span>
                    {!isLast && <span className="reasoning-step__line" />}
                  </div>

                  <div className="reasoning-step__content">
                    <div className="reasoning-step__topline">
                      <div className="reasoning-step__identity">
                        <div className="reasoning-step__mascot">
                          <Mascot name={step.agent} state={mascotStatus(step.status)} />
                        </div>
                        <div>
                          <div className="reasoning-step__heading">
                            <h3>{step.title}</h3>
                            <span className="reasoning-step__phase">{step.phase}</span>
                          </div>
                          <span className="reasoning-step__agent">{config?.label ?? step.agent}</span>
                        </div>
                      </div>
                      <span className="reasoning-step__status">{STATUS_LABELS[step.status]}</span>
                    </div>

                    <p className="reasoning-step__detail">{step.detail}</p>

                    {step.evidence.length > 0 && (
                      <div className="reasoning-step__evidence" aria-label="Evidence">
                        {step.evidence.map((item) => (
                          <code key={item}>{item}</code>
                        ))}
                      </div>
                    )}

                    <div className="reasoning-step__footer">
                      <span>{step.stage}</span>
                      <span>{Math.round(step.confidence * 100)}% confidence</span>
                    </div>
                  </div>
                </li>
              );
            })}
          </ol>
        </div>
      )}
    </section>
  );
}
