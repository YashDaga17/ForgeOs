/**
 * ForgeOS API Client
 *
 * Handles communication with the FastAPI backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface AnalyzeResponse {
  session_id: string;
  status: string;
  message: string;
}

export async function analyzeRepository(
  repositoryUrl: string
): Promise<AnalyzeResponse> {
  const response = await fetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repository_url: repositoryUrl }),
  });

  if (!response.ok) {
    throw new Error(`Analysis failed: ${response.statusText}`);
  }

  return response.json();
}

export function getStreamUrl(sessionId?: string): string {
  const url = new URL(`${API_BASE}/api/stream`);
  if (sessionId) {
    url.searchParams.set("session_id", sessionId);
  }
  return url.toString();
}
