export const runtime = "nodejs";

const PYTHON_API_URL = (
  process.env.PYTHON_API_URL || "http://localhost:8000"
).replace(/\/$/, "");

export async function POST(request: Request) {
  const body = await request.json();

  if (!body.url) {
    return new Response(JSON.stringify({ error: "url is required" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const targetUrl = `${PYTHON_API_URL}/analyze`;
  console.log("[analyze] calling:", targetUrl);

  let upstream: Response;
  try {
    upstream = await fetch(targetUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch (e) {
    console.log("[analyze] fetch error:", e);
    const err = JSON.stringify({ type: "error", message: "Analysis service unavailable" });
    return new Response(`data: ${err}\n\ndata: [DONE]\n\n`, {
      headers: { "Content-Type": "text/event-stream" },
    });
  }

  console.log("[analyze] upstream status:", upstream.status);

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
