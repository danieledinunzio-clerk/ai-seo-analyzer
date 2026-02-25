import { redis } from "@/lib/redis";
import { Update } from "@/app/api/cron/check-posts/route";

export async function GET() {
  try {
    const updates = await redis.lrange<Update>("metehan:updates", 0, 4);
    return Response.json({ updates: updates ?? [] });
  } catch {
    return Response.json({ updates: [] });
  }
}
