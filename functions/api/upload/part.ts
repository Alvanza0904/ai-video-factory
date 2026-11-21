import { Env, json, userFrom } from "../_shared";
export const onRequestPut: PagesFunction<Env> = async ({ request, env }) => {
  const user = await userFrom(request, env); if (!user) return json({ error: "Sesi tidak valid." }, 401);
  const url = new URL(request.url); const key = url.searchParams.get("key") || ""; const uploadId = url.searchParams.get("uploadId") || ""; const partNumber = Number(url.searchParams.get("partNumber"));
  if (!key.startsWith(`users/${user.id}/`) || !uploadId || !Number.isInteger(partNumber) || partNumber < 1 || partNumber > 10000) return json({ error: "Parameter upload tidak valid." }, 400);
  const part = await env.MEDIA_BUCKET.resumeMultipartUpload(key, uploadId).uploadPart(partNumber, request.body!);
  return json({ etag: part.etag });
};
