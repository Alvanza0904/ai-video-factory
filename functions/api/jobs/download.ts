import { Env, json, verifyJobSignature } from "../_shared";

export const onRequestGet: PagesFunction<Env> = async ({ request, env }) => {
  const url = new URL(request.url);
  const jobId = url.searchParams.get("job_id") || "";
  const userId = url.searchParams.get("user_id") || "";
  const expires = url.searchParams.get("expires") || "";
  const signature = url.searchParams.get("signature") || "";
  const key = url.searchParams.get("key") || "";
  if (!jobId || !userId || !key || !(await verifyJobSignature(env, jobId, userId, expires, signature))) return json({ error: "Tautan unduhan tidak valid atau kedaluwarsa." }, 403);
  if (!key.startsWith(`users/${userId}/projects/`) || key.includes("..")) return json({ error: "Lokasi file tidak valid." }, 400);
  const object = await env.MEDIA_BUCKET.get(key);
  if (!object) return json({ error: "Footage tidak ditemukan di penyimpanan." }, 404);
  const headers = new Headers();
  object.writeHttpMetadata(headers);
  headers.set("Content-Length", String(object.size));
  headers.set("Cache-Control", "private, no-store");
  headers.set("Content-Disposition", 'attachment; filename="' + (object.httpMetadata?.contentDisposition || "source-video").replace(/["\r\n]/g, "") + '"');
  return new Response(object.body, { headers });
};
