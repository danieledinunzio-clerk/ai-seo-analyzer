import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { Finding } from "@/lib/types";

const LAYER_STYLES: Record<Finding["layer"], string> = {
  TRADITIONAL: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
  AI: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  BOTH: "bg-slate-500/10 text-slate-400 border-slate-500/20",
};

interface LayerBadgeProps {
  layer: Finding["layer"];
  className?: string;
}

export function LayerBadge({ layer, className }: LayerBadgeProps) {
  return (
    <Badge
      variant="outline"
      className={cn(
        "text-xs px-2 py-0.5 shrink-0",
        LAYER_STYLES[layer],
        className
      )}
    >
      {layer}
    </Badge>
  );
}
