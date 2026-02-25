import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const ROADMAP = {
  "30 Days": {
    label: "Foundation",
    items: [
      "Fix all CRITICAL findings immediately (canonical, H1, noindex, robots.txt LLM access)",
      "Add JSON-LD structured data: Organization + WebSite + page-specific types",
      "Optimize og:image (1200px+) and all OG tags for Discover eligibility",
      "Add viewport meta tag and audit Core Web Vitals via PageSpeed Insights",
      "Create/fix sitemap.xml and submit to Google Search Console",
      "Add llms.txt at domain root",
    ],
  },
  "60 Days": {
    label: "Content Architecture",
    items: [
      "Re-chunk all pages: ensure each section is 150-375 words under a clear H2/H3",
      "Generate 8-10 sub-queries per content page; add sections for uncovered queries",
      "Add attribution patterns ('according to...', 'research shows...') every 2-3 claims",
      "Add explicit entity declarations ('[Brand] is...', '[Brand] provides...')",
      "Improve token efficiency: replace markdown tables with prose, use numerals",
      "Add FAQPage schema to all informational pages",
    ],
  },
  "90 Days": {
    label: "Authority & AI Visibility",
    items: [
      "Establish entity presence: GitHub, LinkedIn, YouTube, Product Hunt, Wikipedia (if notable)",
      "Acquire high-Harmonic-Centrality backlinks (WordPress.org plugin, GitHub repos, podcasts)",
      "Check CC Rank at webgraph.metehan.ai vs competitors — target <1M rank",
      "Run manual LLM citation audit: test in ChatGPT, Perplexity, Gemini for your key queries",
      "Map GSC queries to conversational prompts; track AI vs Google visibility gap",
      "Implement Discover freshness strategy: 7-day content publication cadence",
    ],
  },
};

export function RoadmapTimeline() {
  return (
    <div className="glass-card p-4">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-white/80">30/60/90 Day Roadmap</h3>
        <p className="text-xs text-white/30">Path to #1 + LLM citations</p>
      </div>
      <Tabs defaultValue="30 Days">
        <TabsList className="bg-white/5 border border-white/8 h-9 mb-4">
          {Object.keys(ROADMAP).map((tab) => (
            <TabsTrigger
              key={tab}
              value={tab}
              className="text-xs data-[state=active]:bg-indigo-600 data-[state=active]:text-white text-white/50"
            >
              {tab}
            </TabsTrigger>
          ))}
        </TabsList>
        {Object.entries(ROADMAP).map(([tab, { label, items }]) => (
          <TabsContent key={tab} value={tab} className="mt-0">
            <p className="text-xs font-medium text-indigo-400 mb-3 uppercase tracking-wider">{label}</p>
            <div className="space-y-2.5">
              {items.map((item, i) => (
                <div key={i} className="flex gap-3 text-sm">
                  <div className="w-5 h-5 rounded-full bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center shrink-0 mt-0.5">
                    <span className="text-indigo-400 text-xs font-bold">{i + 1}</span>
                  </div>
                  <p className="text-white/70 leading-snug">{item}</p>
                </div>
              ))}
            </div>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
