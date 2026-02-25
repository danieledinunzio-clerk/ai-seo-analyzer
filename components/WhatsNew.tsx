"use client";

import { useEffect, useState } from "react";

interface Post {
  url: string;
  lastmod: string;
  title: string;
}

async function fetchLatestPosts(): Promise<Post[]> {
  const res = await fetch(
    "https://metehan.ai/post-sitemap.xml",
    { cache: "no-store" }
  );
  const xml = await res.text();

  const posts: Omit<Post, "title">[] = [];
  for (const match of xml.matchAll(/<url>([\s\S]*?)<\/url>/g)) {
    const loc = match[1].match(/<loc>(.*?)<\/loc>/)?.[1]?.trim();
    const lastmod = match[1].match(/<lastmod>(.*?)<\/lastmod>/)?.[1]?.trim();
    if (loc && lastmod && !loc.includes("/tr/")) {
      posts.push({ url: loc, lastmod });
    }
  }

  const sorted = posts
    .sort((a, b) => b.lastmod.localeCompare(a.lastmod))
    .slice(0, 5);

  // Extract titles from slugs
  return sorted.map((p) => ({
    ...p,
    title: p.url
      .replace(/\/$/, "")
      .split("/")
      .pop()!
      .replace(/-/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase()),
  }));
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function WhatsNew() {
  const [posts, setPosts] = useState<Post[]>([]);

  useEffect(() => {
    fetchLatestPosts().then(setPosts).catch(() => {});
  }, []);

  if (!posts.length) return null;

  return (
    <section className="max-w-5xl mx-auto px-4 pb-16 fade-up">
      <div className="mb-5 flex items-center gap-3">
        <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
        <h2 className="text-sm font-semibold text-white/60 uppercase tracking-wider">
          Latest from Metehan Yesilyurt
        </h2>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {posts.map((p, i) => (
          <a
            key={i}
            href={p.url}
            target="_blank"
            rel="noopener noreferrer"
            className="glass-card p-4 group hover:border-indigo-500/30 transition-all"
          >
            <p className="text-sm font-medium text-white/80 group-hover:text-white leading-snug mb-2 transition-colors">
              {p.title}
            </p>
            <p className="text-xs text-white/30">{formatDate(p.lastmod)}</p>
          </a>
        ))}
      </div>
    </section>
  );
}
