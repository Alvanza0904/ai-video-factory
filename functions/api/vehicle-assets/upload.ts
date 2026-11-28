import { Env, json, userFrom } from "../_shared";
const allowed = new Set(["image/jpeg","image/png","image/webp"]);
export const onRequestPost: PagesFunction<Env> = async ({request,env}) => {
 const user=await userFrom(request,env); if(!user) return json({error:"Sesi tidak valid."},401);
 const form=await request.formData(); const file=form.get("file"); const brand=String(form.get("brand")||""); const model=String(form.get("model")||"").trim().slice(0,40);
 if(!(file instanceof File) || !["JAECOO","OMODA"].includes(brand) || !model) return json({error:"File, brand, dan model wajib diisi."},400);
 if(!allowed.has(file.type)) return json({error:"Format harus JPG, PNG, atau WebP."},415);
 if(file.size<1 || file.size>10*1024*1024) return json({error:"Ukuran foto maksimal 10 MB."},413);
 const ext=file.type==="image/jpeg"?"jpg":file.type==="image/png"?"png":"webp";
 const key="vehicle-assets/"+user.id+"/"+brand+"/"+crypto.randomUUID()+"."+ext;
 await env.MEDIA_BUCKET.put(key,file.stream(),{httpMetadata:{contentType:file.type},customMetadata:{userId:user.id,brand,model,filename:file.name.slice(0,120)}});
 return json({asset:{key,brand,model,filename:file.name.slice(0,120),size:file.size,uploadedAt:new Date().toISOString()}},201);
};
