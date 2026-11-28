import { Env, dispatchToken, json, signJob, supabase, userFrom } from "../_shared";

type Body = { brand?: string; topic?: string; duration?: number; vehicleAssetKey?: string | null };
export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  const user = await userFrom(request, env);
  if (!user) return json({ error: "Sesi tidak valid. Silakan masuk kembali." }, 401);
  const token = dispatchToken(env);
  if (!token) return json({ error: "Koneksi GitHub belum siap. Secret GH_DISPATCH_TOKEN belum tersedia di Cloudflare Pages." }, 503);

  let body: Body;
  try { body = await request.json() as Body; } catch { return json({ error: "Data permintaan tidak valid." }, 400); }
  const brand = body.brand === "OMODA" ? "OMODA" : body.brand === "JAECOO" ? "JAECOO" : "";
  const topic = (body.topic || "").trim().slice(0, 180);
  const duration = Number(body.duration || 45);
  if (!brand || topic.length < 8 || ![30, 45, 60].includes(duration)) {
    return json({ error: "Pilih brand, topik minimal 8 karakter, dan durasi 30/45/60 detik." }, 400);
  }

  const vehicleAssetKey = body.vehicleAssetKey || null;
  if (vehicleAssetKey) {
    if (!vehicleAssetKey.startsWith("vehicle-assets/" + user.id + "/" + brand + "/") || vehicleAssetKey.includes("..")) return json({ error: "Foto kendaraan tidak valid untuk akun atau brand ini." }, 403);
    const asset = await env.MEDIA_BUCKET.head(vehicleAssetKey);
    if (!asset || !["image/jpeg","image/png","image/webp"].includes(asset.httpMetadata?.contentType || "")) return json({ error: "Foto kendaraan tidak ditemukan atau formatnya tidak didukung." }, 404);
  }

  const projectRes = await supabase(request, env, "/rest/v1/video_projects", {
    method: "POST",
    headers: { "Content-Type": "application/json", Prefer: "return=representation" },
    body: JSON.stringify({ user_id: user.id, name: "Education Studio · " + brand, brand: brand + " Palembang" })
  });
  const projects = await projectRes.json() as Array<{ id: string }>;
  if (!projectRes.ok || !projects[0]) return json({ error: "Tidak dapat membuat proyek video edukasi. Periksa akses database." }, 500);
  const projectId = projects[0].id;

  const jobRes = await supabase(request, env, "/rest/v1/editing_jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json", Prefer: "return=representation" },
    body: JSON.stringify({
      project_id: projectId, user_id: user.id, title: "Edukasi " + brand + " · " + topic.slice(0, 70),
      genre: "other", target_duration: duration, aspect_ratio: "9:16",
      instructions: JSON.stringify({ module: "animated_education", brand, topic, style: "explainer_cartoon_motion_graphics", voice: "id_ID-news_tts-medium", vehicleAssetKey }),
      status: "queued", progress: 1
    })
  });
  const jobs = await jobRes.json() as Array<{ id: string }>;
  if (!jobRes.ok || !jobs[0]) return json({ error: "Tidak dapat membuat antrean render video." }, 500);
  const jobId = jobs[0].id;
  const expires = String(Math.floor(Date.now() / 1000) + 2 * 60 * 60);
  const signature = await signJob(env, jobId, user.id, expires);
  const manifest = { jobId, userId: user.id, projectId, expires, signature, brand, topic, duration, vehicleAssetKey, module: "animated_education" };
  await env.MEDIA_BUCKET.put("private-jobs/" + jobId + "/manifest.json", JSON.stringify(manifest), {
    httpMetadata: { contentType: "application/json" }
  });

  const dispatch = await fetch("https://api.github.com/repos/Alvanza0904/ai-video-factory/actions/workflows/education-animation.yml/dispatches", {
    method: "POST",
    headers: { Authorization: "Bearer " + token, Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json", "User-Agent": "AI-Animated-Education-Factory" },
    body: JSON.stringify({ ref: "main", inputs: { job_id: jobId } })
  });
  if (!dispatch.ok) {
    const raw = await dispatch.text();
    let detail = "";
    try { detail = (JSON.parse(raw) as { message?: string }).message || ""; } catch { /* ignore */ }
    const message = "GitHub gagal menerima job animasi (HTTP " + dispatch.status + "). " + detail;
    await env.MEDIA_BUCKET.delete("private-jobs/" + jobId + "/manifest.json");
    await supabase(request, env, "/rest/v1/editing_jobs?id=eq." + jobId, {
      method: "PATCH", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "failed", progress: 0, error_message: message })
    });
    return json({ error: message }, 502);
  }
  await supabase(request, env, "/rest/v1/editing_jobs?id=eq." + jobId, {
    method: "PATCH", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: "analyzing", progress: 5 })
  });
  return json({ success: true, jobId, status: "analyzing" }, 202);
};
