import { Env, json, supabase, userFrom } from "../_shared";

export const onRequestGet: PagesFunction<Env> = async ({ request, env }) => {
  const user = await userFrom(request, env);
  if (!user) return json({ error: "Sesi tidak valid." }, 401);
  const jobId = new URL(request.url).searchParams.get("job_id") || "";
  if (!jobId) return json({ error: "Job ID wajib diisi." }, 400);
  const result = await supabase(request, env, `/rest/v1/editing_jobs?id=eq.${encodeURIComponent(jobId)}&user_id=eq.${user.id}&select=id,status,progress,error_message,genre,target_duration,blueprint,created_at`);
  const rows = await result.json() as Array<Record<string, unknown>>;
  if (!result.ok || !rows.length) return json({ error: "Job tidak ditemukan." }, 404);
  const job = rows[0];
  if (job.status !== "completed" && job.status !== "failed") {
    const key = `users/${user.id}/renders/${jobId}.mp4`;
    const object = await env.MEDIA_BUCKET.head(key);
    if (object) {
      const outputRes = await supabase(request, env, "/rest/v1/render_outputs?on_conflict=job_id", {
        method: "POST",
        headers: { "Content-Type": "application/json", Prefer: "resolution=merge-duplicates,return=minimal" },
        body: JSON.stringify({ job_id: jobId, user_id: user.id, r2_key: key, filename: "ai-video-factory-" + jobId + ".mp4", size_bytes: object.size, content_type: "video/mp4", width: 1080, height: 1920 })
      });
      const update = await supabase(request, env, `/rest/v1/editing_jobs?id=eq.${jobId}&user_id=eq.${user.id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: "completed", progress: 100 }) });
      if (outputRes.ok && update.ok) { job.status = "completed"; job.progress = 100; }
    }
  }
  return json({ job, outputUrl: job.status === "completed" ? "/api/jobs/output?job_id=" + encodeURIComponent(jobId) : null });
};
