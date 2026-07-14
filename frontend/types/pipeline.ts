/**
 * ForgeOS Pipeline State Types
 *
 * Central state structure driven entirely by SSE events.
 */

import type {
  AgentName,
  AgentStatus,
  AIActivityEvent,
  DependencyLink,
  DiffUpdateEvent,
  FileInfo,
  GraphEdge,
  GraphNode,
  ImpactUpdateEvent,
  ModuleInfo,
  PlannerTask,
  DecisionEvent,
  ReasoningUpdateEvent,
} from "./events";

export interface AgentState {
  name: AgentName;
  status: AgentStatus;
  message: string;
  progress: number;
  confidence: number;
  emoji: string;
}

export interface TerminalLine {
  id: number;
  source: string;
  content: string;
  is_error: boolean;
  timestamp: string;
}

export interface PipelineState {
  // Connection
  isConnected: boolean;
  sessionId: string | null;

  // Pipeline progress
  currentStage: string;
  stageIndex: number;
  totalStages: number;
  isRunning: boolean;
  isCompleted: boolean;

  // Repository
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

  // Architecture
  architecture: {
    summary: string;
    modules: ModuleInfo[];
    dependencies: DependencyLink[];
    graphNodes: GraphNode[];
    graphEdges: GraphEdge[];
    graphTruncated: boolean;
    entryPoints: string[];
  };

  // Agents
  agents: Record<AgentName, AgentState>;

  // Observable OpenAI activity for real bounded requests.
  aiActivities: AIActivityEvent[];

  // Deterministic dependency reach for the current repair target.
  impact: Omit<ImpactUpdateEvent, "event" | "timestamp" | "session_id">;

  // Planner
  planner: {
    phase: string;
    tasks: PlannerTask[];
    currentTask: string;
    message: string;
  };

  // Terminal
  terminalLines: TerminalLine[];

  // Diffs
  diffs: DiffUpdateEvent[];

  // Metrics
  metrics: {
    testsTotal: number;
    testsPassed: number;
    testsFailed: number;
    testsSkipped: number;
    testStatus: string;
    testCommand: string;
    testError: string;
    coverage: number;
    issuesFound: number;
    issuesFixed: number;
  };

  // Health
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

  // Business
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
    aiRequestId: string;
    aiInputTokens: number;
    aiOutputTokens: number;
  };

  // Completion
  completion: {
    success: boolean;
    requiresReview: boolean;
    durationSeconds: number;
    summary: string;
  } | null;

  // Errors
  errors: string[];

  // Decision Log
  decisions: DecisionEvent[];

  // Observable reasoning trace, kept separate from pipeline stage history
  reasoningSteps: ReasoningUpdateEvent[];
}

export const AGENT_CONFIG: Record<AgentName, { emoji: string; label: string }> = {
  Atlas: { emoji: "🎯", label: "Atlas" },
  Forge: { emoji: "🔧", label: "Forge" },
  Pulse: { emoji: "✅", label: "Pulse" },
  Sentinel: { emoji: "🛡️", label: "Sentinel" },
  Nitro: { emoji: "⚡", label: "Nitro" },
  Oracle: { emoji: "🔍", label: "Oracle" },
};

export const INITIAL_PIPELINE_STATE: PipelineState = {
  isConnected: false,
  sessionId: null,
  currentStage: "",
  stageIndex: 0,
  totalStages: 14,
  isRunning: false,
  isCompleted: false,
  repository: {
    name: "",
    url: "",
    language: "",
    framework: "",
    testFramework: "",
    totalFiles: 0,
    totalLines: 0,
    files: [],
  },
  architecture: {
    summary: "",
    modules: [],
    dependencies: [],
    graphNodes: [],
    graphEdges: [],
    graphTruncated: false,
    entryPoints: [],
  },
  agents: Object.fromEntries(
    (
      [
        "Atlas",
        "Forge",
        "Pulse",
        "Sentinel",
        "Nitro",
        "Oracle",
      ] as AgentName[]
    ).map((name) => [
      name,
      {
        name,
        status: "Idle" as AgentStatus,
        message: "Awaiting mission...",
        progress: 0,
        confidence: 0,
        emoji: AGENT_CONFIG[name].emoji,
      },
    ])
  ) as Record<AgentName, AgentState>,
  aiActivities: [],
  impact: {
    focus_files: [],
    affected_files: [],
    inbound_dependents: 0,
    outbound_dependencies: 0,
    risk: "low",
    message: "",
  },
  planner: { phase: "", tasks: [], currentTask: "", message: "" },
  terminalLines: [],
  diffs: [],
  metrics: {
    testsTotal: 0,
    testsPassed: 0,
    testsFailed: 0,
    testsSkipped: 0,
    testStatus: "not_run",
    testCommand: "",
    testError: "",
    coverage: 0,
    issuesFound: 0,
    issuesFixed: 0,
  },
  health: {
    overallScore: 0,
    dimensions: {},
    recommendations: [],
    repositoryGrade: "Pending",
    engineeringQuality: "Not assessed",
    businessRisk: "Unknown",
    criticalFindings: 0,
    topRecommendation: "",
    deploymentRecommendation: "",
    estimatedTimeSaved: "",
    executiveSummary: "",
  },
  business: {
    stars: 0,
    forks: 0,
    contributors: 0,
    openIssues: 0,
    watchers: 0,
    releaseCadence: "",
    dependencyHealth: "",
    communityActivity: "",
    executiveSummary: "",
    source: "",
    repositoryOwner: "",
    repositoryName: "",
    primaryLanguage: "",
    license: "",
    topics: [],
    competitorSnapshot: [],
    lastUpdated: "",
    aiStatus: "not_requested",
    aiModel: "",
    aiMessage: "",
    aiProductThesis: "",
    aiEngineeringRisk: "",
    aiNextMove: "",
    aiConfidence: 0,
    aiRequestId: "",
    aiInputTokens: 0,
    aiOutputTokens: 0,
  },
  completion: null,
  errors: [],
  decisions: [],
  reasoningSteps: [],
};
