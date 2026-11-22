import { Env, dispatchToken, json, supabase, userFrom } from "../_shared";

const REPO = "Alvanza0904/ai-video-factory";
const API = "https://api.github.com";

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  const user = await userFrom(request, env);
  if (!user) return json({ error: "Sesi tidak valid. Silakan masuk kembali." }, 401);
  const token = dispatchToken(env);
  if (!token) return json({ error: "Koneksi GitHub belum siap." }, 503);

  const body = await request.json() as { jobId?: string };
  const jobId = (body.jobId || "").trim();
  if (!/^[0-9a-f]{8}-[0-9a-f-]{27,}$/i.test(jobId)) return json({ error: "ID proses tidak valid." }, 400);

  const jobRes = await supabase(request, env,
    `/rest/v1/editing_jobs?id=eq.${encodeURIComponent(jobId)}&user_id=eq.${encodeURIComponent(user.id)}&select=id,status`);
  const jobs = await jobRes.json() as Array<{ id: string; status: string }>;
  if (!jobRes.ok || !jobs.length) return json({ error: "Proses tidak ditemukan." }, 404);
  if (["completed", "failed", "cancelled"].includes(jobs[0].status)) {
    return json({ success: true, status: jobs[0].status, alreadyFinished: true });
  }

  const headers = {
    Authorization: "Bearer " + token,
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "AI-Video-Factory"
  };
  const list = await fetch(`${API}/repos/${REPO}/actions/workflows/ai-edit.yml/runs?per_page=100&event=workflow_dispatch`, { headers });
  if (!list.ok) return json({ error: "Tidak dapat memeriksa proses GitHub. Coba lagi." }, 502);
  const payload = await list.json() as { workflow_runs?: Array<{ id: number; display_title?: string; status?: string }> };
  const run = (payload.workflow_runs || []).find(item =>
    (item.display_title || "").includes(jobId) &&
    ["queued", "in_progress", "waiting", "requested", "pending"].includes(item.status || "")
  );
  if (!run) return json({ error: "Workflow belum ditemukan atau sudah berhenti. Muat ulang daftar proses lalu coba lagi." }, 409);

  const stopped = await fetch(`${API}/repos/${REPO}/actions/runs/${run.id}/cancel`, {
    method: "POST", headers
  });
  if (!stopped.ok && stopped.status !== 409) {
    return json({ error: "GitHub belum dapat menghentikan proses (HTTP " + stopped.status + ")." }, 502);
  }

  const update = await supabase(request, env,
    `/rest/v1/editing_jobs?id=eq.${encodeURIComponent(jobId)}&user_id=eq.${encodeURIComponent(user.id)}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Prefer: "return=minimal" },
      body: JSON.stringify({ status: "cancelled", progress: 0, error_message: "Dibatalkan oleh pengguna." })
    });
  if (!update.ok) return json({ error: "Workflow dihentikan, tetapi status database belum berhasil diperbarui. Muat ulang beberapa saat lagi." }, 502);
  return json({ success: true, status: "cancelled" });
};
