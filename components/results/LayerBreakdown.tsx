import { GlassCard } from "@/components/shared/GlassCard";
import { LayerSummary } from "@/lib/types";

interface LayerBreakdownProps {
  layerSummary: LayerSummary;
}

export function LayerBreakdown({ layerSummary }: LayerBreakdownProps) {
  const { traditional_issues, ai_issues, traditional_total, ai_total } = layerSummary;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <GlassCard className="border-indigo-500/20">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/15 flex items-center justify-center shrink-0">
            <span className="text-indigo-400 text-sm font-bold">L1</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-white text-sm">Traditional Search</p>
            <p className="text-xs text-white/40 mb-2">Google / Bing</p>
            <div className="flex items-baseline gap-1.5">
              <span className={`text-2xl font-bold ${traditional_issues > 0 ? "text-red-400" : "text-emerald-400"}`}>
                {traditional_issues}
              </span>
              <span className="text-white/40 text-sm">/ {traditional_total} issues requiring action</span>
            </div>
          </div>
        </div>
      </GlassCard>

      <GlassCard className="border-purple-500/20">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-purple-500/15 flex items-center justify-center shrink-0">
            <span className="text-purple-400 text-sm font-bold">L2</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-white text-sm">AI Search</p>
            <p className="text-xs text-white/40 mb-2">ChatGPT / Perplexity / Gemini</p>
            <div className="flex items-baseline gap-1.5">
              <span className={`text-2xl font-bold ${ai_issues > 0 ? "text-red-400" : "text-emerald-400"}`}>
                {ai_issues}
              </span>
              <span className="text-white/40 text-sm">/ {ai_total} issues requiring action</span>
            </div>
          </div>
        </div>
      </GlassCard>
    </div>
  );
}
