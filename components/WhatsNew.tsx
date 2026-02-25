"use client";

import { useEffect, useState } from "react";
import { Update } from "@/app/api/cron/check-posts/route";

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const days = Math.floor(diff / 86400000);
  if (days === 0) return "today";
  if (days === 1) return "yesterday";
  return `${days}d ago`;
}

export function WhatsNew() {
  const [updates, setUpdates] = useState<Update[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    fetch("/api/whats-new")
      .then((r) => r.json())
      .then((d) => {
        setUpdates(d.updates ?? []);
        setLoaded(true);
      })
      .catch(() => setLoaded(true));
  }, []);

  if (!loaded || !updates.length) return null;

  return (
    <section className="max-w-5xl mx-auto px-4 pb-16 fade-up">
      <div className="mb-5 flex items-center gap-3">
        <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
        <h2 className="text-base font-semibold text-white/80">
          What&apos;s New from Metehan
        </h2>
        <span className="text-xs text-white/25 ml-auto">
          Auto-updated from metehan.ai
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {updates.map((u, i) => (
          <div
            key={i}
            className="glass-card p-4 border-l-2 border-l-indigo-500 hover:border-l-indigo-400 transition-colors"
          >
            <div className="flex items-start justify-between gap-3 mb-3">
              <a
                href={u.postUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="font-semibold text-sm text-white hover:text-indigo-400 transition-colors leading-snug"
              >
                {u.postTitle}
              </a>
              <span className="text-xs text-white/25 shrink-0 mt-0.5">
                {timeAgo(u.detectedAt)}
              </span>
            </div>

            <ul className="space-y-1.5">
              {u.insights.map((insight, j) => (
                <li key={j} className="flex gap-2 text-xs text-white/55 leading-relaxed">
                  <span className="text-indigo-400 shrink-0 mt-0.5">→</span>
                  {insight}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}
