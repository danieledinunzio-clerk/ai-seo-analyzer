import { Finding } from "@/lib/types";
import { SeverityBadge } from "@/components/shared/SeverityBadge";

interface QuickWinsProps {
  findings: Finding[];
}

export function QuickWins({ findings }: QuickWinsProps) {
  const wins = findings
    .filter(
      (f) =>
        f.effort === "LOW" &&
        (f.severity === "CRITICAL" || f.severity === "WARNING")
    )
    .slice(0, 8);

  if (!wins.length) return null;

  return (
    <div className="space-y-3">
      <div>
        <h3 className="text-sm font-semibold text-white/80">Quick Wins</h3>
        <p className="text-xs text-white/30">Low effort, high-medium impact findings</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {wins.map((f, i) => (
          <div
            key={i}
            className="glass-card border-l-2 border-l-emerald-500 pl-3 pr-4 py-3"
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs text-white/40 bg-white/5 px-2 py-0.5 rounded">
                {f.category}
              </span>
              <SeverityBadge severity={f.severity} />
            </div>
            <p className="text-sm font-medium text-white/90 leading-snug mb-1">{f.title}</p>
            <p className="text-xs text-indigo-400/80 italic">&rarr; {f.action}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
