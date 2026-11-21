"use client";

import { useEffect, useRef, useState } from "react";
import { Activity, ArrowUpRight, Clapperboard, Cloud, Film, Github, HardDrive, Layers3, LogOut, Menu, Settings2, Sparkles, UploadCloud, WandSparkles, X, Play, FolderPlus, CheckCircle2 } from "lucide-react";

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

export default function Home() {
  const [menuOpen, setMenuOpen] = useState(false);
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
        if (data.job.status === "completed" && data.outputUrl) { setOutputUrl(data.outputUrl); setNotice("AI editing selesai. Video final sudah siap diputar."); }
        else if (data.job.status === "failed") { setNotice(data.job.error_message || "Proses editing gagal. Cek detail job."); }
      } catch (error) { if (active) setNotice((error as Error).message); }
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

  function logout() { localStorage.removeItem("avf-session"); setSession(null); setProjects([]); setAssets([]); setNotice("Kamu sudah keluar."); }

  return <main className="shell">
    <aside className={`sidebar ${menuOpen ? "sidebar-open" : ""}`}>
      <div className="brand"><div className="brand-mark"><Clapperboard size={21}/></div><div><strong>VIDEO FACTORY</strong><span>UNIVERSAL EDITOR</span></div><button className="mobile-close" onClick={()=>setMenuOpen(false)} aria-label="Tutup menu"><X size={19}/></button></div>
      <div className="workspace-label">WORKSPACE</div><nav>
        <a className="nav-item active" href="#"><Layers3 size={18}/> Dashboard</a><a className="nav-item" href="#new-project"><UploadCloud size={18}/> Buat proyek</a><a className="nav-item" href="#genres"><Film size={18}/> Gaya editing</a><a className="nav-item" href="#infrastructure"><Settings2 size={18}/> Infrastruktur</a>
      </nav>
      <div className="sidebar-bottom"><div className="profile"><div className="avatar">A</div><div><strong>{session?.user.email||"Workspace Alvan"}</strong><span>{session?"Authenticated":"Mobile workspace"}</span></div></div><div className="version">AI VIDEO FACTORY · 0.2</div></div>
    </aside>
    {menuOpen&&<button className="scrim" onClick={()=>setMenuOpen(false)} aria-label="Tutup navigasi"/>}
    <section className="main"><header className="topbar"><button className="mobile-menu" onClick={()=>setMenuOpen(true)} aria-label="Buka menu"><Menu size={21}/></button><div className="breadcrumb">Workspace <span>/</span> Dashboard</div><div className="top-status"><span className="status-dot"/>{session?"Signed in":"Cloud-first workspace"}</div></header>
      <div className="content">
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
        <footer><span>AI VIDEO FACTORY</span><span>Built for mobile-first creation · <a href="https://github.com/Alvanza0904/ai-video-factory" target="_blank" rel="noreferrer">GitHub <ArrowUpRight size={12}/></a></span></footer>
      </div>
    </section>
  </main>;
}
function Infra({icon,title,state,detail}:{icon:React.ReactNode;title:string;state:string;detail:string}) { return <div className="infra-card"><div className="infra-icon">{icon}</div><div className="infra-info"><strong>{title}</strong><span>{detail}</span><small>{state}</small></div></div>; }
