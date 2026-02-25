"use client";

import { useMemo } from "react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Finding } from "@/lib/types";
import { FindingRow } from "./FindingRow";
import { SeverityBadge } from "@/components/shared/SeverityBadge";

const SEVERITY_ORDER: Record<string, number> = {
  CRITICAL: 0,
  WARNING: 1,
  INFO: 2,
  PASS: 3,
};

function categoryHasCritical(findings: Finding[]) {
  return findings.some((f) => f.severity === "CRITICAL");
}

interface FindingsAccordionProps {
  findings: Finding[];
}

export function FindingsAccordion({ findings }: FindingsAccordionProps) {
  const grouped = useMemo(() => {
    const map: Record<string, Finding[]> = {};
    for (const f of findings) {
      (map[f.category] ??= []).push(f);
    }

    // Sort each category's findings by severity
    for (const cat of Object.keys(map)) {
      map[cat].sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]);
    }

    // Sort categories: ones with CRITICAL first, then alphabetically
    return Object.entries(map).sort(([catA, fA], [catB, fB]) => {
      const aHasCrit = categoryHasCritical(fA) ? 0 : 1;
      const bHasCrit = categoryHasCritical(fB) ? 0 : 1;
      if (aHasCrit !== bHasCrit) return aHasCrit - bHasCrit;
      return catA.localeCompare(catB);
    });
  }, [findings]);

  const defaultOpen = grouped
    .filter(([, f]) => categoryHasCritical(f))
    .slice(0, 3)
    .map(([cat]) => cat);

  return (
    <div className="glass-card overflow-hidden">
      <div className="px-4 pt-4 pb-2">
        <h3 className="text-sm font-semibold text-white/80">All Findings by Category</h3>
        <p className="text-xs text-white/30">{findings.length} total findings</p>
      </div>
      <Accordion type="multiple" defaultValue={defaultOpen} className="px-2 pb-2">
        {grouped.map(([cat, catFindings]) => {
          const counts: Partial<Record<Finding["severity"], number>> = {};
          for (const f of catFindings) {
            counts[f.severity] = (counts[f.severity] ?? 0) + 1;
          }

          return (
            <AccordionItem
              key={cat}
              value={cat}
              className="border-white/8 last:border-0"
            >
              <AccordionTrigger className="hover:no-underline px-2 py-3 text-sm font-medium text-white/80 hover:text-white">
                <div className="flex items-center gap-2 flex-1 min-w-0 mr-2">
                  <span className="truncate">{cat}</span>
                  <div className="flex gap-1 shrink-0 flex-wrap">
                    {(["CRITICAL", "WARNING", "INFO", "PASS"] as Finding["severity"][]).map(
                      (sev) =>
                        counts[sev] ? (
                          <SeverityBadge key={sev} severity={sev} />
                        ) : null
                    )}
                  </div>
                </div>
              </AccordionTrigger>
              <AccordionContent className="pb-0">
                <div className="ml-2 border-l border-white/5">
                  {catFindings.map((f, i) => (
                    <FindingRow key={i} finding={f} />
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>
          );
        })}
      </Accordion>
    </div>
  );
}
