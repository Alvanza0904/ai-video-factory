import { Env, json, supabase, userFrom, verifyJobSignature } from "../_shared";

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  const url = new URL(request.url);
  const jobId = url.searchParams.get("job_id") || "";
  const userId = url.searchParams.get("user_id") || "";
  const expires = url.searchParams.get("expires") || "";
  const signature = url.searchParams.get("signature") || "";
  if (!jobId || !userId || !(await verifyJobSignature(env, jobId, userId, expires, signature))) return json({ error: "Izin upload hasil render tidak valid." }, 403);
  const contentLength = Number(request.headers.get("Content-Length") || 0);
  if (contentLength <= 0 || contentLength > 95 * 1024 * 1024) return json({ error: "Ukuran hasil render harus di antara 1 byte dan 95 MB." }, 413);
  const key = `users/${userId}/renders/${jobId}.mp4`;
  await env.MEDIA_BUCKET.put(key, request.body, { httpMetadata: { contentType: "video/mp4", contentDisposition: 'inline; filename="ai-video-factory-' + jobId + '.mp4"' }, customMetadata: { jobId, userId } });
  return json({ success: true, key });
};

export const onRequestGet: PagesFunction<Env> = async ({ request, env }) => {
  const user = await userFrom(request, env);
  if (!user) return json({ error: "Sesi tidak valid." }, 401);
  const jobId = new URL(request.url).searchParams.get("job_id") || "";
  const check = await supabase(request, env, `/rest/v1/editing_jobs?id=eq.${encodeURIComponent(jobId)}&user_id=eq.${user.id}&select=id`);
  const rows = await check.json() as unknown[];
  if (!check.ok || !rows.length) return json({ error: "Job tidak ditemukan." }, 404);
  const key = `users/${user.id}/renders/${jobId}.mp4`;
  const object = await env.MEDIA_BUCKET.get(key);
  if (!object) return json({ error: "Video final belum tersedia." }, 404);
  const headers = new Headers();
  object.writeHttpMetadata(headers);
  headers.set("Cache-Control", "private, no-store");
  return new Response(object.body, { headers });
};
