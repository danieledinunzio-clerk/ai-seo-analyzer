"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface UrlInputFormProps {
  onAnalyze: (url: string, maxPages: number) => void;
  loading: boolean;
}

export function UrlInputForm({ onAnalyze, loading }: UrlInputFormProps) {
  const [url, setUrl] = useState("");
  const [maxPages, setMaxPages] = useState(5);
  const [error, setError] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = url.trim();
    if (!trimmed) {
      setError("Please enter a URL");
      return;
    }
    setError("");
    onAnalyze(trimmed, maxPages);
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl space-y-3">
      <div className="flex gap-2">
        <Input
          type="text"
          placeholder="https://example.com"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          disabled={loading}
          className="flex-1 h-12 bg-white/5 border-white/15 text-white placeholder:text-white/30 focus:border-indigo-500 focus:ring-indigo-500/20 text-base"
        />
        <Button
          type="submit"
          disabled={loading}
          className="h-12 px-6 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition-all shrink-0"
        >
          {loading ? "Analyzing..." : "Analyze"}
        </Button>
      </div>

      <div className="flex items-center gap-3">
        <label className="text-sm text-white/40 shrink-0">Max pages:</label>
        <div className="flex gap-2">
          {[3, 5, 10].map((n) => (
            <button
              key={n}
              type="button"
              onClick={() => setMaxPages(n)}
              disabled={loading}
              className={`px-3 py-1 text-sm rounded-full border transition-all ${
                maxPages === n
                  ? "bg-indigo-600/30 border-indigo-500 text-indigo-300"
                  : "bg-white/5 border-white/10 text-white/40 hover:border-white/25"
              }`}
            >
              {n}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}
    </form>
  );
}
