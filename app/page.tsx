"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, ArrowDownToLine, ArrowLeft, CheckCircle2, Clapperboard, Clock3, Film, Folder, FolderOpen, LogIn, LogOut, Play, Plus, RefreshCw, Sparkles, Video, XCircle } from "lucide-react";
import "./studio.css";

const API = "https://sdmnhhgcenhzfnvzwyzo.supabase.co";
const ANON = "sb_publishable_uxSrstD_fl3oJS1BkfvtkA__KzQtI7A";
const TOPICS = [
  ["Regenerative braking: bagaimana mobil listrik mengembalikan energi saat melambat?", "regenerative braking"],
  ["Mengenal baterai LFP pada kendaraan listrik", "baterai LFP"],
  ["Apa perbedaan BEV, HEV, dan PHEV?", "perbedaan BEV, HEV, dan PHEV"],
  ["Apa bedanya pengisian daya AC dan DC?", "perbedaan charging AC dan DC"],
  ["Bagaimana motor listrik menggerakkan mobil?", "cara kerja motor listrik"]
] as const;

type Session = { access_token: string; refresh_token?: string; expires_at?: number; user: { id: string; email?: string } };
type AuthPayload = { access_token?: string; refresh_token?: string; expires_in?: number; user?: Session["user"]; msg?: string; message?: string; error_description?: string };
type Job = { id: string; project_id: string; title: string | null; status: string; progress: number; error_message: string | null; target_duration: number | null; created_at: string; instructions: string; outputUrl?: string | null; filename?: string; size_bytes?: number };
type StatusPayload = { job?: { status: string; progress: number; error_message?: string | null }; outputUrl?: string | null; error?: string };
type VehicleAsset = { key: string; brand: "JAECOO" | "OMODA"; model: string; filename: string; size: number; uploadedAt: string };

function brandOf(job: Job) {
  try { return JSON.parse(job.instructions || "{}").brand === "OMODA" ? "OMODA" : "JAECOO"; } catch { return "JAECOO"; }
}
function statusLabel(status: string) {
  if (status === "completed") return "Selesai";
  if (status === "failed") return "Gagal";
  if (status === "queued") return "Dalam antrean";
  if (status === "analyzing") return "Menyiapkan naskah";
  if (status === "rendering") return "Membuat animasi";
  return "Sedang diproses";
}
function dateLabel(value: string) {
  return new Date(value).toLocaleString("id-ID", { dateStyle: "medium", timeStyle: "short" });
}

export default function Home() {
  const [session, setSession] = useState<Session | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authMode, setAuthMode] = useState<"login" | "signup">("login");
  const [tab, setTab] = useState<"generate" | "process" | "library" | "assets">("generate");
  const [brand, setBrand] = useState<"JAECOO" | "OMODA">("JAECOO");
  const [topic, setTopic] = useState<string>(TOPICS[0][1]);
  const [customTopic, setCustomTopic] = useState("");
  const [duration, setDuration] = useState("45");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("Studio siap. Pilih topik untuk mulai membuat video animasi.");
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(false);
  const [folder, setFolder] = useState<"OMODA" | "JAECOO" | null>(null);
  const [activeJobId, setActiveJobId] = useState("");
  const [assets, setAssets] = useState<VehicleAsset[]>([]);
  const [assetBrand, setAssetBrand] = useState<"JAECOO" | "OMODA">("JAECOO");
  const [assetModel, setAssetModel] = useState("J5");
  const [selectedAsset, setSelectedAsset] = useState("");
  const [assetBusy, setAssetBusy] = useState(false);

  const refreshToken = useCallback(async (current: Session): Promise<Session | null> => {
    if (!current.refresh_token) return null;
    try {
      const response = await fetch(API + "/auth/v1/token?grant_type=refresh_token", {
        method: "POST", headers: { "Content-Type": "application/json", apikey: ANON },
        body: JSON.stringify({ refresh_token: current.refresh_token })
      });
      const data = await response.json() as AuthPayload;
      if (!response.ok || !data.access_token) return null;
      const updated: Session = { ...current, access_token: data.access_token, refresh_token: data.refresh_token || current.refresh_token, expires_at: Math.floor(Date.now() / 1000) + (data.expires_in || 3600), user: data.user || current.user };
      localStorage.setItem("avf-session", JSON.stringify(updated));
      setSession(updated);
      return updated;
    } catch { return null; }
  }, []);

  const authorizedFetch = useCallback(async (url: string, init: RequestInit = {}, active?: Session): Promise<Response> => {
    const current = active || session;
    if (!current) throw new Error("Silakan masuk terlebih dahulu.");
    const send = (token: string) => {
      const headers = new Headers(init.headers || {});
      headers.set("Authorization", "Bearer " + token);
      if (url.includes("/rest/v1/")) headers.set("apikey", ANON);
      return fetch(url, { ...init, headers });
    };
    let response = await send(current.access_token);
    if (response.status === 401) {
      const updated = await refreshToken(current);
      if (updated) response = await send(updated.access_token);
    }
    return response;
  }, [session, refreshToken]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem("avf-session");
      if (raw) setSession(JSON.parse(raw) as Session);
      const saved = localStorage.getItem("avf-education-job");
      if (saved) setActiveJobId(saved);
    } catch { localStorage.removeItem("avf-session"); }
  }, []);

  const loadJobs = useCallback(async (active?: Session) => {
    const current = active || session;
    if (!current) return;
    setLoadingJobs(true);
    try {
      const response = await authorizedFetch(API + "/rest/v1/editing_jobs?select=id,project_id,title,status,progress,error_message,target_duration,created_at,instructions&user_id=eq." + encodeURIComponent(current.user.id) + "&order=created_at.desc&limit=100", {}, current);
      if (!response.ok) throw new Error("Riwayat produksi tidak dapat dimuat.");
      const all = await response.json() as Job[];
      const animationJobs = all.filter(job => (job.instructions || "").includes("animated_education"));
      const outputsResponse = await authorizedFetch(API + "/rest/v1/render_outputs?select=job_id,filename,size_bytes&user_id=eq." + encodeURIComponent(current.user.id), {}, current);
      const outputs = outputsResponse.ok ? await outputsResponse.json() as Array<{ job_id: string; filename: string; size_bytes: number }> : [];
      const outputMap = new Map(outputs.map(item => [item.job_id, item]));
      const enriched = animationJobs.map(job => ({ ...job, filename: outputMap.get(job.id)?.filename, size_bytes: outputMap.get(job.id)?.size_bytes }));
      const candidates = enriched.filter(job => !["failed", "cancelled"].includes(job.status));
      const updates = await Promise.all(candidates.map(async job => {
        try {
          const response = await authorizedFetch("/api/jobs/status?job_id=" + encodeURIComponent(job.id), {}, current);
          const data = await response.json() as StatusPayload;
          if (!response.ok || !data.job) return [job.id, null] as const;
          return [job.id, { status: data.job.status, progress: data.job.progress, error_message: data.job.error_message || null, outputUrl: data.outputUrl || null }] as const;
        } catch { return [job.id, null] as const; }
      }));
      const updateMap = new Map(updates);
      const activeUpdate = activeJobId ? updateMap.get(activeJobId) : null;
      if (activeUpdate && ["completed", "failed"].includes(activeUpdate.status)) localStorage.removeItem("avf-education-job");
      setJobs(enriched.map(job => ({ ...job, ...(updateMap.get(job.id) || {}), outputUrl: updateMap.get(job.id)?.outputUrl || null })));
    } catch (error) { setMessage((error as Error).message); }
    finally { setLoadingJobs(false); }
  }, [session, authorizedFetch, activeJobId]);

  useEffect(() => { if (session) { void loadJobs(session); void loadAssets(session); } }, [session, loadJobs]);

  useEffect(() => {
    if (!session) return;
    const timer = window.setInterval(() => { void loadJobs(session); }, 12000);
    return () => window.clearInterval(timer);
  }, [session, loadJobs]);

  async function loadAssets(active?: Session) {
    const current = active || session; if (!current) return;
    try { const response = await authorizedFetch("/api/vehicle-assets/list", {}, current); const data = await response.json() as {assets?:VehicleAsset[];error?:string}; if (!response.ok) throw new Error(data.error || "Aset gagal dimuat."); setAssets(data.assets || []); }
    catch(error) { setMessage((error as Error).message); }
  }
  async function uploadVehicleAsset(file?: File) {
    if (!file || !session) return;
    if (!["image/jpeg","image/png","image/webp"].includes(file.type)) { setMessage("Gunakan foto JPG, PNG, atau WebP."); return; }
    if (file.size > 10*1024*1024) { setMessage("Ukuran foto maksimal 10 MB."); return; }
    setAssetBusy(true);
    try { const form=new FormData(); form.append("file",file); form.append("brand",assetBrand); form.append("model",assetModel); const response=await authorizedFetch("/api/vehicle-assets/upload",{method:"POST",body:form},session); const data=await response.json() as {asset?:VehicleAsset;error?:string}; if(!response.ok || !data.asset) throw new Error(data.error || "Upload gagal."); setAssets(old=>[data.asset!,...old]); setSelectedAsset(data.asset.key); setMessage("Foto kendaraan berhasil diunggah."); }
    catch(error) { setMessage((error as Error).message); } finally { setAssetBusy(false); }
  }
  async function deleteVehicleAsset(key:string) {
    if(!session || !window.confirm("Hapus foto kendaraan ini?")) return;
    try { const response=await authorizedFetch("/api/vehicle-assets/delete",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({key})},session); const data=await response.json() as {error?:string}; if(!response.ok) throw new Error(data.error || "Hapus gagal."); setAssets(old=>old.filter(x=>x.key!==key)); if(selectedAsset===key)setSelectedAsset(""); setMessage("Foto kendaraan dihapus."); }
    catch(error) { setMessage((error as Error).message); }
  }
  async function signIn() {
    setBusy(true);
    try {
      const endpoint = authMode === "signup" ? "/auth/v1/signup" : "/auth/v1/token?grant_type=password";
      const response = await fetch(API + endpoint, { method: "POST", headers: { "Content-Type": "application/json", apikey: ANON }, body: JSON.stringify({ email, password }) });
      const data = await response.json() as AuthPayload;
      if (!response.ok) throw new Error(data.msg || data.message || data.error_description || "Autentikasi gagal.");
      if (!data.access_token || !data.user) { setMessage("Akun dibuat. Periksa email untuk konfirmasi, lalu masuk."); return; }
      const next: Session = { access_token: data.access_token, refresh_token: data.refresh_token, expires_at: Math.floor(Date.now() / 1000) + (data.expires_in || 3600), user: data.user };
      localStorage.setItem("avf-session", JSON.stringify(next));
      setSession(next);
      setMessage("Berhasil masuk ke studio produksi.");
    } catch (error) { setMessage((error as Error).message); }
    finally { setBusy(false); }
  }

  async function generate() {
    if (!session) { setMessage("Masuk terlebih dahulu untuk memulai produksi."); return; }
    const selectedTopic = (customTopic.trim() || topic).trim();
    if (selectedTopic.length < 8) { setMessage("Topik minimal 8 karakter."); return; }
    setBusy(true);
    setMessage("Mengirim permintaan produksi animasi…");
    try {
      const response = await authorizedFetch("/api/education/create", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ brand, topic: selectedTopic, duration: Number(duration), vehicleAssetKey: selectedAsset || null }) }, session);
      const data = await response.json() as { jobId?: string; error?: string };
      if (!response.ok || !data.jobId) throw new Error(data.error || "Tidak dapat memulai produksi.");
      localStorage.setItem("avf-education-job", data.jobId);
      setActiveJobId(data.jobId);
      setTab("process");
      setMessage("Produksi masuk antrean. Pantau progresnya di halaman Proses Produksi.");
      await loadJobs(session);
    } catch (error) { setMessage((error as Error).message); }
    finally { setBusy(false); }
  }

  function logout() {
    localStorage.removeItem("avf-session");
    localStorage.removeItem("avf-education-job");
    setSession(null); setJobs([]); setActiveJobId("");
    setMessage("Kamu sudah keluar dari workspace.");
  }

  const activeJobs = useMemo(() => jobs.filter(job => !["completed", "failed", "cancelled"].includes(job.status)), [jobs]);
  const completedJobs = useMemo(() => jobs.filter(job => job.status === "completed"), [jobs]);
  const failedJobs = useMemo(() => jobs.filter(job => job.status === "failed"), [jobs]);
  const folderJobs = useMemo(() => folder ? completedJobs.filter(job => brandOf(job) === folder) : [], [completedJobs, folder]);

  return <main className="studio-shell">
    <header className="studio-header">
      <div className="studio-brand"><span className="studio-mark"><Clapperboard size={21}/></span><span><b>ANIMATED VIDEO STUDIO</b><small>OMODA × JAECOO PALEMBANG</small></span></div>
      <div className="studio-account">{session ? <><span>{session.user.email || "Workspace aktif"}</span><button onClick={logout} aria-label="Keluar"><LogOut size={17}/></button></> : <span>Workspace belum masuk</span>}</div>
    </header>

    <div className="studio-wrap">
      <section className="studio-hero">
        <div className="studio-eyebrow"><Sparkles size={14}/> ANIMATION PRODUCTION WORKSPACE</div>
        <h1>Ide jadi <em>video animasi.</em></h1>
        <p>Satu tempat untuk membuat video, memantau proses render, dan menyimpan semua hasil produksi OMODA maupun JAECOO.</p>
        <div className="studio-stats">
          <div><b>{jobs.length}</b><span>Total produksi</span></div>
          <div><b>{activeJobs.length}</b><span>Sedang diproses</span></div>
          <div><b>{completedJobs.length}</b><span>Video selesai</span></div>
        </div>
      </section>

      {!session ? <section className="studio-auth">
        <div><span className="studio-eyebrow"><LogIn size={14}/> AKSES WORKSPACE</span><h2>Masuk untuk mulai produksi</h2><p>Gunakan akun studio yang sudah kamu buat sebelumnya.</p></div>
        <div className="auth-form"><input type="email" value={email} onChange={event => setEmail(event.target.value)} placeholder="Email" autoComplete="email"/><input type="password" value={password} onChange={event => setPassword(event.target.value)} placeholder="Password" autoComplete={authMode === "login" ? "current-password" : "new-password"}/><button className="studio-primary" disabled={busy || !email || !password} onClick={signIn}>{busy ? "Memproses…" : authMode === "login" ? "Masuk" : "Buat akun"}</button><button className="studio-link" onClick={() => setAuthMode(authMode === "login" ? "signup" : "login")}>{authMode === "login" ? "Belum punya akun? Daftar" : "Sudah punya akun? Masuk"}</button></div>
      </section> : <>
        <nav className="studio-tabs">
          <button className={tab === "generate" ? "selected" : ""} onClick={() => setTab("generate")}><Plus size={17}/> Generate Animasi</button>
          <button className={tab === "process" ? "selected" : ""} onClick={() => { setTab("process"); void loadJobs(); }}><Activity size={17}/> Proses Produksi <i>{activeJobs.length}</i></button>
          <button className={tab === "library" ? "selected" : ""} onClick={() => { setTab("library"); setFolder(null); void loadJobs(); }}><Folder size={17}/> Hasil Produksi <i>{completedJobs.length}</i></button>
          <button className={tab === "assets" ? "selected" : ""} onClick={() => { setTab("assets"); void loadAssets(); }}><Video size={17}/> Aset Kendaraan <i>{assets.length}</i></button>
        </nav>

        {tab === "generate" && <section className="studio-grid">
          <article className="studio-panel generate-panel">
            <div className="panel-title"><div><span className="studio-eyebrow">01 / CREATE</span><h2>Generate video animasi</h2></div><span className="live-pill">STUDIO</span></div>
            <label>Brand kendaraan</label>
            <div className="brand-picker"><button className={brand === "JAECOO" ? "chosen" : ""} onClick={() => setBrand("JAECOO")}>JAECOO</button><button className={brand === "OMODA" ? "chosen" : ""} onClick={() => setBrand("OMODA")}>OMODA</button></div>
            <label>Pilih topik</label>
            <select value={topic} onChange={event => { setTopic(event.target.value); setCustomTopic(""); }}>{TOPICS.map(([label, value]) => <option key={value} value={value}>{label}</option>)}</select>
            <label>Atau masukkan ide sendiri</label>
            <textarea value={customTopic} onChange={event => setCustomTopic(event.target.value)} placeholder="Contoh: bagaimana teknologi hybrid bekerja saat perjalanan jauh?"/>
            <label>Foto kendaraan (opsional)</label><select value={selectedAsset} onChange={event => setSelectedAsset(event.target.value)}><option value="">Gunakan ilustrasi animasi</option>{assets.filter(item => item.brand === brand).map(item => <option key={item.key} value={item.key}>{item.brand} {item.model} · {item.filename}</option>)}</select><button type="button" className="studio-link" onClick={() => setTab("assets")}>＋ Kelola / unggah foto kendaraan</button>
            <label>Durasi video</label>
            <div className="duration-picker">{["30", "45", "60"].map(value => <button key={value} className={duration === value ? "chosen" : ""} onClick={() => setDuration(value)}>{value} detik</button>)}</div>
            <div className="visual-style"><Film size={19}/><div><b>2D Explainer + Cartoon Motion Graphics</b><span>Ilustrasi bergerak, transisi adegan, narasi Bahasa Indonesia, dan subtitle.</span></div></div>
            <button className="studio-primary generate-button" disabled={busy} onClick={generate}>{busy ? <RefreshCw className="spin" size={18}/> : <Sparkles size={18}/>} {busy ? "Menyiapkan produksi…" : "Mulai Generate Animasi"}</button>
            <p className="studio-footnote">Catatan: hasil awal memakai template animasi dan naskah terkurasi. Periksa akurasi informasi sebelum video dipublikasikan.</p>
          </article>
          <aside className="studio-side">
            <div className="side-art"><div className="orbit orbit-a"/><div className="orbit orbit-b"/><div className="art-icon"><Clapperboard size={42}/></div><span>ANIMATION ENGINE</span></div>
            <div className="studio-panel side-card"><span className="studio-eyebrow">PRODUCTION FLOW</span><h3>Dari topik ke MP4</h3><ol><li><b>01</b><span>Naskah & alur cerita</span></li><li><b>02</b><span>Narasi Bahasa Indonesia</span></li><li><b>03</b><span>Ilustrasi dan animasi</span></li><li><b>04</b><span>Render video final</span></li></ol></div>
          </aside>
        </section>}

        {tab === "assets" && <section className="studio-section">
          <div className="section-head"><div><span className="studio-eyebrow">04 / VEHICLE LIBRARY</span><h2>Aset kendaraan</h2><p>Unggah foto mobil langsung dari galeri HP. Maksimal 10 MB per foto.</p></div><button className="refresh-button" onClick={() => void loadAssets()}><RefreshCw size={16}/> Perbarui</button></div>
          <article className="studio-panel asset-upload-panel"><label>Brand kendaraan</label><div className="brand-picker"><button className={assetBrand==="JAECOO"?"chosen":""} onClick={()=>{setAssetBrand("JAECOO");setAssetModel("J5");}}>JAECOO</button><button className={assetBrand==="OMODA"?"chosen":""} onClick={()=>{setAssetBrand("OMODA");setAssetModel("C5");}}>OMODA</button></div><label>Model</label><select value={assetModel} onChange={e=>setAssetModel(e.target.value)}>{(assetBrand==="JAECOO"?["J5","J7","J7 SHS-P ARDIS","J8 SHS-P ARDIS"]:["C5","C7","E5","O4"]).map(m=><option key={m}>{m}</option>)}</select><label>Foto kendaraan · JPG / PNG / WebP</label><input type="file" accept="image/jpeg,image/png,image/webp" disabled={assetBusy} onChange={e=>{void uploadVehicleAsset(e.target.files?.[0]);e.currentTarget.value="";}}/>{assetBusy&&<p>Mengunggah foto…</p>}</article>
          <div className="video-grid">{assets.length===0?<div className="empty-state"><Video size={28}/><b>Belum ada foto kendaraan</b><span>Pilih foto mobil dari galeri untuk mulai.</span></div>:assets.map(item=><article className="video-card" key={item.key}><div className="asset-placeholder">{item.brand} · {item.model}</div><h3>{item.filename}</h3><p>{(item.size/1048576).toFixed(1)} MB</p><button className="studio-secondary" onClick={()=>{setBrand(item.brand);setSelectedAsset(item.key);setTab("generate");}}>Pakai untuk video</button><button className="studio-link" onClick={()=>void deleteVehicleAsset(item.key)}>Hapus aset</button></article>)}</div>
        </section>}

        {tab === "process" && <section className="studio-section">
          <div className="section-head"><div><span className="studio-eyebrow">02 / LIVE MONITOR</span><h2>Proses produksi</h2><p>Pantau antrean dan progres render video animasi.</p></div><button className="refresh-button" onClick={() => void loadJobs()} disabled={loadingJobs}><RefreshCw size={16}/> Perbarui</button></div>
          {loadingJobs ? <div className="empty-state"><RefreshCw className="spin" size={24}/>Memuat proses…</div> : activeJobs.length === 0 && failedJobs.length === 0 ? <div className="empty-state"><Activity size={30}/><b>Belum ada proses aktif</b><span>Mulai generate animasi untuk melihat prosesnya di sini.</span><button className="studio-secondary" onClick={() => setTab("generate")}>Buat video pertama</button></div> : <div className="job-list">{[...activeJobs, ...failedJobs].map(job => <article className="job-card" key={job.id}><div className="job-top"><span className={"job-state " + (job.status === "failed" ? "bad" : "working")}>{job.status === "failed" ? <XCircle size={14}/> : <Clock3 size={14}/>} {statusLabel(job.status)}</span><time>{dateLabel(job.created_at)}</time></div><h3>{job.title || "Video animasi " + brandOf(job)}</h3><p>{brandOf(job)} · {job.target_duration || 45} detik · 9:16</p>{job.status === "failed" ? <div className="error-box">{job.error_message || "Produksi gagal. Coba buat ulang."}</div> : <div className="job-progress"><div><span>Progres render</span><b>{job.progress || 0}%</b></div><i><span style={{ width: Math.max(0, Math.min(100, job.progress || 0)) + "%" }}/></i></div>}</article>)}</div>}
        </section>}

        {tab === "library" && <section className="studio-section">
          <div className="section-head"><div><span className="studio-eyebrow">03 / YOUR LIBRARY</span><h2>Folder hasil produksi</h2><p>Semua video selesai tersimpan di sini dan bisa dibuka kembali.</p></div><button className="refresh-button" onClick={() => void loadJobs()} disabled={loadingJobs}><RefreshCw size={16}/> Perbarui</button></div>
          {folder ? <><button className="folder-back" onClick={() => setFolder(null)}><ArrowLeft size={16}/> Semua folder</button><div className="folder-banner"><FolderOpen size={26}/><div><b>{folder}</b><span>{folderJobs.length} video tersimpan</span></div></div>{folderJobs.length === 0 ? <div className="empty-state"><Video size={28}/><b>Folder masih kosong</b><span>Video {folder} yang selesai diproduksi akan tampil di sini.</span></div> : <div className="video-grid">{folderJobs.map(job => <article className="video-card" key={job.id}><video controls playsInline preload="metadata" src={job.outputUrl || undefined}/><div className="video-meta"><span className="job-state success"><CheckCircle2 size={14}/> Selesai</span><time>{dateLabel(job.created_at)}</time></div><h3>{job.title || "Video animasi " + folder}</h3><p>{job.target_duration || 45} detik · 9:16 {job.size_bytes ? "· " + (job.size_bytes / 1048576).toFixed(1) + " MB" : ""}</p>{job.outputUrl ? <a className="download-link" href={job.outputUrl + "&download=1"}><ArrowDownToLine size={16}/> Unduh MP4</a> : <span className="unavailable">Tautan video belum tersedia. Perbarui folder.</span>}</article>)}</div>}</> : <div className="folder-grid">{(["JAECOO", "OMODA"] as const).map(name => { const count = completedJobs.filter(job => brandOf(job) === name).length; return <button className="folder-tile" key={name} onClick={() => setFolder(name)}><span className="folder-graphic"><Folder size={30}/></span><span className="folder-info"><b>{name}</b><small>Folder video animasi</small><em>{count} video</em></span><span className="folder-arrow">›</span></button>; })}</div>}
          {completedJobs.length === 0 && !folder && <div className="library-hint">Hasil render akan otomatis masuk ke folder brand masing-masing setelah proses selesai.</div>}
        </section>}
      </>}

      <div className="studio-message"><span className="message-dot"/>{message}</div>
      <footer className="studio-footer"><span>ANIMATED VIDEO STUDIO</span><span>Mobile-first production workspace</span></footer>
    </div>
  </main>;
}
