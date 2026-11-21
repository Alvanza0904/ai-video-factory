import { Env, json, verifyJobSignature } from "../_shared";

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  const url = new URL(request.url);
  const jobId = url.searchParams.get("job_id") || "";
  const userId = url.searchParams.get("user_id") || "";
  const expires = url.searchParams.get("expires") || "";
  const signature = url.searchParams.get("signature") || "";
  if (!jobId || !userId || !(await verifyJobSignature(env, jobId, userId, expires, signature))) return json({ error: "Izin pelaporan job tidak valid." }, 403);
  const body = await request.json() as { message?: string };
  const message = (body.message || "AI editing gagal. Periksa detail proses di GitHub Actions.").slice(0, 500);
  const key = `users/${userId}/renders/${jobId}.failure.json`;
  await env.MEDIA_BUCKET.put(key, JSON.stringify({ message, failedAt: new Date().toISOString() }), { httpMetadata: { contentType: "application/json" }, customMetadata: { jobId, userId } });
  return json({ success: true });
};
