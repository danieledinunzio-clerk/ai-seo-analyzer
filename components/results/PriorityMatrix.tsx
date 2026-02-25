import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Finding } from "@/lib/types";
import { SeverityBadge } from "@/components/shared/SeverityBadge";
import { LayerBadge } from "@/components/shared/LayerBadge";

const IMPACT_ORDER: Record<Finding["impact"], number> = { HIGH: 0, MEDIUM: 1, LOW: 2 };
const EFFORT_ORDER: Record<Finding["effort"], number> = { LOW: 0, MEDIUM: 1, HIGH: 2 };

const EFFORT_STYLES: Record<Finding["effort"], string> = {
  LOW: "text-emerald-400",
  MEDIUM: "text-amber-400",
  HIGH: "text-red-400",
};

const IMPACT_STYLES: Record<Finding["impact"], string> = {
  HIGH: "text-red-400",
  MEDIUM: "text-amber-400",
  LOW: "text-white/30",
};

interface PriorityMatrixProps {
  findings: Finding[];
}

export function PriorityMatrix({ findings }: PriorityMatrixProps) {
  const actionable = findings
    .filter((f) => f.severity === "CRITICAL" || f.severity === "WARNING")
    .sort((a, b) => {
      const impactDiff = IMPACT_ORDER[a.impact] - IMPACT_ORDER[b.impact];
      if (impactDiff !== 0) return impactDiff;
      const effortDiff = EFFORT_ORDER[a.effort] - EFFORT_ORDER[b.effort];
      if (effortDiff !== 0) return effortDiff;
      return 0;
    })
    .slice(0, 20);

  if (!actionable.length) return null;

  return (
    <div className="glass-card overflow-hidden">
      <div className="px-4 pt-4 pb-2">
        <h3 className="text-sm font-semibold text-white/80">Priority Action Matrix</h3>
        <p className="text-xs text-white/30">Top {actionable.length} actions ranked by Impact then Effort</p>
      </div>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="border-white/8 hover:bg-transparent">
              <TableHead className="text-white/40 text-xs w-8">#</TableHead>
              <TableHead className="text-white/40 text-xs">Priority</TableHead>
              <TableHead className="text-white/40 text-xs">Layer</TableHead>
              <TableHead className="text-white/40 text-xs">Finding</TableHead>
              <TableHead className="text-white/40 text-xs text-center">Effort</TableHead>
              <TableHead className="text-white/40 text-xs text-center">Impact</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {actionable.map((f, i) => (
              <TableRow key={i} className="border-white/5 hover:bg-white/3 align-top">
                <TableCell className="text-white/30 text-xs">{i + 1}</TableCell>
                <TableCell className="py-2">
                  <SeverityBadge severity={f.severity} />
                </TableCell>
                <TableCell className="py-2">
                  <LayerBadge layer={f.layer} />
                </TableCell>
                <TableCell className="text-xs text-white/70 max-w-[280px] py-2">
                  {f.title.length > 60 ? f.title.slice(0, 58) + "…" : f.title}
                </TableCell>
                <TableCell className={`text-xs text-center font-semibold ${EFFORT_STYLES[f.effort]}`}>
                  {f.effort}
                </TableCell>
                <TableCell className={`text-xs text-center font-semibold ${IMPACT_STYLES[f.impact]}`}>
                  {f.impact}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
