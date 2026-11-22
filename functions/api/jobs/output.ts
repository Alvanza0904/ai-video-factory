import { Env, json, supabase, userFrom, verifyJobSignature } from "../_shared";

function parseRange(value: string | null, size: number): { offset: number; length: number } | null | "invalid" {
  if (!value) return null;
  const match = /^bytes=(\d*)-(\d*)$/.exec(value.trim());
  if (!match || (!match[1] && !match[2])) return "invalid";
  let start: number;
  let end: number;
  if (!match[1]) {
    const suffix = Number(match[2]);
    if (!Number.isSafeInteger(suffix) || suffix <= 0) return "invalid";
    start = Math.max(0, size - suffix);
    end = size - 1;
  } else {
    start = Number(match[1]);
    end = match[2] ? Number(match[2]) : size - 1;
  }
  if (!Number.isSafeInteger(start) || !Number.isSafeInteger(end) || start < 0 || start >= size || end < start) return "invalid";
  end = Math.min(end, size - 1);
  return { offset: start, length: end - start + 1 };
}

export const onRequestGet: PagesFunction<Env> = async ({ request, env }) => {
  const url = new URL(request.url);
  const jobId = url.searchParams.get("job_id") || "";
  const userId = url.searchParams.get("user_id") || "";
  const expires = url.searchParams.get("expires") || "";
  const signature = url.searchParams.get("signature") || "";
  if (!jobId || !userId || !(await verifyJobSignature(env, jobId, userId, expires, signature))) {
    return json({ error: "Tautan pemutaran tidak valid atau kedaluwarsa." }, 403);
  }
  const check = await supabase(request, env, `/rest/v1/editing_jobs?id=eq.${encodeURIComponent(jobId)}&user_id=eq.${encodeURIComponent(userId)}&status=eq.completed&select=id`);
  const rows = await check.json() as unknown[];
  if (!check.ok || !rows.length) return json({ error: "Video tidak ditemukan atau belum selesai." }, 404);

  const key = `users/${userId}/renders/${jobId}.mp4`;
  const head = await env.MEDIA_BUCKET.head(key);
  if (!head) return json({ error: "File video tidak ditemukan di penyimpanan." }, 404);
  const range = parseRange(request.headers.get("Range"), head.size);
  if (range === "invalid") {
    return new Response(null, { status: 416, headers: { "Content-Range": `bytes */${head.size}`, "Accept-Ranges": "bytes" } });
  }
  const object = range
    ? await env.MEDIA_BUCKET.get(key, { range })
    : await env.MEDIA_BUCKET.get(key);
  if (!object) return json({ error: "File video tidak tersedia." }, 404);

  const headers = new Headers();
  object.writeHttpMetadata(headers);
  headers.set("Content-Type", "video/mp4");
  headers.set("Accept-Ranges", "bytes");
  headers.set("Cache-Control", "private, no-store");
  headers.set("Content-Disposition", 'inline; filename="ai-video-factory.mp4"');
  if (range) {
    headers.set("Content-Length", String(range.length));
    headers.set("Content-Range", `bytes ${range.offset}-${range.offset + range.length - 1}/${head.size}`);
    return new Response(object.body, { status: 206, headers });
  }
  headers.set("Content-Length", String(head.size));
  return new Response(object.body, { status: 200, headers });
};
