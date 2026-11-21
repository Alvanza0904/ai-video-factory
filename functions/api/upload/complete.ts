import { Env, json, supabase, userFrom } from "../_shared";
type Part = { partNumber: number; etag: string };
export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  const user = await userFrom(request, env); if (!user) return json({ error: "Sesi tidak valid." }, 401);
  const body = await request.json() as { key: string; uploadId: string; parts: Part[]; assetId: string };
  if (!body.key?.startsWith(`users/${user.id}/`) || !body.uploadId || !body.assetId || !Array.isArray(body.parts) || !body.parts.length) return json({ error: "Data penyelesaian upload tidak valid." }, 400);
  const result = await env.MEDIA_BUCKET.resumeMultipartUpload(body.key, body.uploadId).complete(body.parts.map(p => ({ partNumber: p.partNumber, etag: p.etag })));
  const update = await supabase(request, env, `/rest/v1/media_assets?id=eq.${encodeURIComponent(body.assetId)}&user_id=eq.${user.id}`, { method: "PATCH", headers: { "Content-Type": "application/json", Prefer: "return=representation" }, body: JSON.stringify({ upload_status: "uploaded", metadata: { etag: result.etag } }) });
  const rows = await update.json() as unknown[]; if (!update.ok) return json({ error: "Video tersimpan, tetapi metadata gagal diperbarui." }, 500);
  return json({ success: true, asset: rows[0] });
};
