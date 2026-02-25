"use client";

import { useAnalysis } from "@/hooks/useAnalysis";
import { HeroSection } from "@/components/hero/HeroSection";
import { ResultsDashboard } from "@/components/results/ResultsDashboard";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export default function Home() {
  const { status, progressSteps, currentStage, result, error, analyze, reset } =
    useAnalysis();

  return (
    <main className="min-h-screen">
      {status !== "complete" && (
        <HeroSection
          onAnalyze={analyze}
          loading={status === "loading"}
          progressSteps={progressSteps}
          currentStage={currentStage}
        />
      )}

      {status === "error" && (
        <div className="max-w-2xl mx-auto px-4 py-8">
          <Alert className="bg-red-500/10 border-red-500/30 text-red-400">
            <AlertTitle>Analysis Failed</AlertTitle>
            <AlertDescription className="text-red-400/80">{error}</AlertDescription>
          </Alert>
          <button
            onClick={reset}
            className="mt-4 text-sm text-white/40 hover:text-white/70 underline"
          >
            Try again
          </button>
        </div>
      )}

      {status === "complete" && result && (
        <ResultsDashboard result={result} onReset={reset} />
      )}
    </main>
  );
}
