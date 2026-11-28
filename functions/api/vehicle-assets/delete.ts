import { Env, json, userFrom } from "../_shared";
export const onRequestPost: PagesFunction<Env> = async ({request,env}) => {
 const user=await userFrom(request,env); if(!user) return json({error:"Sesi tidak valid."},401);
 let body:{key?:string};try{body=await request.json() as {key?:string};}catch{return json({error:"Permintaan tidak valid."},400);}
 const key=body.key||"";if(!key.startsWith("vehicle-assets/"+user.id+"/")||key.includes(".."))return json({error:"Aset tidak diizinkan."},403);
 await env.MEDIA_BUCKET.delete(key);return json({success:true});
};
