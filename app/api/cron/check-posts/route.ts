import { NextRequest } from "next/server";
import Anthropic from "@anthropic-ai/sdk";
import { redis } from "@/lib/redis";

export const runtime = "nodejs";
export const maxDuration = 60;

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

export interface Update {
  postUrl: string;
  postTitle: string;
  postDate: string;
  insights: string[];
  detectedAt: string;
}

async function fetchSitemap(): Promise<{ url: string; lastmod: string }[]> {
  const res = await fetch("https://metehan.ai/post-sitemap.xml", {
    cache: "no-store",
  });
  const xml = await res.text();

  const posts: { url: string; lastmod: string }[] = [];
  for (const match of xml.matchAll(/<url>([\s\S]*?)<\/url>/g)) {
    const locMatch = match[1].match(/<loc>(.*?)<\/loc>/);
    const lastmodMatch = match[1].match(/<lastmod>(.*?)<\/lastmod>/);
    if (locMatch && lastmodMatch && !locMatch[1].includes("/tr/")) {
      posts.push({ url: locMatch[1].trim(), lastmod: lastmodMatch[1].trim() });
    }
  }

  return posts.sort((a, b) => b.lastmod.localeCompare(a.lastmod));
}

async function fetchPostContent(
  url: string
): Promise<{ title: string; content: string }> {
  const res = await fetch(url, { cache: "no-store" });
  const html = await res.text();

  const titleMatch = html.match(/<title[^>]*>(.*?)<\/title>/i);
  const title = (titleMatch?.[1] ?? url)
    .replace(/\s*[-|]\s*Metehan.*$/i, "")
    .trim();

  const content = html
    .replace(/<script[\s\S]*?<\/script>/gi, "")
    .replace(/<style[\s\S]*?<\/style>/gi, "")
    .replace(/<nav[\s\S]*?<\/nav>/gi, "")
    .replace(/<footer[\s\S]*?<\/footer>/gi, "")
    .replace(/<header[\s\S]*?<\/header>/gi, "")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 5000);

  return { title, content };
}

async function extractInsights(
  title: string,
  content: string
): Promise<string[]> {
  const msg = await anthropic.messages.create({
    model: "claude-haiku-4-5-20251001",
    max_tokens: 600,
    messages: [
      {
        role: "user",
        content: `You are an AI SEO expert. Read this blog post and extract exactly 4 specific, actionable insights for improving AI search visibility. Be concrete — name specific tactics, not vague advice.

Return ONLY a valid JSON array of 4 strings. No other text.

Title: ${title}
Content: ${content}

JSON array:`,
      },
    ],
  });

  const text =
    msg.content[0].type === "text" ? msg.content[0].text.trim() : "";
  try {
    const arr = JSON.parse(text.match(/\[[\s\S]*\]/)?.[0] ?? "[]");
    return Array.isArray(arr) ? arr.slice(0, 4) : [];
  } catch {
    return [];
  }
}

export async function GET(request: NextRequest) {
  // Verify Vercel cron secret
  const authHeader = request.headers.get("authorization");
  if (
    process.env.CRON_SECRET &&
    authHeader !== `Bearer ${process.env.CRON_SECRET}`
  ) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const posts = await fetchSitemap();
    if (!posts.length) {
      return Response.json({ message: "No posts found in sitemap" });
    }

    const latestPost = posts[0];
    const lastSeenUrl = await redis.get<string>("metehan:last_post_url");

    if (lastSeenUrl === latestPost.url) {
      return Response.json({
        message: "No new posts",
        latest: latestPost.url,
      });
    }

    // Find new posts since last seen
    const lastSeenIndex = posts.findIndex((p) => p.url === lastSeenUrl);
    const newPosts =
      lastSeenIndex === -1 ? [posts[0]] : posts.slice(0, lastSeenIndex);

    const processed: Update[] = [];

    for (const post of newPosts.slice(0, 3)) {
      const { title, content } = await fetchPostContent(post.url);
      const insights = await extractInsights(title, content);

      const update: Update = {
        postUrl: post.url,
        postTitle: title,
        postDate: post.lastmod,
        insights,
        detectedAt: new Date().toISOString(),
      };

      await redis.lpush("metehan:updates", update);
      processed.push(update);
    }

    // Keep only last 10 updates
    await redis.ltrim("metehan:updates", 0, 9);

    // Mark latest as seen
    await redis.set("metehan:last_post_url", latestPost.url);

    return Response.json({
      message: `Processed ${processed.length} new post(s)`,
      processed,
    });
  } catch (e) {
    console.error("[cron] error:", e);
    return Response.json({ error: String(e) }, { status: 500 });
  }
}
