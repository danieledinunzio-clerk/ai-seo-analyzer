"use client";

import { Progress } from "@/components/ui/progress";
import { ProgressStep } from "@/lib/types";
import { cn } from "@/lib/utils";

// Total expected stages (domain, robots, sitemap, agent_files, pages x ~3, internal_links, complete)
const TOTAL_STAGES = 9;

interface ProgressStreamProps {
  steps: ProgressStep[];
  currentStage: string;
}

export function ProgressStream({ steps, currentStage }: ProgressStreamProps) {
  const progress = Math.min(100, Math.round((steps.length / TOTAL_STAGES) * 100));

  return (
    <div className="w-full max-w-lg mx-auto space-y-4">
      <Progress value={progress} className="h-1.5 bg-white/10 [&>div]:bg-indigo-500" />

      <div className="space-y-2">
        {steps.map((step, i) => (
          <div key={i} className="flex items-center gap-3 text-sm">
            <span className="w-5 h-5 rounded-full bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center shrink-0">
              <svg className="w-3 h-3 text-indigo-400" fill="none" viewBox="0 0 12 12">
                <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </span>
            <span className="text-white/60 truncate">{step.label}</span>
          </div>
        ))}

        {currentStage && steps.length < TOTAL_STAGES && (
          <div className="flex items-center gap-3 text-sm">
            <span className="w-5 h-5 rounded-full bg-indigo-500/30 border border-indigo-500 flex items-center justify-center shrink-0 pulse-glow">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
            </span>
            <span className="text-white/80 truncate">{currentStage}</span>
          </div>
        )}
      </div>
    </div>
  );
}
