export interface Env {
  MEDIA_BUCKET: R2Bucket;
  NEXT_PUBLIC_SUPABASE_URL: string;
  NEXT_PUBLIC_SUPABASE_ANON_KEY: string;
}
export async function userFrom(request: Request, env: Env) {
  const token = request.headers.get("Authorization")?.replace(/^Bearer\s+/i, "");
  if (!token) return null;
  const response = await fetch(env.NEXT_PUBLIC_SUPABASE_URL + "/auth/v1/user", { headers: { apikey: env.NEXT_PUBLIC_SUPABASE_ANON_KEY, Authorization: "Bearer " + token } });
  if (!response.ok) return null;
  return await response.json() as { id: string; email?: string };
}
export async function supabase(request: Request, env: Env, path: string, init: RequestInit = {}) {
  const token = request.headers.get("Authorization") || "";
  return fetch(env.NEXT_PUBLIC_SUPABASE_URL + path, { ...init, headers: { apikey: env.NEXT_PUBLIC_SUPABASE_ANON_KEY, Authorization: token, ...(init.headers || {}) } });
}
export function json(data: unknown, status = 200) { return new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } }); }
