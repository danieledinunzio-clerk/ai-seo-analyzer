"use client";

import { AnalysisResult } from "@/lib/types";
import { ScoreCard } from "./ScoreCard";
import { LayerBreakdown } from "./LayerBreakdown";
import { PageSnapshotTable } from "./PageSnapshotTable";
import { FindingsAccordion } from "./FindingsAccordion";
import { PriorityMatrix } from "./PriorityMatrix";
import { QuickWins } from "./QuickWins";
import { RoadmapTimeline } from "./RoadmapTimeline";

interface ResultsDashboardProps {
  result: AnalysisResult;
  onReset: () => void;
}

export function ResultsDashboard({ result, onReset }: ResultsDashboardProps) {
  return (
    <div className="fade-up max-w-5xl mx-auto px-4 py-12 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Audit Report</h2>
          <p className="text-sm text-white/40 mt-0.5 truncate max-w-md">{result.url}</p>
        </div>
        <button
          onClick={onReset}
          className="text-sm text-white/40 hover:text-white/70 border border-white/10 hover:border-white/25 px-3 py-1.5 rounded-lg transition-all"
        >
          New Analysis
        </button>
      </div>

      {/* Score + Layer breakdown */}
      <ScoreCard
        score={result.score}
        summary={result.summary}
        domain={result.domain}
        pagesAnalyzed={result.pages_analyzed}
      />
      <LayerBreakdown layerSummary={result.layer_summary} />

      {/* Page snapshot */}
      <PageSnapshotTable pages={result.pages} baseUrl={result.url} />

      {/* Quick wins */}
      <QuickWins findings={result.findings} />

      {/* Priority matrix */}
      <PriorityMatrix findings={result.findings} />

      {/* All findings */}
      <FindingsAccordion findings={result.findings} />

      {/* Roadmap */}
      <RoadmapTimeline />

      <p className="text-xs text-white/20 text-center pb-8">
        Methodology: Metehan Yesilyurt / AEOVision research-first framework
      </p>
    </div>
  );
}
