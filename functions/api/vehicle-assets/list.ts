import { Env, json, userFrom } from "../_shared";
export const onRequestGet: PagesFunction<Env> = async ({request,env}) => {
 const user=await userFrom(request,env); if(!user) return json({error:"Sesi tidak valid."},401);
 const prefix="vehicle-assets/"+user.id+"/"; const assets:any[]=[]; let cursor:string|undefined;
 do { const page=await env.MEDIA_BUCKET.list({prefix,cursor,limit:100}); for(const obj of page.objects){const brand=obj.customMetadata?.brand;const model=obj.customMetadata?.model;if((brand==="JAECOO"||brand==="OMODA")&&model)assets.push({key:obj.key,brand,model,filename:obj.customMetadata?.filename||obj.key.split("/").pop(),size:obj.size,uploadedAt:obj.uploaded.toISOString()});} cursor=page.truncated?page.cursor:undefined; } while(cursor);
 assets.sort((a,b)=>b.uploadedAt.localeCompare(a.uploadedAt)); return json({assets});
};
