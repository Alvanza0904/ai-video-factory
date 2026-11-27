import { Env, json, verifyJobSignature } from "../_shared";

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

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  const url = new URL(request.url);
  const jobId = url.searchParams.get("job_id") || "";
  const userId = url.searchParams.get("user_id") || "";
  const expires = url.searchParams.get("expires") || "";
  const signature = url.searchParams.get("signature") || "";

  if (!jobId || !userId || !(await verifyJobSignature(env, jobId, userId, expires, signature))) {
    return json({ error: "Izin unggah video tidak valid atau kedaluwarsa." }, 403);
  }
  if (!request.body) return json({ error: "File video kosong." }, 400);
  const contentType = request.headers.get("Content-Type") || "";
  if (!contentType.toLowerCase().startsWith("video/mp4")) {
    return json({ error: "Format hasil render harus MP4." }, 415);
  }
  const contentLength = Number(request.headers.get("Content-Length") || 0);
  if (contentLength > 512 * 1024 * 1024) return json({ error: "Ukuran video melebihi batas 512 MB." }, 413);

  const key = `users/${userId}/renders/${jobId}.mp4`;
  const stored = await env.MEDIA_BUCKET.put(key, request.body, {
    httpMetadata: {
      contentType: "video/mp4",
      contentDisposition: `inline; filename="animated-video-${jobId}.mp4"`
    },
    customMetadata: { jobId, userId, uploadedAt: new Date().toISOString() }
  });
  return json({ success: true, key, size: stored.size, etag: stored.etag });
};

export const onRequestGet: PagesFunction<Env> = async ({ request, env }) => {
  const url = new URL(request.url);
  const jobId = url.searchParams.get("job_id") || "";
  const userId = url.searchParams.get("user_id") || "";
  const expires = url.searchParams.get("expires") || "";
  const signature = url.searchParams.get("signature") || "";
  if (!jobId || !userId || !(await verifyJobSignature(env, jobId, userId, expires, signature))) {
    return json({ error: "Tautan pemutaran tidak valid atau kedaluwarsa." }, 403);
  }
  // The HMAC signature already authorizes this exact user/job pair.
  // Do not require a browser Authorization header here: native <video> and
  // download navigations cannot reliably attach the Supabase bearer token.
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
  const download = url.searchParams.get("download") === "1";
  headers.set("Content-Disposition", `${download ? "attachment" : "inline"}; filename="ai-video-factory-${jobId}.mp4"`);
  headers.set("X-Content-Type-Options", "nosniff");
  if (range) {
    headers.set("Content-Length", String(range.length));
    headers.set("Content-Range", `bytes ${range.offset}-${range.offset + range.length - 1}/${head.size}`);
    return new Response(object.body, { status: 206, headers });
  }
  headers.set("Content-Length", String(head.size));
  return new Response(object.body, { status: 200, headers });
};
