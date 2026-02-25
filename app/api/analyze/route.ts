import { spawn } from "child_process";
import path from "path";

export const runtime = "nodejs";

const SCRIPT_PATH =
  process.env.SEO_SCRIPT_PATH ||
  path.join("/Users/danieledinunzio/Documents/AI SEO", "seo_analyzer.py");

export async function POST(request: Request) {
  const { url, maxPages = 5 } = await request.json();

  if (!url) {
    return new Response(JSON.stringify({ error: "url is required" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    start(controller) {
      const pythonBin = process.env.PYTHON_BIN || "/usr/bin/python3";
      const child = spawn(pythonBin, [
        SCRIPT_PATH,
        url,
        String(maxPages),
        "--json",
      ]);

      let buffer = "";

      child.stdout.on("data", (chunk: Buffer) => {
        buffer += chunk.toString();
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;
          try {
            JSON.parse(trimmed); // validate
            controller.enqueue(encoder.encode(`data: ${trimmed}\n\n`));
          } catch {
            // skip non-JSON lines
          }
        }
      });

      child.stderr.on("data", () => {
        // Rich output goes to stderr in JSON mode — ignore
      });

      child.on("close", () => {
        // Flush remaining buffer
        if (buffer.trim()) {
          try {
            JSON.parse(buffer.trim());
            controller.enqueue(
              encoder.encode(`data: ${buffer.trim()}\n\n`)
            );
          } catch {
            // skip
          }
        }
        controller.enqueue(encoder.encode("data: [DONE]\n\n"));
        controller.close();
      });

      child.on("error", (err: Error) => {
        const errEvent = JSON.stringify({ type: "error", message: err.message });
        controller.enqueue(encoder.encode(`data: ${errEvent}\n\n`));
        controller.close();
      });
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
