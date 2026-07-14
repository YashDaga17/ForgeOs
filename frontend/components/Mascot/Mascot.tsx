"use client";

/**
 * Mascot — Animated SVG illustrations for specialized agents
 *
 * Designed in a flat, high-contrast Neo-Brutalist illustration style.
 * Supports three states: Idle (bob/tilt), Working (rapid actions/pulses),
 * and Celebration (bouncing/dancing).
 */

import type { AgentName, AgentStatus } from "@/types/events";

interface MascotProps {
  name: AgentName | string;
  state: AgentStatus | string;
}

export function Mascot({ name, state }: MascotProps) {
  const status = state.toLowerCase();
  const isWorking = status === "running";
  const isCompleted = status === "completed";

  // Common styling class name helpers
  const animationClass = isWorking
    ? "working"
    : isCompleted
    ? "celebration"
    : "idle";

  return (
    <div
      style={{
        width: "48px",
        height: "48px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
      }}
    >
      <svg
        viewBox="0 0 48 48"
        width="100%"
        height="100%"
        style={{ overflow: "visible" }}
      >
        <defs>
          <style>{`
            /* Global Animations */
            @keyframes idle-bob {
              0%, 100% { transform: translateY(0px); }
              50% { transform: translateY(-2.5px); }
            }
            @keyframes idle-tilt {
              0%, 100% { transform: rotate(-3deg); }
              50% { transform: rotate(3deg); }
            }
            @keyframes working-spin {
              from { transform: rotate(0deg); }
              to { transform: rotate(360deg); }
            }
            @keyframes working-shake {
              0%, 100% { transform: translate(0, 0) rotate(0deg); }
              20% { transform: translate(-1px, 1px) rotate(-1deg); }
              40% { transform: translate(1px, -1px) rotate(1deg); }
              60% { transform: translate(-1px, -1px) rotate(0deg); }
              80% { transform: translate(1px, 1px) rotate(1deg); }
            }
            @keyframes working-pulse {
              0%, 100% { transform: scale(0.95); }
              50% { transform: scale(1.05); }
            }
            @keyframes celebration-dance {
              0%, 100% { transform: translateY(0) scale(1) rotate(0deg); }
              50% { transform: translateY(-4px) scale(1.08) rotate(4deg); }
            }

            /* Agent Specific Anim Hooks */
            .atlas-core.idle { animation: idle-tilt 2.5s ease-in-out infinite; transform-origin: 24px 24px; }
            .atlas-core.working { animation: working-spin 3s linear infinite; transform-origin: 24px 24px; }
            .atlas-core.celebration { animation: celebration-dance 1s ease-in-out infinite; transform-origin: 24px 24px; }

            .forge-hammer.idle { animation: idle-tilt 2s ease-in-out infinite; transform-origin: 28px 12px; }
            .forge-hammer.working { animation: working-shake 0.3s linear infinite; transform-origin: 28px 12px; }
            .forge-hammer.celebration { animation: celebration-dance 0.8s ease-in-out infinite; transform-origin: 28px 12px; }

            @keyframes wave-flow {
              from { stroke-dashoffset: 0; }
              to { stroke-dashoffset: -20; }
            }
            .pulse-wave.idle { stroke-dasharray: 4, 2; animation: wave-flow 2s linear infinite; }
            .pulse-wave.working { stroke-dasharray: 6, 2; animation: wave-flow 0.5s linear infinite; }
            .pulse-wave.celebration { animation: working-pulse 1s ease-in-out infinite; transform-origin: 24px 24px; }

            .sentinel-shield.idle { animation: idle-bob 2.5s ease-in-out infinite; }
            .sentinel-shield.working { animation: working-pulse 1s ease-in-out infinite; transform-origin: 24px 24px; }
            .sentinel-shield.celebration { animation: celebration-dance 1s ease-in-out infinite; transform-origin: 24px 24px; }

            .nitro-bolt.idle { animation: idle-bob 2s ease-in-out infinite; }
            .nitro-bolt.working { animation: working-shake 0.2s linear infinite; }
            .nitro-bolt.celebration { animation: celebration-dance 0.7s ease-in-out infinite; transform-origin: 24px 24px; }

            .oracle-eye.idle { animation: idle-bob 3s ease-in-out infinite; }
            .oracle-eye.working { animation: working-pulse 1.2s ease-in-out infinite; transform-origin: 24px 24px; }
            .oracle-eye.celebration { animation: celebration-dance 1s ease-in-out infinite; transform-origin: 24px 24px; }
          `}</style>
        </defs>

        {/* Mascot Graphics */}
        {name === "Atlas" && (
          <g className={`atlas-core ${animationClass}`}>
            {/* Outer Ring */}
            <circle
              cx="24"
              cy="24"
              r="18"
              fill="none"
              stroke="#0a0a0a"
              strokeWidth="2.5"
            />
            {/* Crosshairs */}
            <line
              x1="24"
              y1="2"
              x2="24"
              y2="46"
              stroke="#0a0a0a"
              strokeWidth="1.5"
              strokeDasharray="2 2"
            />
            <line
              x1="2"
              y1="24"
              x2="46"
              y2="24"
              stroke="#0a0a0a"
              strokeWidth="1.5"
              strokeDasharray="2 2"
            />
            {/* Central Globe Core */}
            <circle
              cx="24"
              cy="24"
              r="11"
              fill="var(--accent-purple)"
              stroke="#0a0a0a"
              strokeWidth="2.5"
            />
            {/* Navigational Pointer */}
            <polygon
              points="24,17 28,26 24,24 20,26"
              fill="#ffffff"
              stroke="#0a0a0a"
              strokeWidth="2"
            />
          </g>
        )}

        {name === "Forge" && (
          <g>
            {/* Anvil Base */}
            <path
              d="M 10,38 L 38,38 L 34,30 L 14,30 Z"
              fill="#e2e8f0"
              stroke="#0a0a0a"
              strokeWidth="2"
            />
            {/* Anvil Top Block */}
            <path
              d="M 6,22 L 32,22 L 38,30 L 10,30 Z"
              fill="var(--accent-orange)"
              stroke="#0a0a0a"
              strokeWidth="2.5"
            />
            {/* Hammer Illustration */}
            <g className={`forge-hammer ${animationClass}`}>
              {/* Handle */}
              <line
                x1="28"
                y1="12"
                x2="38"
                y2="2"
                stroke="#0a0a0a"
                strokeWidth="3.5"
                strokeLinecap="round"
              />
              {/* Hammer Head */}
              <rect
                x="22"
                y="6"
                width="12"
                height="8"
                rx="1"
                fill="#ffffff"
                stroke="#0a0a0a"
                strokeWidth="2"
              />
            </g>
          </g>
        )}

        {name === "Pulse" && (
          <g>
            {/* Oscilloscope Grid Background */}
            <rect
              x="6"
              y="10"
              width="36"
              height="28"
              rx="4"
              fill="#0f172a"
              stroke="#0a0a0a"
              strokeWidth="2.5"
            />
            {/* Moving Waveform Line */}
            <path
              className={`pulse-wave ${animationClass}`}
              d="M 8,24 L 16,24 L 20,14 L 24,34 L 28,20 L 32,24 L 40,24"
              fill="none"
              stroke="var(--accent-green)"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </g>
        )}

        {name === "Sentinel" && (
          <g className={`sentinel-shield ${animationClass}`}>
            {/* Neo-brutalist Shield Body */}
            <path
              d="M 12,8 Q 24,6 36,8 L 36,24 Q 36,36 24,42 Q 12,36 12,24 Z"
              fill="var(--accent-cyan)"
              stroke="#0a0a0a"
              strokeWidth="2.5"
            />
            {/* Central Secure Lock Icon */}
            <rect
              x="20"
              y="20"
              width="8"
              height="8"
              rx="1.5"
              fill="#ffffff"
              stroke="#0a0a0a"
              strokeWidth="2"
            />
            <path
              d="M 22,20 L 22,16 Q 24,13 26,16 L 26,20"
              fill="none"
              stroke="#0a0a0a"
              strokeWidth="2"
            />
          </g>
        )}

        {name === "Nitro" && (
          <g className={`nitro-bolt ${animationClass}`}>
            {/* Circular background shadow */}
            <circle
              cx="24"
              cy="24"
              r="16"
              fill="#ffffff"
              stroke="#0a0a0a"
              strokeWidth="2"
            />
            {/* Lightning Bolt */}
            <polygon
              points="27,6 16,25 24,25 21,42 32,23 24,23"
              fill="var(--accent-amber)"
              stroke="#0a0a0a"
              strokeWidth="2.5"
              strokeLinejoin="round"
            />
          </g>
        )}

        {name === "Oracle" && (
          <g className={`oracle-eye ${animationClass}`}>
            {/* Eye Shape Outlines */}
            <path
              d="M 6,24 Q 24,10 42,24 Q 24,38 6,24 Z"
              fill="#ffffff"
              stroke="#0a0a0a"
              strokeWidth="2.5"
            />
            {/* Iris */}
            <circle
              cx="24"
              cy="24"
              r="7"
              fill="var(--accent-blue)"
              stroke="#0a0a0a"
              strokeWidth="2"
            />
            {/* Pupil Highlight */}
            <circle cx="26.5" cy="21.5" r="2" fill="#ffffff" />
            {/* Small Sparkles */}
            <path
              d="M 37,13 L 39,15 M 39,13 L 37,15 M 9,13 L 11,15 M 11,13 L 9,15"
              stroke="#0a0a0a"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </g>
        )}
      </svg>
    </div>
  );
}
