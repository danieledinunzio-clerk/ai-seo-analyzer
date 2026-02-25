import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { PageSnapshot } from "@/lib/types";

interface PageSnapshotTableProps {
  pages: PageSnapshot[];
  baseUrl: string;
}

export function PageSnapshotTable({ pages, baseUrl }: PageSnapshotTableProps) {
  if (!pages.length) return null;

  function shortUrl(url: string) {
    const path = url.replace(baseUrl, "") || "/";
    return path.length > 40 ? path.slice(0, 38) + "…" : path;
  }

  return (
    <div className="glass-card overflow-hidden">
      <div className="px-4 pt-4 pb-2">
        <h3 className="text-sm font-semibold text-white/80">Page Snapshot</h3>
      </div>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="border-white/8 hover:bg-transparent">
              <TableHead className="text-white/40 text-xs">URL</TableHead>
              <TableHead className="text-white/40 text-xs text-center">Status</TableHead>
              <TableHead className="text-white/40 text-xs text-right">Words</TableHead>
              <TableHead className="text-white/40 text-xs text-right">Tokens</TableHead>
              <TableHead className="text-white/40 text-xs text-right">CPT</TableHead>
              <TableHead className="text-white/40 text-xs text-right">Load</TableHead>
              <TableHead className="text-white/40 text-xs text-center">H1s</TableHead>
              <TableHead className="text-white/40 text-xs text-center">H2s</TableHead>
              <TableHead className="text-white/40 text-xs text-center">Schema</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {pages.map((page, i) => (
              <TableRow key={i} className="border-white/5 hover:bg-white/3">
                <TableCell className="text-white/60 text-xs font-mono max-w-[180px] truncate">
                  {shortUrl(page.url)}
                </TableCell>
                <TableCell className="text-center">
                  <span className={`text-xs font-semibold ${page.status_code === 200 ? "text-emerald-400" : "text-red-400"}`}>
                    {page.status_code}
                  </span>
                </TableCell>
                <TableCell className="text-right text-xs text-white/60">{page.word_count}</TableCell>
                <TableCell className="text-right text-xs text-white/60">{page.token_count}</TableCell>
                <TableCell className="text-right text-xs">
                  <span className={page.chars_per_token >= 5.5 ? "text-emerald-400" : "text-amber-400"}>
                    {page.chars_per_token.toFixed(1)}
                  </span>
                </TableCell>
                <TableCell className="text-right text-xs text-white/60">
                  {page.load_time_ms.toFixed(0)}ms
                </TableCell>
                <TableCell className="text-center text-xs text-white/60">{page.h1_count}</TableCell>
                <TableCell className="text-center text-xs text-white/60">{page.h2_count}</TableCell>
                <TableCell className="text-center text-xs">
                  <span className={page.has_schema ? "text-emerald-400" : "text-red-400"}>
                    {page.has_schema ? "Yes" : "No"}
                  </span>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
