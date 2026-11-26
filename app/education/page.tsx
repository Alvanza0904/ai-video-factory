"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Clapperboard, Download, Film, LoaderCircle, Sparkles, Volume2 } from "lucide-react";

const API = "https://sdmnhhgcenhzfnvzwyzo.supabase.co";
const ANON = "sb_publishable_uxSrstD_fl3oJS1BkfvtkA__KzQtI7A";
type Session = { access_token: string; refresh_token?: string; expires_at?: number; user: { id: string; email?: string } };
type Status = { job?: { status: string; progress: number; error_message?: string | null }; outputUrl?: string | null; error?: string };

const topics = [
  ["Regenerative braking: bagaimana mobil listrik mengembalikan energi saat melambat?", "regenerative braking"],
  ["Mengenal baterai LFP pada kendaraan listrik", "baterai LFP"],
  ["Apa perbedaan BEV, HEV, dan PHEV?", "perbedaan BEV, HEV, dan PHEV"],
  ["Apa bedanya pengisian daya AC dan DC?", "perbedaan charging AC dan DC"],
  ["Bagaimana motor listrik menggerakkan mobil?", "cara kerja motor listrik"]
];

export default function EducationStudio() {
  const [session,setSession]=useState<Session|null>(null);
  const [brand,setBrand]=useState("JAECOO");
  const [topic,setTopic]=useState(topics[0][1]);
  const [customTopic,setCustomTopic]=useState("");
  const [duration,setDuration]=useState("45");
  const [jobId,setJobId]=useState("");
  const [status,setStatus]=useState("");
  const [progress,setProgress]=useState(0);
  const [outputUrl,setOutputUrl]=useState("");
  const [message,setMessage]=useState("Pilih topik, lalu biarkan studio membuat video edukasi animasi.");
  const [busy,setBusy]=useState(false);

  useEffect(()=>{
    try {
      const raw=localStorage.getItem("avf-session");
      if(raw) setSession(JSON.parse(raw) as Session);
      const saved=localStorage.getItem("avf-education-job");
      if(saved) { setJobId(saved); setStatus("restoring"); setMessage("Memulihkan proses video terakhir…"); }
    } catch { setMessage("Sesi tidak dapat dibaca. Silakan masuk kembali."); }
  },[]);

  const authorizedFetch=useCallback(async(url:string,init:RequestInit,active:Session)=>{
    const send=(token:string)=>{
      const headers=new Headers(init.headers||{});
      headers.set("Authorization","Bearer "+token);
      return fetch(url,{...init,headers});
    };
    let response=await send(active.access_token);
    if(response.status!==401||!active.refresh_token) return response;
    const refresh=await fetch(API+"/auth/v1/token?grant_type=refresh_token",{
      method:"POST",headers:{"Content-Type":"application/json",apikey:ANON},
      body:JSON.stringify({refresh_token:active.refresh_token})
    });
    if(!refresh.ok) return response;
    const next=await refresh.json() as {access_token:string;refresh_token?:string;expires_in?:number};
    const updated={...active,access_token:next.access_token,refresh_token:next.refresh_token||active.refresh_token,expires_at:Math.floor(Date.now()/1000)+(next.expires_in||3600)};
    localStorage.setItem("avf-session",JSON.stringify(updated));
    setSession(updated);
    response=await send(updated.access_token);
    return response;
  },[]);

  useEffect(()=>{
    if(!session||!jobId) return;
    let active=true;
    const poll=async()=>{
      try{
        const res=await authorizedFetch("/api/jobs/status?job_id="+encodeURIComponent(jobId),{headers:{}},session);
        const data=await res.json() as Status;
        if(!res.ok) throw new Error(data.error||"Tidak dapat memeriksa status.");
        if(!active||!data.job) return;
        setStatus(data.job.status); setProgress(data.job.progress||0);
        if(data.job.status==="completed"&&data.outputUrl){
          setOutputUrl(data.outputUrl);setMessage("Video edukasi selesai dibuat. Periksa hasilnya sebelum dipublikasikan.");
          localStorage.removeItem("avf-education-job");
        }else if(data.job.status==="failed"){
          setMessage(data.job.error_message||"Proses gagal. Coba lagi dengan topik lain.");
          localStorage.removeItem("avf-education-job");
        }else setMessage("Proses berjalan di cloud. Kamu boleh meninggalkan halaman dan kembali lagi nanti.");
      }catch(e){if(active)setMessage((e as Error).message);}
    };
    void poll();
    const timer=window.setInterval(poll,10000);
    return()=>{active=false;window.clearInterval(timer);};
  },[session,jobId,authorizedFetch]);

  async function createVideo(){
    if(!session){setMessage("Masuk melalui dashboard utama terlebih dahulu.");return;}
    const selected=(customTopic.trim()||topic).trim();
    if(selected.length<8){setMessage("Topik minimal 8 karakter.");return;}
    setBusy(true);setOutputUrl("");setStatus("queued");setProgress(1);
    try{
      const res=await authorizedFetch("/api/education/create",{
        method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({brand,topic:selected,duration:Number(duration)})
      },session);
      const data=await res.json() as {jobId?:string;error?:string};
      if(!res.ok||!data.jobId) throw new Error(data.error||"Tidak dapat memulai pembuatan video.");
      localStorage.setItem("avf-education-job",data.jobId);
      setJobId(data.jobId);setStatus("analyzing");setMessage("Job berhasil dibuat. Menyiapkan narasi, ilustrasi, dan animasi 2D.");
    }catch(e){setStatus("failed");setMessage((e as Error).message);}
    finally{setBusy(false);}
  }

  return <main className="edu-shell">
    <header className="edu-top"><Link href="/" className="back"><ArrowLeft size={17}/> Dashboard</Link><div className="logo"><span><Clapperboard size={19}/></span><div><b>ANIMATED EDUCATION</b><small>OMODA × JAECOO PALEMBANG</small></div></div><div className="signed">{session?"Workspace aktif":"Belum masuk"}</div></header>
    <div className="edu-content">
      <section className="hero"><div className="eyebrow"><Sparkles size={14}/> AUTOMATED EXPLAINER VIDEO</div><h1>Topik jadi video.<br/><em>Tanpa rekam, tanpa edit.</em></h1><p>Buat video edukasi otomotif dengan naskah, suara narator Bahasa Indonesia, ilustrasi bergerak, motion graphics, dan subtitle secara otomatis.</p></section>
      <div className="layout">
        <section className="panel form-panel">
          <div className="panel-head"><div><span className="kicker">CREATE NEW VIDEO</span><h2>Buat video edukasi</h2></div><span className="pill">FREE-FIRST MVP</span></div>
          <label>Brand</label>
          <div className="brand-select"><button className={brand==="JAECOO"?"chosen":""} onClick={()=>setBrand("JAECOO")}>JAECOO</button><button className={brand==="OMODA"?"chosen":""} onClick={()=>setBrand("OMODA")}>OMODA</button></div>
          <label>Topik edukasi</label>
          <select value={topic} onChange={e=>{setTopic(e.target.value);setCustomTopic("");}}>
            {topics.map(([label,value])=><option key={value} value={value}>{label}</option>)}
          </select>
          <label>Atau tulis topik sendiri</label>
          <input value={customTopic} onChange={e=>setCustomTopic(e.target.value)} placeholder="Contoh: bagaimana cara kerja sistem hybrid?"/>
          <label>Durasi target</label>
          <div className="duration">{["30","45","60"].map(v=><button key={v} className={duration===v?"chosen":""} onClick={()=>setDuration(v)}>{v} detik</button>)}</div>
          <div className="style-note"><Film size={17}/><div><b>Gaya visual otomatis</b><span>Campuran 2D explainer, cartoon, dan motion graphics.</span></div></div>
          <div className="style-note"><Volume2 size={17}/><div><b>Narator Bahasa Indonesia</b><span>Suara sintetis natural, ramah, dan energik.</span></div></div>
          <button className="generate" disabled={busy||!session} onClick={createVideo}>{busy?<LoaderCircle className="spin" size={18}/>:<Sparkles size={18}/>} {busy?"Menyiapkan…":"Generate Video Otomatis"}</button>
          {!session&&<p className="login-note">Masuk di <Link href="/">dashboard utama</Link> terlebih dahulu. Sesi login akan digunakan bersama.</p>}
          <p className="disclaimer">MVP awal memakai naskah edukasi terkurasi dan template animasi 2D. Topik khusus perlu diperiksa faktanya sebelum dipublikasikan.</p>
        </section>
        <section className="panel result-panel">
          <div className="panel-head"><div><span className="kicker">VIDEO OUTPUT</span><h2>Hasil produksi</h2></div><span className={"status "+(status==="completed"?"done":status==="failed"?"failed":"")}>{status||"READY"}</span></div>
          {outputUrl?<><video controls playsInline preload="metadata" src={outputUrl} className="video"/><a className="download" href={outputUrl+"&download=1"}><Download size={17}/> Unduh MP4</a></>:<div className="empty"><div className="empty-art"><Clapperboard size={46}/><span>2D</span></div><b>Video kamu akan muncul di sini</b><p>Setelah proses selesai, kamu bisa langsung menonton dan mengunduh MP4.</p></div>}
          {jobId&&<div className="progress-wrap"><div className="progress-meta"><span>{status==="completed"?"Selesai":status==="failed"?"Gagal":"Proses produksi"}</span><b>{progress}%</b></div><div className="bar"><i style={{width:Math.max(0,Math.min(100,progress))+"%"}}/></div></div>}
          <div className="message">{message}</div>
          <div className="steps"><span>01 Naskah</span><span>02 Voice</span><span>03 Animasi</span><span>04 Render</span></div>
        </section>
      </div>
      <footer>AI ANIMATED EDUCATION FACTORY <span>Powered by open-source rendering tools</span></footer>
    </div>
    <style jsx>{`
      .edu-shell{min-height:100vh;background:radial-gradient(ellipse at 75% 8%,#203326 0,transparent 32%),#090d12;color:#f3f6f8;font-family:Arial,sans-serif}
      .edu-top{height:70px;border-bottom:1px solid #26313a;display:flex;align-items:center;justify-content:space-between;padding:0 max(22px,calc((100% - 1180px)/2));gap:18px}
      .back{display:flex;align-items:center;gap:7px;color:#b6c2ca;text-decoration:none;font-size:13px}.logo{display:flex;align-items:center;gap:10px}.logo>span{width:36px;height:36px;border-radius:11px;background:#b8f36a;color:#15210d;display:grid;place-items:center}.logo b,.logo small{display:block}.logo b{font-size:11px;letter-spacing:1.3px}.logo small{font-size:9px;color:#87969e;letter-spacing:1px;margin-top:4px}.signed{font-size:11px;color:#a8b5bd}
      .edu-content{max-width:1120px;margin:auto;padding:42px 22px 28px}.hero{padding:20px 0 35px}.eyebrow,.kicker{font-size:10px;font-weight:700;letter-spacing:1.8px;color:#b8f36a;display:flex;align-items:center;gap:7px}.hero h1{font-size:clamp(38px,6vw,64px);line-height:1.03;letter-spacing:-2.8px;margin:18px 0}.hero h1 em{font-style:normal;color:#b8f36a}.hero p{max-width:650px;color:#a4b1b9;line-height:1.8;font-size:14px}
      .layout{display:grid;grid-template-columns:1fr 1fr;gap:18px}.panel{background:#111920;border:1px solid #293640;border-radius:17px;padding:23px;min-width:0}.panel-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:23px}.panel h2{font-size:21px;margin:7px 0 0;letter-spacing:-.5px}.pill,.status{font-size:9px;letter-spacing:1px;border:1px solid #43523a;color:#b8f36a;border-radius:20px;padding:6px 9px}.status{color:#aab6bf;border-color:#3a4650;text-transform:uppercase}.status.done{color:#b8f36a;border-color:#657e42}.status.failed{color:#ff9d93;border-color:#88544e}
      label{display:block;color:#aab7bf;font-size:11px;margin:17px 0 8px}select,input{width:100%;padding:13px 12px;border:1px solid #34434d;border-radius:9px;background:#0b1117;color:#f4f7f9;font-size:13px;outline:none}select:focus,input:focus{border-color:#b8f36a}.brand-select,.duration{display:flex;gap:9px}.brand-select button,.duration button{flex:1;padding:12px;border:1px solid #34434d;border-radius:9px;background:#0b1117;color:#c0cbd1}.brand-select .chosen,.duration .chosen{border-color:#b8f36a;background:#1b291a;color:#d6ff9a}
      .style-note{display:flex;gap:12px;align-items:center;margin-top:15px;padding:12px;border:1px solid #2b3942;border-radius:10px;color:#b8f36a}.style-note div{min-width:0}.style-note b,.style-note span{display:block}.style-note b{font-size:11px;color:#e8eef0}.style-note span{font-size:10px;color:#91a0a8;margin-top:4px;line-height:1.5}
      .generate,.download{width:100%;display:flex;align-items:center;justify-content:center;gap:9px;margin-top:20px;padding:14px;border:0;border-radius:10px;background:#b8f36a;color:#16200d;font-size:13px;font-weight:800;text-decoration:none}.generate:disabled{opacity:.45;cursor:not-allowed}.login-note,.disclaimer{font-size:10px;line-height:1.6;color:#91a0a8}.login-note a{color:#c8f68d}.disclaimer{margin:13px 0 0}
      .empty{min-height:340px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;color:#e6ecef}.empty-art{width:112px;height:112px;border-radius:30px;background:#1d2c35;color:#b8f36a;display:grid;place-items:center;position:relative;margin-bottom:22px}.empty-art span{position:absolute;right:-7px;bottom:-7px;border-radius:9px;background:#b8f36a;color:#16200d;padding:6px 8px;font-size:11px;font-weight:bold}.empty p{max-width:270px;color:#93a1a9;font-size:11px;line-height:1.7}.video{width:100%;max-height:620px;background:#05080b;border-radius:12px}.download{margin-top:13px}.progress-wrap{margin-top:18px}.progress-meta{display:flex;justify-content:space-between;font-size:11px;color:#aebbc2}.bar{height:7px;background:#26343d;border-radius:10px;margin-top:9px;overflow:hidden}.bar i{display:block;height:100%;background:#b8f36a;border-radius:10px;transition:width .3s}.message{margin-top:17px;background:#17231b;border:1px solid #33452d;border-radius:10px;padding:12px;color:#c9d9bd;font-size:11px;line-height:1.6}.steps{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}.steps span{font-size:9px;color:#9eabb2;border:1px solid #34414a;border-radius:20px;padding:6px 9px}footer{display:flex;justify-content:space-between;gap:10px;border-top:1px solid #27333b;margin-top:38px;padding-top:17px;color:#89969e;font-size:9px;letter-spacing:1px}footer span{letter-spacing:0}
      .spin{animation:spin 1s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}
      @media(max-width:760px){.edu-top{height:60px;padding:0 15px}.logo b{font-size:9px}.logo small{font-size:7px}.signed{font-size:9px}.back{font-size:11px}.edu-content{padding:25px 15px}.hero{padding:16px 0 23px}.hero h1{font-size:39px;letter-spacing:-1.8px}.hero p{font-size:12px}.layout{grid-template-columns:1fr}.panel{padding:17px}.empty{min-height:250px}footer{flex-direction:column}}
    `}</style>
  </main>;
}
