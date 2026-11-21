import { Env, json } from "../_shared";

const WORKFLOW_ID = 426064875;

export const onRequestGet: PagesFunction<Env> = async ({ request, env }) => {
  const token = request.headers.get("Authorization")?.replace(/^Bearer\\s+/i, "") || "";
  const url = new URL(request.url);
  const jobId = url.searchParams.get("job_id") || "";
  const runId = url.searchParams.get("run_id") || "";
  if (!token || !/^\\d+$/.test(runId) || !jobId) return json({ error: "Identitas runner tidak lengkap." }, 400);

  const check = await fetch(`https://api.github.com/repos/Alvanza0904/ai-video-factory/actions/runs/${runId}`, {
    headers: { Authorization: "Bearer " + token, Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "AI-Video-Factory" }
  });
  if (!check.ok) return json({ error: "Runner GitHub tidak dapat diverifikasi." }, 403);
  const run = await check.json() as { workflow_id?: number; path?: string; repository?: { full_name?: string } };
  if (run.workflow_id !== WORKFLOW_ID || run.path !== ".github/workflows/ai-edit.yml" || run.repository?.full_name !== "Alvanza0904/ai-video-factory") return json({ error: "Workflow runner tidak diizinkan." }, 403);

  const object = await env.MEDIA_BUCKET.get(`private-jobs/${jobId}/manifest.json`);
  if (!object) return json({ error: "Manifest job tidak ditemukan." }, 404);
  return json(await object.json());
};
