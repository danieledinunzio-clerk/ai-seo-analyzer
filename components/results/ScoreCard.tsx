"use client";

import { useEffect, useRef } from "react";
import { GlassCard } from "@/components/shared/GlassCard";

const RADIUS = 54;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

function scoreColor(score: number) {
  if (score < 50) return "#ef4444"; // red-500
  if (score < 75) return "#f59e0b"; // amber-500
  return "#10b981"; // emerald-500
}

interface ScoreCardProps {
  score: number;
  summary: {
    critical: number;
    warning: number;
    info: number;
    passing: number;
  };
  domain: string;
  pagesAnalyzed: number;
}

export function ScoreCard({ score, summary, domain, pagesAnalyzed }: ScoreCardProps) {
  const circleRef = useRef<SVGCircleElement>(null);
  const color = scoreColor(score);

  useEffect(() => {
    if (!circleRef.current) return;
    // Start fully offset (empty arc), then animate to score position
    const offset = CIRCUMFERENCE - (score / 100) * CIRCUMFERENCE;
    circleRef.current.style.transition = "stroke-dashoffset 1.5s ease-out";
    circleRef.current.style.strokeDashoffset = String(offset);
  }, [score]);

  return (
    <div className="gradient-border">
      <GlassCard className="flex flex-col sm:flex-row items-center gap-8 p-6">
        {/* SVG gauge */}
        <div className="relative shrink-0">
          <svg width="140" height="140" className="-rotate-90">
            {/* Track */}
            <circle
              cx="70"
              cy="70"
              r={RADIUS}
              fill="none"
              stroke="rgba(255,255,255,0.06)"
              strokeWidth="10"
            />
            {/* Arc */}
            <circle
              ref={circleRef}
              cx="70"
              cy="70"
              r={RADIUS}
              fill="none"
              stroke={color}
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={CIRCUMFERENCE}
              strokeDashoffset={CIRCUMFERENCE}
              style={{ filter: `drop-shadow(0 0 8px ${color}80)` }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center rotate-0">
            <span className="text-3xl font-bold" style={{ color }}>
              {score}
            </span>
            <span className="text-xs text-white/40">/ 100</span>
          </div>
        </div>

        {/* Stats */}
        <div className="flex-1 space-y-3">
          <div>
            <p className="text-lg font-semibold text-white truncate">{domain}</p>
            <p className="text-sm text-white/40">{pagesAnalyzed} page{pagesAnalyzed !== 1 ? "s" : ""} analyzed</p>
          </div>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-red-500" />
              <span className="text-white/60">Critical</span>
              <span className="ml-auto font-semibold text-red-400">{summary.critical}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-amber-500" />
              <span className="text-white/60">Warning</span>
              <span className="ml-auto font-semibold text-amber-400">{summary.warning}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-500" />
              <span className="text-white/60">Info</span>
              <span className="ml-auto font-semibold text-cyan-400">{summary.info}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span className="text-white/60">Passing</span>
              <span className="ml-auto font-semibold text-emerald-400">{summary.passing}</span>
            </div>
          </div>
        </div>
      </GlassCard>
    </div>
  );
}
