/**
 * AI Architecture Engine API Client
 * Connects the Next.js frontend to the native Next.js Architecture Engine (REE + SAE pipeline).
 */

export const API_HOST = (process.env.NEXT_PUBLIC_AI_ENGINE_URL || "").trim().replace(/\/+$/, "");
export const API_BASE_URL = `${API_HOST}/api/v1/generations`;
export const HEALTH_URL = `${API_HOST}/api/v1/health`;

export type LldType = "backend" | "frontend" | "database" | "security" | "cloud";
export type LldStatusType = "NOT_STARTED" | "GENERATING" | "READY" | "FAILED";

export interface InterviewQuestion {
  question_id: string;
  question: string;
  rationale?: string;
  priority?: "high" | "medium" | "low" | string;
  options?: string[];
  default_option?: string;
}

export interface StartGenerationResponse {
  generation_id: string;
  status: "INTERVIEW_IN_PROGRESS" | "INTERVIEW_COMPLETED" | string;
  current_question?: InterviewQuestion;
  message?: string;
  detail?: string;
}

export interface SubmitAnswerResponse {
  generation_id: string;
  status: "INTERVIEW_IN_PROGRESS" | "INTERVIEW_COMPLETED" | string;
  next_question?: InterviewQuestion;
  message?: string;
  detail?: string;
}

export interface GenerateArchitectureResponse {
  generation_id: string;
  status: string;
  arsrs: Record<string, unknown>;
  hld: Record<string, unknown>;
  detail?: string;
}

export interface LldResponse {
  status: LldStatusType;
  data?: Record<string, unknown>;
  message?: string;
  error?: string;
  detail?: string;
}

export interface LogEntry {
  timestamp: string;
  stage: string;
  message: string;
  level: "INFO" | "WARNING" | "ERROR" | "DEBUG" | string;
  process?: string;
  process_status?: string;
  lld_status?: Record<LldType, LldStatusType>;
  lld_completed?: LldType;
}

export interface LogsResponse {
  generation_id: string;
  logs: LogEntry[];
}

export interface StatusResponse {
  generation_id: string;
  status: string;
  llds?: Record<LldType, LldStatusType>;
}

export const aiEngineApi = {
  // 1. Health check
  async checkHealth(): Promise<{ ok: boolean; version?: string }> {
    try {
      const rootUrl = API_HOST || "";
      const res = await fetch(`${rootUrl}/`, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json().catch(() => ({}));
        return { ok: true, version: data?.version || "2.0.0" };
      }
      const altRes = await fetch(HEALTH_URL, { cache: "no-store" });
      if (altRes.ok) {
        const data = await altRes.json().catch(() => ({}));
        return { ok: true, version: data?.version || "2.0.0" };
      }
      return { ok: false };
    } catch {
      return { ok: false };
    }
  },

  // 2. Start generation
  async startGeneration(prompt: string): Promise<StartGenerationResponse> {
    const res = await fetch(API_BASE_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || `Server error (${res.status})`);
    }
    return data;
  },

  // 3. Submit interview answer
  async submitAnswer(
    generationId: string,
    questionId: string,
    answer: string
  ): Promise<SubmitAnswerResponse> {
    const res = await fetch(`${API_BASE_URL}/${generationId}/answers`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question_id: questionId,
        answer,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || `Server error (${res.status})`);
    }
    return data;
  },

  // 4. Generate ARSRS + HLD
  async generateArchitecture(
    generationId: string
  ): Promise<GenerateArchitectureResponse> {
    const res = await fetch(`${API_BASE_URL}/${generationId}/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || `Server error (${res.status})`);
    }
    return data;
  },

  // 5. Get specific LLD
  async getLLD(generationId: string, lldType: LldType): Promise<LldResponse> {
    const res = await fetch(`${API_BASE_URL}/${generationId}/lld/${lldType}`);
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || `Failed to fetch ${lldType} LLD (${res.status})`);
    }
    return data;
  },

  // 6. Get logs history
  async getLogs(generationId: string): Promise<LogsResponse> {
    const res = await fetch(`${API_BASE_URL}/${generationId}/logs`);
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || `Failed to fetch logs (${res.status})`);
    }
    return data;
  },

  // 7. Get SSE logs stream URL
  getLogsStreamUrl(generationId: string): string {
    return `${API_BASE_URL}/${generationId}/logs/stream`;
  },

  // 8. Get generation status
  async getStatus(generationId: string): Promise<StatusResponse> {
    const res = await fetch(`${API_BASE_URL}/${generationId}/status`);
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || `Failed to fetch status (${res.status})`);
    }
    return data;
  },
};
