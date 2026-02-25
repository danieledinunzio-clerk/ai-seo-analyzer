export const runtime = "nodejs";

const PYTHON_API_URL =
  process.env.PYTHON_API_URL || "http://localhost:8000";

export async function POST(request: Request) {
  const body = await request.json();

  if (!body.url) {
    return new Response(JSON.stringify({ error: "url is required" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${PYTHON_API_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    const err = JSON.stringify({ type: "error", message: "Analysis service unavailable" });
    return new Response(`data: ${err}\n\ndata: [DONE]\n\n`, {
      headers: { "Content-Type": "text/event-stream" },
    });
  }

  if (!upstream.ok || !upstream.body) {
    const err = JSON.stringify({ type: "error", message: `Service error: ${upstream.status}` });
    return new Response(`data: ${err}\n\ndata: [DONE]\n\n`, {
      headers: { "Content-Type": "text/event-stream" },
    });
  }

  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
