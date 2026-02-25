export interface Finding {
  category: string;
  severity: "CRITICAL" | "WARNING" | "INFO" | "PASS";
  layer: "TRADITIONAL" | "AI" | "BOTH";
  title: string;
  detail: string;
  action: string;
  effort: "LOW" | "MEDIUM" | "HIGH";
  impact: "LOW" | "MEDIUM" | "HIGH";
}

export interface PageSnapshot {
  url: string;
  status_code: number;
  title: string;
  word_count: number;
  token_count: number;
  chars_per_token: number;
  load_time_ms: number;
  h1_count: number;
  h2_count: number;
  has_schema: boolean;
  schema_types: string[];
  canonical: string;
  meta_description: string;
}

export interface AnalysisSummary {
  critical: number;
  warning: number;
  info: number;
  passing: number;
}

export interface LayerSummary {
  traditional_issues: number;
  ai_issues: number;
  traditional_total: number;
  ai_total: number;
}

export interface AnalysisResult {
  score: number;
  url: string;
  domain: string;
  pages_analyzed: number;
  pages: PageSnapshot[];
  findings: Finding[];
  summary: AnalysisSummary;
  layer_summary: LayerSummary;
}

export interface ProgressStep {
  stage: string;
  detail?: string;
  label: string;
}

export type AnalysisStatus = "idle" | "loading" | "complete" | "error";

export interface AnalysisState {
  status: AnalysisStatus;
  progressSteps: ProgressStep[];
  currentStage: string;
  result: AnalysisResult | null;
  error: string | null;
}
