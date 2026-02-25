import { Finding } from "@/lib/types";
import { SeverityBadge } from "@/components/shared/SeverityBadge";
import { LayerBadge } from "@/components/shared/LayerBadge";

const EFFORT_COLORS: Record<Finding["effort"], string> = {
  LOW: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  MEDIUM: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  HIGH: "text-red-400 bg-red-500/10 border-red-500/20",
};

const IMPACT_COLORS: Record<Finding["impact"], string> = {
  HIGH: "text-red-400 bg-red-500/10 border-red-500/20",
  MEDIUM: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  LOW: "text-white/30 bg-white/5 border-white/10",
};

interface FindingRowProps {
  finding: Finding;
}

export function FindingRow({ finding }: FindingRowProps) {
  return (
    <div className="py-3 px-4 border-b border-white/5 last:border-0 hover:bg-white/2 transition-colors">
      <div className="flex flex-wrap items-start gap-2 mb-1.5">
        <SeverityBadge severity={finding.severity} />
        <LayerBadge layer={finding.layer} />
        <p className="font-semibold text-sm text-white leading-snug flex-1 min-w-0">{finding.title}</p>
      </div>
      {finding.detail && (
        <p className="text-xs text-white/40 mb-1.5 leading-relaxed pl-0.5">{finding.detail}</p>
      )}
      <p className="text-xs text-indigo-400/80 italic mb-2 pl-0.5">&rarr; {finding.action}</p>
      <div className="flex gap-2">
        <span className={`text-xs px-2 py-0.5 rounded border font-medium ${EFFORT_COLORS[finding.effort]}`}>
          Effort: {finding.effort}
        </span>
        <span className={`text-xs px-2 py-0.5 rounded border font-medium ${IMPACT_COLORS[finding.impact]}`}>
          Impact: {finding.impact}
        </span>
      </div>
    </div>
  );
}
