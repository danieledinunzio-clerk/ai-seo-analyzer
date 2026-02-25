"use client";

import { UrlInputForm } from "./UrlInputForm";
import { ProgressStream } from "@/components/shared/ProgressStream";
import { ProgressStep } from "@/lib/types";

interface HeroSectionProps {
  onAnalyze: (url: string, maxPages: number) => void;
  loading: boolean;
  progressSteps: ProgressStep[];
  currentStage: string;
}

export function HeroSection({
  onAnalyze,
  loading,
  progressSteps,
  currentStage,
}: HeroSectionProps) {
  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center hero-grid overflow-hidden px-4">
      {/* Radial glow */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 80% 60% at 50% 0%, rgba(99,102,241,0.12) 0%, transparent 70%)",
        }}
      />

      <div className="relative z-10 flex flex-col items-center gap-6 text-center max-w-4xl w-full">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-medium mb-2">
          <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
          AI-Era SEO Analyzer — Layer 1 + Layer 2
        </div>

        <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight leading-none">
          <span className="gradient-text">Audit Your Site</span>
          <br />
          <span className="text-white/90">for AI Search</span>
        </h1>

        <p className="text-lg text-white/50 max-w-xl leading-relaxed">
          Dual-layer analysis covering traditional Google/Bing signals and AI
          search visibility for ChatGPT, Perplexity, and Gemini.
        </p>

        <UrlInputForm onAnalyze={onAnalyze} loading={loading} />

        {loading && (
          <div className="w-full pt-6 fade-up">
            <ProgressStream steps={progressSteps} currentStage={currentStage} />
          </div>
        )}
      </div>
    </section>
  );
}
