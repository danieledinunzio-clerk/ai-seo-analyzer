import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { Finding } from "@/lib/types";

const SEVERITY_STYLES: Record<Finding["severity"], string> = {
  CRITICAL: "bg-red-500/15 text-red-400 border-red-500/30",
  WARNING: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  INFO: "bg-cyan-500/15 text-cyan-400 border-cyan-500/30",
  PASS: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
};

interface SeverityBadgeProps {
  severity: Finding["severity"];
  className?: string;
}

export function SeverityBadge({ severity, className }: SeverityBadgeProps) {
  return (
    <Badge
      variant="outline"
      className={cn(
        "text-xs font-semibold px-2 py-0.5 shrink-0",
        SEVERITY_STYLES[severity],
        className
      )}
    >
      {severity}
    </Badge>
  );
}
