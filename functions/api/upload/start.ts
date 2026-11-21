import { Env, json, supabase, userFrom } from "../_shared";
export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  const user = await userFrom(request, env); if (!user) return json({ error: "Sesi tidak valid. Silakan masuk kembali." }, 401);
  const body = await request.json() as { projectId: string; filename: string; size: number; contentType: string };
  if (!body.projectId || !body.filename || !Number.isFinite(body.size) || body.size <= 0 || body.size > 2_000_000_000) return json({ error: "Data file tidak valid atau melebihi batas 2 GB." }, 400);
  if (!body.contentType?.startsWith("video/")) return json({ error: "Hanya file video yang didukung." }, 400);
  const project = await supabase(request, env, `/rest/v1/video_projects?id=eq.${encodeURIComponent(body.projectId)}&user_id=eq.${user.id}&select=id`);
  const rows = await project.json() as unknown[]; if (!project.ok || !rows.length) return json({ error: "Proyek tidak ditemukan." }, 404);
  const safe = body.filename.replace(/[^a-zA-Z0-9._-]/g, "_").slice(-120);
  const key = `users/${user.id}/projects/${body.projectId}/${crypto.randomUUID()}-${safe}`;
  const upload = await env.MEDIA_BUCKET.createMultipartUpload(key, { httpMetadata: { contentType: body.contentType } });
  const insert = await supabase(request, env, "/rest/v1/media_assets", { method: "POST", headers: { "Content-Type": "application/json", Prefer: "return=representation" }, body: JSON.stringify({ project_id: body.projectId, user_id: user.id, asset_type: "video", original_filename: body.filename, content_type: body.contentType, size_bytes: body.size, r2_key: key, upload_status: "uploading" }) });
  const inserted = await insert.json() as Array<{id:string}>;
  if (!insert.ok || !inserted?.[0]) { await upload.abort(); return json({ error: "Gagal menyimpan metadata file." }, 500); }
  return json({ key, uploadId: upload.uploadId, assetId: inserted[0].id });
};
