import { Env, json, verifyJobSignature } from "../_shared";
export const onRequestGet: PagesFunction<Env> = async ({request,env}) => {
 const url=new URL(request.url); const jobId=url.searchParams.get("job_id")||""; const userId=url.searchParams.get("user_id")||""; const expires=url.searchParams.get("expires")||""; const signature=url.searchParams.get("signature")||""; const key=url.searchParams.get("key")||"";
 if(!jobId||!userId||!await verifyJobSignature(env,jobId,userId,expires,signature)) return json({error:"Tautan aset tidak valid atau kedaluwarsa."},403);
 if(!key.startsWith("vehicle-assets/"+userId+"/")||key.includes("..")) return json({error:"Aset tidak diizinkan."},403);
 const object=await env.MEDIA_BUCKET.get(key); if(!object) return json({error:"Foto kendaraan tidak ditemukan."},404);
 const headers=new Headers(); object.writeHttpMetadata(headers); headers.set("Cache-Control","private, no-store"); headers.set("X-Content-Type-Options","nosniff"); return new Response(object.body,{headers});
};
