"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Activity, ArrowUpRight, Clapperboard, Cloud, Film, Github, HardDrive, Layers3, LogOut, Menu, Settings2, Sparkles, UploadCloud, WandSparkles, X, Play, FolderPlus, CheckCircle2, Video, Clock3, AlertCircle, RefreshCw, Download, Folder, ChevronRight, ArrowLeft } from "lucide-react";

const API = "https://sdmnhhgcenhzfnvzwyzo.supabase.co";
const ANON = "sb_publishable_uxSrstD_fl3oJS1BkfvtkA__KzQtI7A";
const genres = [
  { name: "Cinematic", detail: "Automotive, product, travel", icon: "🎬" },
  { name: "Drama & Story", detail: "Dialog, emotion, storytelling", icon: "🎭" },
  { name: "POV", detail: "First-person social content", icon: "👁️" },
  { name: "Comedy & Entertainment", detail: "Punchline, reaction, meme timing", icon: "😂" },
  { name: "Two Characters", detail: "One actor, multiple roles", icon: "🎭" },
  { name: "Review & Talking Head", detail: "Presenter, review, explanation", icon: "🎤" }
];
type Project = { id: string; name: string; created_at: string };
type Asset = { id: string; original_filename: string; upload_status: string; size_bytes: number };
type AuthResponse = { access_token?: string; refresh_token?: string; expires_in?: number; user?: { id: string; email?: string }; msg?: string; message?: string; error_description?: string };
type UploadInit = { key: string; uploadId: string; assetId: string; error?: string };
type UploadPart = { etag: string; error?: string };
type UploadComplete = { asset: Asset; error?: string };
type JobResponse = { jobId?: string; error?: string; success?: boolean };
type JobStatus = { job?: { status: string; progress: number; error_message?: string | null }; outputUrl?: string | null; error?: string };
type LibraryJob = { id:string; project_id:string; title:string|null; status:string; progress:number; error_message:string|null; genre:string|null; target_duration:number|null; created_at:string; projectName:string; outputUrl?:string|null; filename?:string|null; size_bytes?:number|null };

export default function Home() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState("dashboard");
  const [libraryJobs, setLibraryJobs] = useState<LibraryJob[]>([]);
  const [libraryLoading, setLibraryLoading] = useState(false);
  const [libraryError, setLibraryError] = useState("");
  const [selectedResultFolder, setSelectedResultFolder] = useState<string|null>(null);
  const [selectedGenre, setSelectedGenre] = useState("auto");
  const [notice, setNotice] = useState("Masuk untuk membuat proyek dan mengunggah footage langsung dari HP.");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [session, setSession] = useState<{access_token:string; refresh_token?:string; expires_at?:number; user:{id:string;email?:string}}|null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [projectName, setProjectName] = useState("Konten JAECOO Baru");
  const [assets, setAssets] = useState<Asset[]>([]);
  const [jobId, setJobId] = useState("");
  const [jobStatus, setJobStatus] = useState("");
  const [outputUrl, setOutputUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState("");
  const [duration, setDuration] = useState("45");
  const [instructions, setInstructions] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const raw = localStorage.getItem("avf-session");
    if (raw) { try { setSession(JSON.parse(raw)); } catch { localStorage.removeItem("avf-session"); } }
    const savedJobId = localStorage.getItem("avf-active-job");
    if (savedJobId) { setJobId(savedJobId); setJobStatus("restoring"); setNotice("Memulihkan status AI Editing terakhir…"); }
  }, []);

  useEffect(() => {
    if (session) { loadProjects(session.access_token); }
  }, [session]);

  useEffect(() => {
    if (session && projectId) { loadAssets(session.access_token, projectId); }
  }, [session, projectId]);

  useEffect(() => {
    if (!session || !jobId) return;
    let active = true;
    const poll = async () => {
      try {
        const response = await authorizedFetch("/api/jobs/status?job_id=" + encodeURIComponent(jobId), { headers: {} }, session.access_token);
        const data = await response.json() as JobStatus;
        if (!response.ok) throw new Error(data.error || "Gagal memeriksa status editing.");
        if (!active || !data.job) return;
        setJobStatus(data.job.status);
        if (data.job.status === "completed" && data.outputUrl) {
          setOutputUrl(data.outputUrl);
          setNotice("AI editing selesai. Video final sudah siap diputar.");
          localStorage.removeItem("avf-active-job");
        } else if (data.job.status === "failed") {
          setNotice(data.job.error_message || "Proses editing gagal. Cek detail job.");
        } else if (jobStatus === "restoring") {
          setNotice("Status AI Editing berhasil dipulihkan. Proses tetap berjalan di cloud.");
        }
      } catch {
        if (active) {
          // A temporary fetch failure (often when iOS suspends/resumes a tab)
          // must not be presented as an editing failure. Keep the job ID and retry.
          setNotice("Koneksi status terputus sementara. Job tetap tersimpan di cloud; aplikasi akan mencoba memuat ulang otomatis.");
        }
      }
    };
    void poll();
    const timer = window.setInterval(poll, 10000);
    return () => { active = false; window.clearInterval(timer); };
  }, [session, jobId]);

  async function auth(mode: "signup"|"login") {
    setBusy(true);
    try {
      const endpoint = mode === "signup" ? "/auth/v1/signup" : "/auth/v1/token?grant_type=password";
      const res = await fetch(API + endpoint, { method:"POST", headers:{"Content-Type":"application/json", apikey:ANON}, body:JSON.stringify({email,password}) });
      const data = await res.json() as AuthResponse;
      if (!res.ok) throw new Error(data.msg || data.message || data.error_description || "Autentikasi gagal");
      if (!data.access_token || !data.user) { setNotice("Akun dibuat. Periksa email untuk konfirmasi, lalu masuk."); return; }
      const s = {access_token:data.access_token,refresh_token:data.refresh_token,expires_at:Math.floor(Date.now()/1000)+(data.expires_in||3600),user:data.user};
      localStorage.setItem("avf-session", JSON.stringify(s)); setSession(s); setNotice("Berhasil masuk.");
    } catch(e) { setNotice((e as Error).message); }
    finally { setBusy(false); }
  }

  async function refreshAccessToken(currentToken: string): Promise<string | null> {
    const raw = localStorage.getItem("avf-session");
    if (!raw) return null;
    let stored: { access_token?: string; refresh_token?: string; user: { id: string; email?: string } };
    try { stored = JSON.parse(raw); } catch { return null; }
    if (stored.access_token && stored.access_token !== currentToken) return stored.access_token;
    if (!stored.refresh_token) return null;
    try {
      const response = await fetch(API + "/auth/v1/token?grant_type=refresh_token", {
        method: "POST",
        headers: { "Content-Type": "application/json", apikey: ANON },
        body: JSON.stringify({ refresh_token: stored.refresh_token })
      });
      const data = await response.json() as AuthResponse;
      if (!response.ok || !data.access_token || !data.refresh_token) return null;
      const next = {
        access_token: data.access_token,
        refresh_token: data.refresh_token,
        expires_at: Math.floor(Date.now() / 1000) + (data.expires_in || 3600),
        user: data.user || stored.user
      };
      localStorage.setItem("avf-session", JSON.stringify(next));
      setSession(next);
      return next.access_token;
    } catch { return null; }
  }

  async function authorizedFetch(url: string, init: RequestInit, token: string): Promise<Response> {
    const send = (accessToken: string) => {
      const headers = new Headers(init.headers || {});
      headers.set("Authorization", "Bearer " + accessToken);
      return fetch(url, { ...init, headers });
    };
    const response = await send(token);
    if (response.status !== 401) return response;
    const refreshed = await refreshAccessToken(token);
    return refreshed ? send(refreshed) : response;
  }

  async function loadLibrary(token:string) {
    setLibraryLoading(true); setLibraryError("");
    try {
      const [jobsRes, outputsRes, projectsRes] = await Promise.all([
        authorizedFetch(API + "/rest/v1/editing_jobs?select=id,project_id,title,status,progress,error_message,genre,target_duration,created_at&order=created_at.desc", { headers:{apikey:ANON} }, token),
        authorizedFetch(API + "/rest/v1/render_outputs?select=job_id,filename,size_bytes,created_at&order=created_at.desc", { headers:{apikey:ANON} }, token),
        authorizedFetch(API + "/rest/v1/video_projects?select=id,name", { headers:{apikey:ANON} }, token)
      ]);
      if (!jobsRes.ok) throw new Error("Tidak dapat memuat riwayat proyek. Periksa izin akses database.");
      const jobs = await jobsRes.json() as Array<Omit<LibraryJob,"projectName"|"outputUrl"|"filename"|"size_bytes">>;
      const outputs = outputsRes.ok ? await outputsRes.json() as Array<{job_id:string;filename:string;size_bytes:number}> : [];
      const projects = projectsRes.ok ? await projectsRes.json() as Array<{id:string;name:string}> : [];
      const outputMap = new Map(outputs.map(o=>[o.job_id,o]));
      const projectMap = new Map(projects.map(p=>[p.id,p.name]));
      const rows:LibraryJob[] = jobs.map(j=>({ ...j, projectName:projectMap.get(j.project_id)||"Proyek tanpa nama", filename:outputMap.get(j.id)?.filename, size_bytes:outputMap.get(j.id)?.size_bytes }));
      const completed = rows.filter(j=>j.status==="completed" && outputMap.has(j.id));
      const urls = await Promise.all(completed.map(async j=>{
        try { const r=await authorizedFetch("/api/jobs/status?job_id="+encodeURIComponent(j.id),{headers:{}},token); const d=await r.json() as JobStatus; return [j.id,r.ok?d.outputUrl||null:null] as const; } catch { return [j.id,null] as const; }
      }));
      const urlMap=new Map(urls);
      setLibraryJobs(rows.map(j=>({...j,outputUrl:urlMap.get(j.id)||null})));
    } catch(e) { setLibraryError((e as Error).message); }
    finally { setLibraryLoading(false); }
  }

  async function openLibrary(page:string) {
    setCurrentPage(page); setSelectedResultFolder(null); setMenuOpen(false);
    if (session) await loadLibrary(session.access_token);
  }

  async function loadProjects(token:string) {
    try {
      const r=await authorizedFetch(API+"/rest/v1/video_projects?select=id,name,created_at&status=eq.active&order=created_at.desc",{headers:{apikey:ANON}},token);
      if(!r.ok) throw new Error("Gagal memuat proyek");
      const rows=await r.json() as Project[]; setProjects(rows); if(rows.length && !projectId) setProjectId(rows[0].id);
    } catch(e) { setNotice((e as Error).message); }
  }

  async function loadAssets(token: string, selectedProjectId: string) {
    try {
      const response = await authorizedFetch(API + "/rest/v1/media_assets?select=id,original_filename,upload_status,size_bytes&project_id=eq." + encodeURIComponent(selectedProjectId) + "&upload_status=eq.uploaded&asset_type=eq.video&order=created_at.asc", { headers: { apikey: ANON } }, token);
      if (!response.ok) throw new Error("Gagal memuat daftar footage.");
      setAssets(await response.json() as Asset[]);
    } catch (error) { setNotice((error as Error).message); }
  }

  async function startEditing() {
    if (!session || !projectId || assets.length === 0) { setNotice("Pilih proyek dan unggah minimal satu video terlebih dahulu."); return; }
    setBusy(true); setOutputUrl(""); setJobStatus("queued");
    try {
      const response = await authorizedFetch("/api/jobs/create", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ projectId, assetIds: assets.map(asset => asset.id), genre: selectedGenre, targetDuration: Number(duration), instructions }) }, session.access_token);
      const data = await response.json() as JobResponse;
      if (!response.ok || !data.jobId) throw new Error(data.error || "Tidak dapat memulai AI editing.");
      localStorage.setItem("avf-active-job", data.jobId); setJobId(data.jobId); setJobStatus("analyzing"); setNotice("AI Director mulai membaca footage, dialog, dan adegan. Proses berjalan di cloud. Kamu boleh meninggalkan halaman; status akan dipulihkan saat kembali.");
    } catch (error) { setJobStatus("failed"); setNotice((error as Error).message); }
    finally { setBusy(false); }
  }

  async function createProject() {
    if(!session || !projectName.trim()) return;
    setBusy(true);
    try {
      const r=await authorizedFetch(API+"/rest/v1/video_projects",{method:"POST",headers:{apikey:ANON,"Content-Type":"application/json",Prefer:"return=representation"},body:JSON.stringify({name:projectName,brand:"JAECOO Palembang",user_id:session.user.id})},session.access_token);
      const data=await r.json() as (Project[] & {message?:string;details?:string;hint?:string}); if(!r.ok) throw new Error(data.message || data.details || `Gagal membuat proyek (${r.status})`);
      setProjects([data[0],...projects]); setProjectId(data[0].id); setNotice("Proyek berhasil dibuat.");
    } catch(e) { setNotice((e as Error).message); }
    finally { setBusy(false); }
  }

  async function uploadFiles(files:FileList|null) {
    if(!session || !projectId || !files?.length) { setNotice("Masuk dan pilih proyek terlebih dahulu."); return; }
    setBusy(true); const all=Array.from(files);
    try {
      for(let i=0;i<all.length;i++) {
        const file=all[i]; if(!file.type.startsWith("video/")) continue;
        setProgress("Menyiapkan "+file.name+" ("+(i+1)+"/"+all.length+")");
        const start=await authorizedFetch("/api/upload/start",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({projectId,filename:file.name,size:file.size,contentType:file.type})},session.access_token);
        const init=await start.json() as UploadInit; if(!start.ok) throw new Error(init.error||"Gagal memulai upload");
        const partSize=8*1024*1024, parts: {partNumber:number;etag:string}[]=[];
        for(let offset=0,partNumber=1;offset<file.size;offset+=partSize,partNumber++) {
          setProgress("Upload "+file.name+" · "+Math.min(100,Math.round((offset/file.size)*100))+"%");
          const chunk=file.slice(offset,Math.min(file.size,offset+partSize));
          const response=await authorizedFetch("/api/upload/part?key="+encodeURIComponent(init.key)+"&uploadId="+encodeURIComponent(init.uploadId)+"&partNumber="+partNumber,{method:"PUT",headers:{},body:chunk},session.access_token);
          const part=await response.json() as UploadPart; if(!response.ok) throw new Error(part.error||"Upload part gagal"); parts.push({partNumber,etag:part.etag});
        }
        const done=await authorizedFetch("/api/upload/complete",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({key:init.key,uploadId:init.uploadId,parts,assetId:init.assetId})},session.access_token);
        const result=await done.json() as UploadComplete; if(!done.ok) throw new Error(result.error||"Gagal menyelesaikan upload");
        setAssets(prev=>[...prev,result.asset]);
      }
      setNotice(all.length+" file selesai diunggah ke Cloudflare R2."); setProgress("");
      await loadAssets(session.access_token, projectId);
    } catch(e) { setNotice((e as Error).message); setProgress(""); }
    finally { setBusy(false); if(fileRef.current) fileRef.current.value=""; }
  }

  async function cancelJob(targetJobId:string) {
    if (!session) return;
    if (!window.confirm("Batalkan proses editing ini? Proses render akan dihentikan dan tidak menghasilkan video final.")) return;
    try {
      const response=await authorizedFetch("/api/jobs/cancel",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({jobId:targetJobId})},session.access_token);
      const data=await response.json() as {success?:boolean;status?:string;error?:string};
      if(!response.ok||!data.success) throw new Error(data.error||"Tidak dapat membatalkan proses.");
      setLibraryJobs(prev=>prev.map(j=>j.id===targetJobId?{...j,status:"cancelled",progress:0,error_message:"Dibatalkan oleh pengguna."}:j));
      if(jobId===targetJobId){setJobStatus("cancelled");setOutputUrl("");setJobId("");localStorage.removeItem("avf-active-job");}
      setNotice("Proses editing berhasil dibatalkan.");
    } catch(e) { setNotice((e as Error).message); }
  }

  async function cancelAllJobs(activeJobs:LibraryJob[]) {
    if (!session || !activeJobs.length) return;
    if (!window.confirm("Batalkan "+activeJobs.length+" proses yang sedang berjalan? Video yang sudah selesai tidak akan terpengaruh.")) return;
    let cancelled=0; const errors:string[]=[];
    await Promise.all(activeJobs.map(async j=>{
      try {
        const response=await authorizedFetch("/api/jobs/cancel",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({jobId:j.id})},session.access_token);
        const data=await response.json() as {success?:boolean;error?:string};
        if(!response.ok||!data.success) throw new Error(data.error||"Gagal");
        cancelled++;
        setLibraryJobs(prev=>prev.map(item=>item.id===j.id?{...item,status:"cancelled",progress:0,error_message:"Dibatalkan oleh pengguna."}:item));
        if(jobId===j.id){setJobStatus("cancelled");setOutputUrl("");setJobId("");localStorage.removeItem("avf-active-job");}
      } catch(e) { errors.push(j.title||j.id.slice(0,8)); }
    }));
    setNotice(cancelled+" proses berhasil dibatalkan."+ (errors.length?" "+errors.length+" proses belum berhasil dihentikan; muat ulang lalu coba lagi.":""));
  }

  function logout() { localStorage.removeItem("avf-session"); setSession(null); setProjects([]); setAssets([]); setNotice("Kamu sudah keluar."); }

  return <main className="shell">
    <aside className={`sidebar ${menuOpen ? "sidebar-open" : ""}`}>
      <div className="brand"><div className="brand-mark"><Clapperboard size={21}/></div><div><strong>VIDEO FACTORY</strong><span>UNIVERSAL EDITOR</span></div><button className="mobile-close" onClick={()=>setMenuOpen(false)} aria-label="Tutup menu"><X size={19}/></button></div>
      <div className="workspace-label">WORKSPACE</div><nav>
        <button className={`nav-item ${currentPage==="dashboard"?"active":""}`} onClick={()=>{setCurrentPage("dashboard");setMenuOpen(false)}}><Layers3 size={18}/> Dashboard</button><button className={`nav-item ${currentPage==="projects"?"active":""}`} onClick={()=>openLibrary("projects")}><FolderPlus size={18}/> Semua proyek</button><button className={`nav-item ${currentPage==="results"?"active":""}`} onClick={()=>openLibrary("results")}><Video size={18}/> Hasil selesai</button><button className={`nav-item ${currentPage==="processing"?"active":""}`} onClick={()=>openLibrary("processing")}><Clock3 size={18}/> Sedang diproses</button><button className={`nav-item ${currentPage==="failed"?"active":""}`} onClick={()=>openLibrary("failed")}><AlertCircle size={18}/> Proyek gagal</button><button className="nav-item" onClick={()=>{setCurrentPage("dashboard");setMenuOpen(false);setTimeout(()=>document.getElementById("new-project")?.scrollIntoView({behavior:"smooth"}),50)}}><UploadCloud size={18}/> Buat proyek</button><Link className="nav-item" href="/education"><Clapperboard size={18}/> Video Edukasi Animasi</Link><button className="nav-item" onClick={()=>{setCurrentPage("dashboard");setMenuOpen(false);setTimeout(()=>document.getElementById("genres")?.scrollIntoView({behavior:"smooth"}),50)}}><Film size={18}/> Gaya editing</button><button className="nav-item" onClick={()=>{setCurrentPage("dashboard");setMenuOpen(false);setTimeout(()=>document.getElementById("infrastructure")?.scrollIntoView({behavior:"smooth"}),50)}}><Settings2 size={18}/> Infrastruktur</button>
      </nav>
      <div className="sidebar-bottom"><div className="profile"><div className="avatar">A</div><div><strong>{session?.user.email||"Workspace Alvan"}</strong><span>{session?"Authenticated":"Mobile workspace"}</span></div></div><div className="version">AI VIDEO FACTORY · 0.2</div></div>
    </aside>
    {menuOpen&&<button className="scrim" onClick={()=>setMenuOpen(false)} aria-label="Tutup navigasi"/>}
    <section className="main"><header className="topbar"><button className="mobile-menu" onClick={()=>setMenuOpen(true)} aria-label="Buka menu"><Menu size={21}/></button><div className="breadcrumb">Workspace <span>/</span> {({dashboard:"Dashboard",projects:"Semua Proyek",results:"Hasil Selesai",processing:"Sedang Diproses",failed:"Proyek Gagal"} as Record<string,string>)[currentPage]}</div><div className="top-status"><span className="status-dot"/>{session?"Signed in":"Cloud-first workspace"}</div></header>
      <div className="content">
        {currentPage==="dashboard" ? <>
        <section className="welcome"><div><div className="eyebrow"><Sparkles size={14}/> YOUR CREATIVE WORKSPACE</div><h1>Ide jadi video.<br/><em>Tanpa edit manual.</em></h1><p>Upload footage dari HP. AI akan memahami isi konten, menyusun cerita, memilih gaya editing, lalu menyiapkan video final.</p></div><div className="welcome-art"><div className="art-ring ring-one"/><div className="art-ring ring-two"/><div className="art-core"><Clapperboard size={42}/></div><span className="art-tag">AI / EDIT / EXPORT</span></div></section>
        <div className="notice"><Activity size={17}/><span>{notice}</span></div>
        {!session ? <section className="section auth-panel"><div className="section-heading"><div><div className="eyebrow">SECURE WORKSPACE</div><h2>Masuk ke Video Factory</h2></div></div><div className="auth-fields"><input type="email" placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)}/><input type="password" placeholder="Password" value={password} onChange={e=>setPassword(e.target.value)}/><button className="primary-button" disabled={busy||!email||password.length<6} onClick={()=>auth("login")}>Masuk</button><button className="secondary-button" disabled={busy||!email||password.length<6} onClick={()=>auth("signup")}>Buat akun</button></div><p className="muted tiny">Akun tersimpan di Supabase Auth. Gunakan email dan password pribadi.</p></section> :
        <section className="section" id="new-project">
          <div className="section-heading"><div><div className="eyebrow">START CREATING</div><h2>Proyek & footage</h2></div><button className="text-button" onClick={logout}><LogOut size={14}/> Keluar</button></div>
          <div className="project-panel"><div className="project-copy"><h3>Kelola proyek konten</h3><div className="project-controls"><select value={projectId} onChange={e=>setProjectId(e.target.value)}><option value="">Pilih proyek</option>{projects.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select><input value={projectName} onChange={e=>setProjectName(e.target.value)} placeholder="Nama proyek baru"/><button className="secondary-button" onClick={createProject} disabled={busy}><FolderPlus size={16}/> Buat proyek</button></div></div></div>
          <div className="upload-card"><div className="upload-visual"><UploadCloud size={30}/><span>MULTI-CLIP UPLOAD</span></div><div className="project-copy"><h3>Upload banyak footage sekaligus</h3><p>Pilih beberapa video dari galeri. File dipecah menjadi beberapa bagian agar lebih stabil saat upload dari HP dan disimpan privat di Cloudflare R2.</p><input ref={fileRef} type="file" accept="video/*" multiple onChange={e=>uploadFiles(e.target.files)} disabled={busy||!projectId}/>{progress&&<div className="upload-progress">{progress}</div>}<div className="project-actions"><button className="primary-button" onClick={()=>fileRef.current?.click()} disabled={busy||!projectId}><UploadCloud size={17}/> Pilih video dari HP</button><span className="muted tiny">{busy?"Sedang memproses…":projectId?"Pilih beberapa klip sekaligus":"Pilih atau buat proyek dahulu"}</span></div></div></div>
          {assets.length>0&&<div className="asset-list"><h3><CheckCircle2 size={17}/> {assets.length} footage siap diedit</h3>{assets.map(a=><div key={a.id}>{a.original_filename} · {Math.round(a.size_bytes/1048576)} MB · {a.upload_status}</div>)}</div>}
          <div className="editor-settings"><h3><WandSparkles size={17}/> Pengaturan AI Director</h3><label>Gaya editing</label><select value={selectedGenre} onChange={e=>setSelectedGenre(e.target.value)}><option value="auto">Deteksi otomatis</option><option value="cinematic">Cinematic</option><option value="drama">Drama & storytelling</option><option value="pov">POV</option><option value="comedy">Comedy & entertainment</option><option value="two_character">Satu aktor, dua karakter</option><option value="review">Review & talking head</option><option value="mixed">Mixed</option></select><label>Durasi target</label><select value={duration} onChange={e=>setDuration(e.target.value)}><option value="30">30 detik</option><option value="45">45 detik</option><option value="60">60 detik</option></select><label>Instruksi tambahan (opsional)</label><textarea value={instructions} onChange={e=>setInstructions(e.target.value)} placeholder="Contoh: fokus pada detail eksterior JAECOO J5, pertahankan dialog asli, tempo cepat…"/><button className="primary-button" disabled={busy||!assets.length||!projectId} onClick={startEditing}><Play size={16}/> {busy?"Menyiapkan…":"Mulai AI Editing"}</button><p className="muted tiny">{assets.length ? "AI akan menganalisis semua footage terunggah, transkrip dialog, dan memilih adegan." : "Unggah footage terlebih dahulu untuk mengaktifkan AI editing."}</p>{jobId&&<div className="asset-list"><h3><Activity size={17}/> Status AI Editing</h3><div>Job: {jobId.slice(0,8)} · {jobStatus} · {jobStatus==="completed"?"100%":"sedang diproses"}</div>{outputUrl&&<video controls playsInline preload="metadata" src={outputUrl} style={{width:"100%",borderRadius:12,marginTop:12}}/>}</div>}</div>
        </section>}
        <section className="section" id="genres"><div className="section-heading"><div><div className="eyebrow">UNIVERSAL AI DIRECTOR</div><h2>Semua genre, satu editor</h2></div><span className="muted small">Genre otomatis menjadi pilihan utama</span></div><div className="genre-grid">{genres.map(g=><button key={g.name} className={`genre-card ${selectedGenre===g.name.toLowerCase()?"genre-selected":""}`} onClick={()=>setSelectedGenre(g.name.toLowerCase())}><span className="genre-icon">{g.icon}</span><strong>{g.name}</strong><span>{g.detail}</span></button>)}</div><div className="genre-footer"><span>Preferensi: <strong>{selectedGenre==="auto"?"Auto-detect":selectedGenre}</strong></span><button className="text-button" onClick={()=>setSelectedGenre("auto")}>Kembali ke Auto-detect <ArrowUpRight size={14}/></button></div></section>
        <section className="section" id="infrastructure"><div className="section-heading"><div><div className="eyebrow">CLOUD PIPELINE</div><h2>Infrastruktur</h2></div><span className="muted small">Komponen terhubung / proses</span></div><div className="infra-grid"><Infra icon={<Github size={18}/>} title="GitHub Actions" state="Workflow smoke test tersedia" detail="Cloud render worker"/><Infra icon={<WandSparkles size={18}/>} title="Re:Link Gateway" state="Vision model sedang diuji" detail="AI director & analysis"/><Infra icon={<HardDrive size={18}/>} title="Cloudflare R2" state="Bucket & binding aktif" detail="Media storage"/><Infra icon={<Cloud size={18}/>} title="Supabase" state="Database & Auth aktif" detail="Auth, metadata, jobs"/></div></section>
        </> : <section className="library-page">
          <div className="section-heading"><div><div className="eyebrow">PROJECT LIBRARY</div><h2>{({projects:"Semua Proyek",results:"Hasil Proyek Selesai",processing:"Sedang Diproses",failed:"Proyek Gagal"} as Record<string,string>)[currentPage]}</h2><p className="muted library-intro">Riwayat tersimpan di database dan tetap tersedia saat kamu membuka aplikasi kembali.</p></div><button className="secondary-button" onClick={()=>session&&loadLibrary(session.access_token)} disabled={libraryLoading}><RefreshCw size={15}/> Muat ulang</button></div>
          {libraryLoading&&<div className="library-empty">Memuat riwayat proyek…</div>}
          {libraryError&&<div className="notice"><AlertCircle size={16}/>{libraryError}</div>}
          {!libraryLoading&&!libraryError&&(()=>{
            const completed=libraryJobs.filter(j=>j.status==="completed"&&!!j.filename);
            const folders=[
              {id:"cinematic",name:"Cinematic",icon:"🎬",desc:"Visual cinematic dan automotive"},
              {id:"drama",name:"Drama & Story",icon:"🎭",desc:"Storytelling dan dialog"},
              {id:"pov",name:"POV",icon:"👁️",desc:"Sudut pandang orang pertama"},
              {id:"comedy",name:"Comedy & Entertainment",icon:"😂",desc:"Hiburan, reaksi, dan punchline"},
              {id:"two_character",name:"Two Characters",icon:"🎭",desc:"Satu aktor dengan beberapa peran"},
              {id:"review",name:"Review & Talking Head",icon:"🎤",desc:"Review, presenter, dan penjelasan"},
              {id:"mixed",name:"Mixed Content",icon:"🎞️",desc:"Format campuran"},
              {id:"auto",name:"Auto Detect / Lainnya",icon:"✨",desc:"Kategori otomatis atau belum ditentukan"}
            ];
            const category=(genre:string|null)=>{const g=(genre||"auto").toLowerCase().replace(/[ &-]/g,"_");if(["cinematic","drama","pov","comedy","two_character","review","mixed"].includes(g))return g; if(g.includes("cinema"))return "cinematic";if(g.includes("drama")||g.includes("story"))return "drama";if(g.includes("comedy")||g.includes("entertain"))return "comedy";if(g.includes("talk")||g.includes("review"))return "review";return "auto";};
            if(currentPage==="results"){
              if(selectedResultFolder){
                const folder=folders.find(f=>f.id===selectedResultFolder)!;
                const items=completed.filter(j=>category(j.genre)===selectedResultFolder);
                return <><button className="back-folder" onClick={()=>setSelectedResultFolder(null)}><ArrowLeft size={16}/> Semua folder hasil</button><div className="folder-heading"><span>{folder.icon}</span><div><h3>{folder.name}</h3><p>{folder.desc} · {items.length} video</p></div></div>{items.length===0?<div className="library-empty"><Video size={28}/><strong>Folder ini masih kosong</strong><span>Hasil editing kategori ini akan otomatis masuk ke sini.</span></div>:<div className="library-grid">{items.map(j=><article className="library-card" key={j.id}><div className="library-card-top"><span className="job-pill is-done">Selesai</span><span className="muted tiny">{new Date(j.created_at).toLocaleString("id-ID",{dateStyle:"medium",timeStyle:"short"})}</span></div><h3>{j.title||j.projectName}</h3><p className="muted tiny">{j.projectName} · {j.target_duration||"-"} detik</p>{j.outputUrl?<><video className="library-video" controls playsInline preload="metadata" src={j.outputUrl}/><div className="library-actions"><a className="primary-button" href={j.outputUrl + "&download=1"}><Download size={15}/> Unduh video</a><span className="muted tiny">{j.size_bytes?Math.round(j.size_bytes/1048576)+" MB":""}</span></div></>:<div className="library-warning">Video tercatat selesai, tetapi tautan pemutaran belum tersedia. Tekan Muat ulang.</div>}</article>)}</div>}</>;
              }
              return completed.length===0?<div className="library-empty"><Folder size={28}/><strong>Belum ada hasil selesai</strong><span>Setelah AI menyelesaikan editing, video akan tersimpan di folder kategorinya.</span></div>:<div className="folder-grid">{folders.map(folder=>{const count=completed.filter(j=>category(j.genre)===folder.id).length;return <button className="result-folder" key={folder.id} onClick={()=>setSelectedResultFolder(folder.id)}><div className="folder-icon">{folder.icon}<Folder size={25}/></div><div className="folder-copy"><strong>{folder.name}</strong><span>{folder.desc}</span><small>{count} video</small></div><ChevronRight size={18}/></button>})}</div>;
            }
            const activeStatuses=["queued","analyzing","rendering","processing","running"];
            const activeJobs=libraryJobs.filter(j=>activeStatuses.includes(j.status));
            const visible=libraryJobs.filter(j=>currentPage==="projects"||(currentPage==="processing"?activeStatuses.includes(j.status):j.status==="failed"));
            return <>{currentPage==="processing"&&activeJobs.length>0&&<div className="section-heading"><div><strong>{activeJobs.length} proses aktif</strong><p className="muted tiny">Batalkan proses yang tidak lagi diperlukan.</p></div><button className="secondary-button" onClick={()=>cancelAllJobs(activeJobs)}><X size={15}/> Batalkan semua</button></div>}{visible.length===0?<div className="library-empty"><Video size={28}/><strong>Belum ada proyek di kelompok ini</strong><span>Proyek akan muncul otomatis di sini setelah tersimpan.</span></div>:<div className="library-grid">{visible.map(j=><article className="library-card" key={j.id}><div className="library-card-top"><span className={`job-pill ${j.status==="failed"?"is-failed":"is-running"}`}>{j.status==="failed"?"Gagal":j.status}</span><span className="muted tiny">{new Date(j.created_at).toLocaleString("id-ID",{dateStyle:"medium",timeStyle:"short"})}</span></div><h3>{j.title||j.projectName}</h3><p className="muted tiny">{j.projectName} · {j.genre||"Auto"} · {j.target_duration||"-"} detik</p>{j.status==="failed"?<div className="library-warning">{j.error_message||"Proses editing gagal."}</div>:<div className="library-progress"><span>Progres</span><strong>{j.progress||0}%</strong><div><i style={{width:Math.max(0,Math.min(100,j.progress||0))+"%"}}/></div></div>}{currentPage==="processing"&&<button className="secondary-button" style={{marginTop:14,width:"100%"}} onClick={()=>cancelJob(j.id)}><X size={15}/> Batalkan proses ini</button>}</article>)}</div>}</>;
          })()}
        </section>}
        <footer><span>AI VIDEO FACTORY</span><span>Built for mobile-first creation · <a href="https://github.com/Alvanza0904/ai-video-factory" target="_blank" rel="noreferrer">GitHub <ArrowUpRight size={12}/></a></span></footer>
      </div>
    </section>
  </main>;
}
function Infra({icon,title,state,detail}:{icon:React.ReactNode;title:string;state:string;detail:string}) { return <div className="infra-card"><div className="infra-icon">{icon}</div><div className="infra-info"><strong>{title}</strong><span>{detail}</span><small>{state}</small></div></div>; }
