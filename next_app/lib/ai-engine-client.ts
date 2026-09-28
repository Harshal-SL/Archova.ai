/**
 * AI Architecture Engine Client — Frontend Standalone Mode
 * Provides instant, rich sample data for all architecture stages without requiring a backend server.
 */

import {
  dummyHldData,
  dummyAllLldData,
  dummyArsrs,
  sampleInterviewQuestions,
} from "./mock-data";

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

// In-memory question tracker for frontend simulation
const answerCounts: Record<string, number> = {};

export const aiEngineApi = {
  // 1. Health check — Frontend Standalone Mode
  async checkHealth(): Promise<{ ok: boolean; version?: string }> {
    return { ok: true, version: "2.5.0-client" };
  },

  // 2. Start generation with sample interview questions
  async startGeneration(prompt: string): Promise<StartGenerationResponse> {
    const genId = `gen-frontend-${Date.now()}`;
    answerCounts[genId] = 0;

    return {
      generation_id: genId,
      status: "INTERVIEW_IN_PROGRESS",
      current_question: sampleInterviewQuestions[0],
      message: "Frontend simulation: Requirements Engineering Engine initialized.",
    };
  },

  // 3. Submit interview answer
  async submitAnswer(
    generationId: string,
    questionId: string,
    _answer: string
  ): Promise<SubmitAnswerResponse> {
    const currentCount = answerCounts[generationId] || 0;
    const nextIdx = currentCount + 1;
    answerCounts[generationId] = nextIdx;

    if (nextIdx < sampleInterviewQuestions.length) {
      return {
        generation_id: generationId,
        status: "INTERVIEW_IN_PROGRESS",
        next_question: sampleInterviewQuestions[nextIdx],
        message: `Answer recorded for ${questionId}. Proceeding to question ${nextIdx + 1}.`,
      };
    }

    return {
      generation_id: generationId,
      status: "INTERVIEW_COMPLETED",
      message: "Stakeholder requirements clarified. Ready to synthesize ARSRS and Visual HLD.",
    };
  },

  // 4. Generate ARSRS + HLD with sample architecture
  async generateArchitecture(
    generationId: string
  ): Promise<GenerateArchitectureResponse> {
    return {
      generation_id: generationId,
      status: "COMPLETED",
      arsrs: dummyArsrs as Record<string, unknown>,
      hld: dummyHldData as Record<string, unknown>,
    };
  },

  // 5. Get specific LLD with rich sample data
  async getLLD(_generationId: string, lldType: LldType): Promise<LldResponse> {
    const data = dummyAllLldData[lldType] || dummyAllLldData.backend;
    return {
      status: "READY",
      data: data as Record<string, unknown>,
      message: `${lldType.toUpperCase()} Low-Level Design blueprint loaded successfully.`,
    };
  },

  // 6. Get logs history
  async getLogs(generationId: string): Promise<LogsResponse> {
    const now = new Date().toTimeString().split(" ")[0];
    return {
      generation_id: generationId,
      logs: [
        {
          timestamp: now,
          stage: "REE",
          message: "✓ Stakeholder requirements validated & ARSRS synthesized.",
          level: "INFO",
        },
        {
          timestamp: now,
          stage: "SAE",
          message: "✓ High-Level Architecture topology generated with 9 microservices.",
          level: "INFO",
        },
        {
          timestamp: now,
          stage: "LLD",
          message: "✓ Parallel synthesis completed across 5 domains (Backend, Frontend, DB, Security, Cloud).",
          level: "INFO",
        },
      ],
    };
  },

  // 7. Stream URL dummy fallback
  getLogsStreamUrl(generationId: string): string {
    return `/api/v1/generations/${generationId}/logs/stream`;
  },

  // 8. Get status
  async getStatus(generationId: string): Promise<StatusResponse> {
    return {
      generation_id: generationId,
      status: "COMPLETED",
      llds: {
        backend: "READY",
        frontend: "READY",
        database: "READY",
        security: "READY",
        cloud: "READY",
      },
    };
  },
};
