"use client";

/**
 * usePipelineState — Central state management driven entirely by SSE events.
 *
 * Reduces all SSE event types into a single PipelineState object
 * that components can read from.
 */

import { useCallback, useState } from "react";
import type { ForgeOSEvent, AgentName } from "@/types/events";
import { INITIAL_PIPELINE_STATE, type PipelineState } from "@/types/pipeline";

let terminalLineId = 0;

const LEGACY_AGENT_MAP: Record<string, string> = {
  "Supervisor": "Atlas",
  "Repository Analyst": "Oracle",
  "Planner": "Oracle",
  "Repair": "Forge",
  "QA": "Pulse",
  "Security": "Sentinel",
  "Performance": "Nitro",
  "Business": "Oracle",
};

export function usePipelineState() {
  const [state, setState] = useState<PipelineState>(INITIAL_PIPELINE_STATE);

  const handleEvent = useCallback((event: ForgeOSEvent) => {
    setState((prev) => reduceEvent(prev, event));
  }, []);

  const reset = useCallback(() => {
    terminalLineId = 0;
    setState(INITIAL_PIPELINE_STATE);
  }, []);

  const setConnected = useCallback((connected: boolean) => {
    setState((prev) => ({ ...prev, isConnected: connected }));
  }, []);

  return { state, handleEvent, reset, setConnected };
}

function reduceEvent(state: PipelineState, event: ForgeOSEvent): PipelineState {
  switch (event.event) {
    case "pipeline_update":
      return {
        ...state,
        sessionId: event.session_id,
        currentStage: event.stage,
        stageIndex: event.stage_index,
        totalStages: event.total_stages,
        isRunning: event.status === "running",
      };

    case "repository_update":
      return {
        ...state,
        repository: {
          name: event.name,
          url: event.url,
          language: event.language,
          framework: event.framework,
          testFramework: event.test_framework,
          totalFiles: event.total_files,
          totalLines: event.total_lines,
          files: event.files,
        },
      };

    case "architecture_update":
      return {
        ...state,
        architecture: {
          summary: event.summary,
          modules: event.modules,
          dependencies: event.dependencies,
          graphNodes: event.graph_nodes,
          graphEdges: event.graph_edges,
          graphTruncated: event.graph_truncated,
          entryPoints: event.entry_points,
        },
      };

    case "terminal_log":
      if (
        state.terminalLines.some(
          (line) =>
            line.timestamp === event.timestamp &&
            line.source === event.source &&
            line.content === event.content
        )
      ) {
        return state;
      }
      return {
        ...state,
        terminalLines: [
          ...state.terminalLines,
          {
            id: ++terminalLineId,
            source: event.source,
            content: event.content,
            is_error: event.is_error,
            timestamp: event.timestamp,
          },
        ],
      };

    case "planner_update":
      return {
        ...state,
        planner: {
          phase: event.phase,
          tasks: event.tasks,
          currentTask: event.current_task,
          message: event.message,
        },
      };

    case "agent_update": {
      const rawAgent = event.agent;
      const agentName = (LEGACY_AGENT_MAP[rawAgent] || rawAgent) as AgentName;
      
      // If the mapped agent name is still invalid, ignore the update to prevent breaking state structure
      if (!state.agents[agentName]) {
        return state;
      }

      return {
        ...state,
        agents: {
          ...state.agents,
          [agentName]: {
            ...state.agents[agentName],
            status: event.status,
            message: event.message,
            progress: event.progress,
            confidence: event.confidence,
          },
        },
      };
    }

    case "diff_update":
      return {
        ...state,
        diffs: [...state.diffs, event],
      };

    case "metrics_update":
      return {
        ...state,
        metrics: {
          testsTotal: event.tests_total,
          testsPassed: event.tests_passed,
          testsFailed: event.tests_failed,
          testsSkipped: event.tests_skipped,
          testStatus: event.test_status,
          testCommand: event.test_command,
          testError: event.test_error,
          coverage: event.coverage,
          issuesFound: event.issues_found,
          issuesFixed: event.issues_fixed,
        },
      };

    case "health_update":
      return {
        ...state,
        health: {
          overallScore: event.overall_score,
          dimensions: event.dimensions,
          recommendations: event.recommendations,
          repositoryGrade: event.repository_grade,
          engineeringQuality: event.engineering_quality,
          businessRisk: event.business_risk,
          criticalFindings: event.critical_findings,
          topRecommendation: event.top_recommendation,
          deploymentRecommendation: event.deployment_recommendation,
          estimatedTimeSaved: event.estimated_time_saved,
          executiveSummary: event.executive_summary,
        },
      };

    case "business_update":
      return {
        ...state,
        business: {
          stars: event.stars,
          forks: event.forks,
          contributors: event.contributors,
          openIssues: event.open_issues,
          watchers: event.watchers,
          releaseCadence: event.release_cadence,
          dependencyHealth: event.dependency_health,
          communityActivity: event.community_activity,
          executiveSummary: event.executive_summary,
          source: event.source,
          repositoryOwner: event.repository_owner,
          repositoryName: event.repository_name,
          primaryLanguage: event.primary_language,
          license: event.license,
          topics: event.topics,
          competitorSnapshot: event.competitor_snapshot,
          lastUpdated: event.last_updated,
          aiStatus: event.ai_status,
          aiModel: event.ai_model,
          aiMessage: event.ai_message,
          aiProductThesis: event.ai_product_thesis,
          aiEngineeringRisk: event.ai_engineering_risk,
          aiNextMove: event.ai_next_move,
          aiConfidence: event.ai_confidence,
          aiRequestId: event.ai_request_id,
          aiInputTokens: event.ai_input_tokens,
          aiOutputTokens: event.ai_output_tokens,
        },
      };

    case "impact_update":
      return {
        ...state,
        impact: {
          focus_files: event.focus_files,
          affected_files: event.affected_files,
          inbound_dependents: event.inbound_dependents,
          outbound_dependencies: event.outbound_dependencies,
          risk: event.risk,
          message: event.message,
        },
      };

    case "ai_activity": {
      const existingIndex = state.aiActivities.findIndex(
        (activity) => activity.operation_id === event.operation_id
      );
      const aiActivities = [...state.aiActivities];
      if (existingIndex === -1) {
        aiActivities.push(event);
      } else {
        aiActivities[existingIndex] = event;
      }
      return { ...state, aiActivities };
    }

    case "completed":
      return {
        ...state,
        isRunning: false,
        isCompleted: true,
        completion: {
          success: event.success,
          requiresReview: event.requires_review,
          durationSeconds: event.duration_seconds,
          summary: event.summary,
        },
      };

    case "error":
      return {
        ...state,
        errors: [...state.errors, event.error],
      };

    case "decision_event": {
      const rawAgent = event.agent;
      const agentName = (LEGACY_AGENT_MAP[rawAgent] || rawAgent) as AgentName;
      const normalizedEvent = {
        ...event,
        agent: agentName,
      };
      if (state.decisions.some((decision) => decisionKey(decision) === decisionKey(normalizedEvent))) {
        return state;
      }
      return {
        ...state,
        decisions: [...state.decisions, normalizedEvent],
      };
    }

    case "reasoning_update": {
      const existingIndex = state.reasoningSteps.findIndex(
        (step) => step.step_id === event.step_id
      );
      if (existingIndex === -1) {
        return {
          ...state,
          reasoningSteps: [...state.reasoningSteps, event],
        };
      }

      const reasoningSteps = [...state.reasoningSteps];
      reasoningSteps[existingIndex] = event;
      return { ...state, reasoningSteps };
    }

    default:
      return state;
  }
}

function decisionKey(event: {
  timestamp: string;
  stage: string;
  agent: string;
  status: string;
  action_taken: string;
  reason: string;
}): string {
  return [
    event.timestamp,
    event.stage,
    event.agent,
    event.status,
    event.action_taken,
    event.reason,
  ].join("|");
}
