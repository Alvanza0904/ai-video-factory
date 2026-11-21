import { Env, dispatchToken, json, signJob, supabase, userFrom } from "../_shared";

type Asset = { id: string; r2_key: string; original_filename: string; size_bytes: number; content_type: string };
const allowedGenres = ["auto", "cinematic", "drama", "pov", "comedy", "two_character", "review", "mixed", "other"];

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  const user = await userFrom(request, env);
  if (!user) return json({ error: "Sesi tidak valid. Silakan masuk kembali." }, 401);
  const githubToken = dispatchToken(env);
  if (!githubToken) return json({ error: "Koneksi GitHub belum siap. Secret GH_DISPATCH_TOKEN belum ditemukan di Cloudflare Pages." }, 503);

  const body = await request.json() as { projectId: string; assetIds: string[]; genre: string; targetDuration: number; instructions?: string };
  if (!body.projectId || !Array.isArray(body.assetIds) || body.assetIds.length < 1 || body.assetIds.length > 10) return json({ error: "Pilih 1–10 video yang sudah berhasil diunggah." }, 400);
  if (!allowedGenres.includes(body.genre) || ![30, 45, 60].includes(body.targetDuration)) return json({ error: "Pengaturan genre atau durasi tidak valid." }, 400);

  const projectRes = await supabase(request, env, `/rest/v1/video_projects?id=eq.${encodeURIComponent(body.projectId)}&user_id=eq.${user.id}&select=id`);
  const projects = await projectRes.json() as Array<{ id: string }>;
  if (!projectRes.ok || !projects.length) return json({ error: "Proyek tidak ditemukan." }, 404);

  const uniqueIds = [...new Set(body.assetIds)];
  const assetRes = await supabase(request, env, `/rest/v1/media_assets?project_id=eq.${encodeURIComponent(body.projectId)}&user_id=eq.${user.id}&upload_status=eq.uploaded&asset_type=eq.video&select=id,r2_key,original_filename,size_bytes,content_type`);
  const available = await assetRes.json() as Asset[];
  const selected = uniqueIds.map(id => available.find(asset => asset.id === id)).filter((asset): asset is Asset => Boolean(asset));
  if (!assetRes.ok || selected.length !== uniqueIds.length) return json({ error: "Sebagian footage belum selesai diunggah atau bukan milik proyek ini. Muat ulang daftar footage." }, 400);

  const jobRes = await supabase(request, env, "/rest/v1/editing_jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json", Prefer: "return=representation" },
    body: JSON.stringify({ project_id: body.projectId, user_id: user.id, title: "AI Edit " + new Date().toISOString().slice(0, 10), genre: body.genre, target_duration: body.targetDuration, instructions: (body.instructions || "").slice(0, 2000), status: "queued", progress: 1 })
  });
  const jobs = await jobRes.json() as Array<{ id: string }>;
  if (!jobRes.ok || !jobs[0]) return json({ error: "Gagal membuat antrean editing." }, 500);
  const jobId = jobs[0].id;

  const links = await supabase(request, env, "/rest/v1/job_assets", {
    method: "POST",
    headers: { "Content-Type": "application/json", Prefer: "return=minimal" },
    body: JSON.stringify(selected.map((asset, index) => ({ job_id: jobId, asset_id: asset.id, sort_order: index })))
  });
  if (!links.ok) {
    await supabase(request, env, `/rest/v1/editing_jobs?id=eq.${jobId}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: "failed", error_message: "Gagal menghubungkan footage ke job." }) });
    return json({ error: "Gagal menghubungkan footage ke antrean editing." }, 500);
  }

  const expires = String(Math.floor(Date.now() / 1000) + 2 * 60 * 60);
  const signature = await signJob(env, jobId, user.id, expires);
  const manifest = { jobId, userId: user.id, projectId: body.projectId, expires, signature, assets: selected.map(asset => ({ id: asset.id, key: asset.r2_key, filename: asset.original_filename })), targetDuration: body.targetDuration, genre: body.genre, instructions: (body.instructions || "").slice(0, 2000) };
  await env.MEDIA_BUCKET.put(`private-jobs/${jobId}/manifest.json`, JSON.stringify(manifest), { httpMetadata: { contentType: "application/json" } });
  const dispatch = await fetch("https://api.github.com/repos/Alvanza0904/ai-video-factory/actions/workflows/ai-edit.yml/dispatches", {
    method: "POST",
    headers: { Authorization: "Bearer " + githubToken, Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json", "User-Agent": "AI-Video-Factory" },
    body: JSON.stringify({ ref: "main", inputs: { job_id: jobId } })
  });
  if (!dispatch.ok) {
    const raw = await dispatch.text();
    let githubMessage = "";
    try { githubMessage = (JSON.parse(raw) as { message?: string }).message || ""; } catch { /* keep response generic */ }
    let message: string;
    if (dispatch.status === 404) {
      message = "GitHub tidak menemukan workflow AI edit. Pastikan file .github/workflows/ai-edit.yml aktif di branch main.";
    } else if (dispatch.status === 401) {
      message = "GitHub menolak token (401). Token kemungkinan salah, dicabut, atau kedaluwarsa. Perbarui secret GH_DISPATCH_TOKEN di Cloudflare Pages.";
    } else if (dispatch.status === 403) {
      message = "GitHub menolak izin token (403). PAT harus memiliki Repository access ke Alvanza0904/ai-video-factory dan izin Actions: Read and write. Detail GitHub: " + (githubMessage || "Resource not accessible.");
    } else {
      message = "GitHub gagal menerima antrean editing (HTTP " + dispatch.status + "). " + (githubMessage || "");
    }
    await env.MEDIA_BUCKET.delete(`private-jobs/${jobId}/manifest.json`);
    await supabase(request, env, `/rest/v1/editing_jobs?id=eq.${jobId}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: "failed", error_message: message }) });
    return json({ error: message }, 502);
  }
  await supabase(request, env, `/rest/v1/editing_jobs?id=eq.${jobId}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: "analyzing", progress: 5 }) });
  return json({ success: true, jobId, status: "analyzing", selectedAssets: selected.length }, 202);
};
