export interface Env {
  MEDIA_BUCKET: R2Bucket;
  NEXT_PUBLIC_SUPABASE_URL: string;
  NEXT_PUBLIC_SUPABASE_ANON_KEY: string;
  GH_DISPATCH_TOKEN?: string;
  " GH_DISPATCH_TOKEN"?: string;
}
export async function userFrom(request: Request, env: Env) {
  const authorization = request.headers.get("Authorization") || "";
  const match = authorization.match(/^Bearer\s+(.+)$/i);
  const token = match?.[1]?.trim();
  if (!token) return null;
  const response = await fetch(env.NEXT_PUBLIC_SUPABASE_URL + "/auth/v1/user", {
    headers: { apikey: env.NEXT_PUBLIC_SUPABASE_ANON_KEY, Authorization: "Bearer " + token }
  });
  if (!response.ok) return null;
  return await response.json() as { id: string; email?: string };
}
export async function supabase(request: Request, env: Env, path: string, init: RequestInit = {}) {
  const token = request.headers.get("Authorization") || "";
  return fetch(env.NEXT_PUBLIC_SUPABASE_URL + path, { ...init, headers: { apikey: env.NEXT_PUBLIC_SUPABASE_ANON_KEY, Authorization: token, ...(init.headers || {}) } });
}
export function json(data: unknown, status = 200) { return new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } }); }

/** Read the GitHub dispatch secret even if the dashboard accidentally saved whitespace around its name. */
export function dispatchToken(env: Env): string {
  const bindings = env as unknown as Record<string, unknown>;
  for (const [name, value] of Object.entries(bindings)) {
    if (name.trim() === "GH_DISPATCH_TOKEN" && typeof value === "string" && value.trim()) return value.trim();
  }
  return "";
}
export async function signJob(env: Env, jobId: string, userId: string, expires: string): Promise<string> {
  const secret = dispatchToken(env);
  if (!secret) throw new Error("GH_DISPATCH_TOKEN belum dikonfigurasi.");
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const signature = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(jobId + "|" + userId + "|" + expires));
  return Array.from(new Uint8Array(signature), byte => byte.toString(16).padStart(2, "0")).join("");
}
export async function verifyJobSignature(env: Env, jobId: string, userId: string, expires: string, signature: string): Promise<boolean> {
  if (!dispatchToken(env) || !/^\d{10,}$/.test(expires) || Number(expires) < Math.floor(Date.now() / 1000) || Number(expires) > Math.floor(Date.now() / 1000) + 4 * 60 * 60) return false;
  const expected = await signJob(env, jobId, userId, expires);
  if (expected.length !== signature.length) return false;
  let diff = 0;
  for (let i = 0; i < expected.length; i++) diff |= expected.charCodeAt(i) ^ signature.charCodeAt(i);
  return diff === 0;
}
