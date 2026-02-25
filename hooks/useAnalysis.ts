"use client";

import { useState, useRef, useCallback } from "react";
import {
  AnalysisState,
  AnalysisResult,
  ProgressStep,
} from "@/lib/types";

const STAGE_LABELS: Record<string, string> = {
  domain: "Checking domain strategy",
  robots: "Fetching robots.txt",
  sitemap: "Fetching sitemap.xml",
  agent_files: "Checking AI agent files (llms.txt)",
  page: "Analyzing page",
  internal_links: "Analyzing internal link structure",
  complete: "Finalizing results",
};

function stageLabel(stage: string, detail?: string): string {
  if (stage === "page" && detail) {
    return `Analyzing: ${detail.replace(/^https?:\/\//, "").slice(0, 55)}`;
  }
  return STAGE_LABELS[stage] ?? stage;
}

const INITIAL_STATE: AnalysisState = {
  status: "idle",
  progressSteps: [],
  currentStage: "",
  result: null,
  error: null,
};

export function useAnalysis() {
  const [state, setState] = useState<AnalysisState>(INITIAL_STATE);
  const abortRef = useRef<AbortController | null>(null);

  const analyze = useCallback(async (url: string, maxPages: number = 5) => {
    if (abortRef.current) {
      abortRef.current.abort();
    }
    abortRef.current = new AbortController();

    setState({
      status: "loading",
      progressSteps: [],
      currentStage: "Starting analysis...",
      result: null,
      error: null,
    });

    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, maxPages }),
        signal: abortRef.current.signal,
      });

      if (!response.ok || !response.body) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let sseBuffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        sseBuffer += decoder.decode(value, { stream: true });
        const parts = sseBuffer.split("\n\n");
        sseBuffer = parts.pop() ?? "";

        for (const part of parts) {
          const dataLine = part
            .split("\n")
            .find((l) => l.startsWith("data: "));
          if (!dataLine) continue;
          const raw = dataLine.slice(6).trim();
          if (raw === "[DONE]") continue;

          let event: {
            type: string;
            stage?: string;
            detail?: string;
            data?: AnalysisResult;
            message?: string;
          };
          try {
            event = JSON.parse(raw);
          } catch {
            continue;
          }

          if (event.type === "progress") {
            const stage = event.stage ?? "";
            const detail = event.detail;
            const label = stageLabel(stage, detail);
            const step: ProgressStep = { stage, detail, label };

            setState((prev) => ({
              ...prev,
              currentStage: label,
              progressSteps: [...prev.progressSteps, step],
            }));
          } else if (event.type === "result" && event.data) {
            setState((prev) => ({
              ...prev,
              status: "complete",
              result: event.data!,
              currentStage: "Complete",
            }));
          } else if (event.type === "error") {
            setState((prev) => ({
              ...prev,
              status: "error",
              error: event.message ?? "Unknown error",
            }));
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === "AbortError") return;
      setState((prev) => ({
        ...prev,
        status: "error",
        error: err instanceof Error ? err.message : "Unknown error",
      }));
    }
  }, []);

  const reset = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
    }
    setState(INITIAL_STATE);
  }, []);

  return { ...state, analyze, reset };
}
