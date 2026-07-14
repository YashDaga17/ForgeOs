/**
 * ForgeOS SSE Event Types
 *
 * These types mirror the backend Pydantic event models.
 * The frontend derives all UI state from these events.
 */

export type EventType =
  | "repository_update"
  | "architecture_update"
  | "terminal_log"
  | "planner_update"
  | "agent_update"
  | "diff_update"
  | "metrics_update"
  | "health_update"
  | "business_update"
  | "pipeline_update"
  | "completed"
  | "error"
  | "decision_event"
  | "reasoning_update"
  | "impact_update"
  | "ai_activity";

export type AgentName =
  | "Atlas"
  | "Forge"
  | "Pulse"
  | "Sentinel"
  | "Nitro"
  | "Oracle";

export type AgentStatus = "Idle" | "Running" | "Completed" | "Failed" | "Waiting";

export interface BaseEvent {
  event: EventType;
  timestamp: string;
  session_id: string;
}

export interface RepositoryUpdateEvent extends BaseEvent {
  event: "repository_update";
  name: string;
  url: string;
  language: string;
  framework: string;
  test_framework: string;
  test_paths: string[];
  total_files: number;
  total_lines: number;
  files: FileInfo[];
}

export interface FileInfo {
  path: string;
  lines: number;
  type: "source" | "test" | "config" | "docs" | "ci";
}

export interface ArchitectureUpdateEvent extends BaseEvent {
  event: "architecture_update";
  summary: string;
  modules: ModuleInfo[];
  dependencies: DependencyLink[];
  graph_nodes: GraphNode[];
  graph_edges: GraphEdge[];
  graph_truncated: boolean;
  entry_points: string[];
}

export interface ModuleInfo {
  name: string;
  type: string;
  files: number;
}

export interface DependencyLink {
  from: string;
  to: string;
}

export interface GraphNode {
  id: string;
  label: string;
  path: string;
  kind: "source" | "test" | "config" | "docs" | "ci" | string;
  lines: number;
  entry_point: boolean;
}

export interface GraphEdge extends DependencyLink {
  kind: "imports" | string;
}

export interface TerminalLogEvent extends BaseEvent {
  event: "terminal_log";
  source: string;
  content: string;
  is_error: boolean;
}

export interface PlannerUpdateEvent extends BaseEvent {
  event: "planner_update";
  phase: string;
  tasks: PlannerTask[];
  current_task: string;
  message: string;
}

export interface PlannerTask {
  id: number;
  title: string;
  type: string;
  priority: string;
  file: string;
}

export interface AgentUpdateEvent extends BaseEvent {
  event: "agent_update";
  agent: AgentName;
  status: AgentStatus;
  message: string;
  progress: number;
  confidence: number;
}

export interface DiffUpdateEvent extends BaseEvent {
  event: "diff_update";
  file_path: string;
  diff: string;
  explanation: string;
  confidence: number;
  risk: "low" | "medium" | "high";
}

export interface MetricsUpdateEvent extends BaseEvent {
  event: "metrics_update";
  tests_total: number;
  tests_passed: number;
  tests_failed: number;
  tests_skipped: number;
  test_status: string;
  test_command: string;
  test_error: string;
  coverage: number;
  issues_found: number;
  issues_fixed: number;
}

export interface HealthUpdateEvent extends BaseEvent {
  event: "health_update";
  overall_score: number;
  dimensions: Record<string, number>;
  recommendations: string[];
  repository_grade: string;
  engineering_quality: string;
  business_risk: string;
  critical_findings: number;
  top_recommendation: string;
  deployment_recommendation: string;
  estimated_time_saved: string;
  executive_summary: string;
}

export interface BusinessUpdateEvent extends BaseEvent {
  event: "business_update";
  stars: number;
  forks: number;
  contributors: number;
  open_issues: number;
  watchers: number;
  release_cadence: string;
  dependency_health: string;
  community_activity: string;
  executive_summary: string;
  source: "github" | "local" | string;
  repository_owner: string;
  repository_name: string;
  primary_language: string;
  license: string;
  topics: string[];
  competitor_snapshot: CompetitorSnapshot[];
  last_updated: string;
  ai_status: "completed" | "blocked" | "failed" | "not_requested" | string;
  ai_model: string;
  ai_message: string;
  ai_product_thesis: string;
  ai_engineering_risk: string;
  ai_next_move: string;
  ai_confidence: number;
  ai_request_id: string;
  ai_input_tokens: number;
  ai_output_tokens: number;
}

export interface CompetitorSnapshot {
  name: string;
  stars: number;
  forks: number;
  description: string;
}

export interface PipelineUpdateEvent extends BaseEvent {
  event: "pipeline_update";
  stage: string;
  stage_index: number;
  total_stages: number;
  status: string;
  message: string;
}

export interface CompletedEvent extends BaseEvent {
  event: "completed";
  success: boolean;
  requires_review: boolean;
  duration_seconds: number;
  summary: string;
}

export interface ErrorEvent extends BaseEvent {
  event: "error";
  error: string;
  stage: string;
  recoverable: boolean;
}

export interface DecisionEvent extends BaseEvent {
  event: "decision_event";
  stage: string;
  agent: AgentName;
  reason: string;
  evidence: string;
  action_taken: string;
  expected_outcome?: string;
  confidence: number;
  status: string;
}

export type ReasoningStatus = "running" | "completed" | "blocked" | "failed";

export interface ReasoningUpdateEvent extends BaseEvent {
  event: "reasoning_update";
  step_id: string;
  stage: string;
  phase: string;
  title: string;
  detail: string;
  status: ReasoningStatus;
  agent: AgentName;
  evidence: string[];
  confidence: number;
}

export interface ImpactUpdateEvent extends BaseEvent {
  event: "impact_update";
  focus_files: string[];
  affected_files: string[];
  inbound_dependents: number;
  outbound_dependencies: number;
  risk: "low" | "medium" | "high";
  message: string;
}

export type AIActivityStatus = "running" | "completed" | "blocked" | "failed";

export interface AIActivityEvent extends BaseEvent {
  event: "ai_activity";
  operation_id: string;
  capability: string;
  agent: AgentName | null;
  status: AIActivityStatus;
  model: string;
  message: string;
  request_id: string;
  input_tokens: number;
  output_tokens: number;
}

export type ForgeOSEvent =
  | RepositoryUpdateEvent
  | ArchitectureUpdateEvent
  | TerminalLogEvent
  | PlannerUpdateEvent
  | AgentUpdateEvent
  | DiffUpdateEvent
  | MetricsUpdateEvent
  | HealthUpdateEvent
  | BusinessUpdateEvent
  | PipelineUpdateEvent
  | CompletedEvent
  | ErrorEvent
  | DecisionEvent
  | ReasoningUpdateEvent
  | ImpactUpdateEvent
  | AIActivityEvent;
