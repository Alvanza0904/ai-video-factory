"use client";

import { useState } from "react";
import {
  Activity, ArrowUpRight, Clapperboard, Cloud, Film,
  Gauge, Github, HardDrive, Layers3, Menu, Settings2,
  Sparkles, UploadCloud, WandSparkles, X
} from "lucide-react";

const genres = [
  { name: "Cinematic", detail: "Automotive, product, travel", icon: "🎬" },
  { name: "Drama & Story", detail: "Dialog, emotion, storytelling", icon: "🎭" },
  { name: "POV", detail: "First-person social content", icon: "👁️" },
  { name: "Comedy & Entertainment", detail: "Punchline, reaction, meme timing", icon: "😂" },
  { name: "Two Characters", detail: "One actor, multiple roles", icon: "🎭" },
  { name: "Review & Talking Head", detail: "Presenter, review, explanation", icon: "🎤" }
];

export default function Home() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [selectedGenre, setSelectedGenre] = useState("Auto-detect");
  const [notice, setNotice] = useState("Fondasi dashboard sudah dibuat. Upload dan AI editing akan diaktifkan setelah koneksi storage dan Re:Link dikonfigurasi.");

  return (
    <main className="shell">
      <aside className={`sidebar ${menuOpen ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-mark"><Clapperboard size={21}/></div>
          <div><strong>VIDEO FACTORY</strong><span>UNIVERSAL EDITOR</span></div>
          <button className="mobile-close" onClick={() => setMenuOpen(false)} aria-label="Tutup menu"><X size={19}/></button>
        </div>
        <div className="workspace-label">WORKSPACE</div>
        <nav>
          <a className="nav-item active" href="#"><Layers3 size={18}/> Dashboard</a>
          <a className="nav-item" href="#new-project"><UploadCloud size={18}/> Buat proyek</a>
          <a className="nav-item" href="#genres"><Film size={18}/> Gaya editing</a>
          <a className="nav-item" href="#infrastructure"><Settings2 size={18}/> Infrastruktur</a>
        </nav>
        <div className="sidebar-bottom">
          <div className="profile"><div className="avatar">A</div><div><strong>Workspace Alvan</strong><span>Personal workspace</span></div></div>
          <div className="version">AI VIDEO FACTORY · FOUNDATION 0.1</div>
        </div>
      </aside>

      {menuOpen && <button className="scrim" onClick={() => setMenuOpen(false)} aria-label="Tutup navigasi"/>}

      <section className="main">
        <header className="topbar">
          <button className="mobile-menu" onClick={() => setMenuOpen(true)} aria-label="Buka menu"><Menu size={21}/></button>
          <div className="breadcrumb">Workspace <span>/</span> Dashboard</div>
          <div className="top-status"><span className="status-dot"/> Cloud-first workspace</div>
        </header>

        <div className="content">
          <section className="welcome">
            <div>
              <div className="eyebrow"><Sparkles size={14}/> YOUR CREATIVE WORKSPACE</div>
              <h1>Ide jadi video.<br/><em>Tanpa edit manual.</em></h1>
              <p>Upload footage dari HP. AI akan memahami isi konten, menyusun cerita, memilih gaya editing, lalu menyiapkan video final.</p>
            </div>
            <div className="welcome-art"><div className="art-ring ring-one"/><div className="art-ring ring-two"/><div className="art-core"><Clapperboard size={42}/></div><span className="art-tag">AI / EDIT / EXPORT</span></div>
          </section>

          <div className="notice"><Activity size={17}/><span>{notice}</span></div>

          <section className="section" id="new-project">
            <div className="section-heading"><div><div className="eyebrow">START CREATING</div><h2>Proyek baru</h2></div><span className="muted small">Output target · 9:16 · 1080p · 30–60 detik</span></div>
            <div className="project-panel">
              <div className="upload-visual"><UploadCloud size={30}/><span>UPLOAD AREA</span></div>
              <div className="project-copy">
                <h3>Siapkan satu konten dari banyak footage</h3>
                <p>Unggah beberapa klip dalam satu proyek. Sistem nantinya menganalisis seluruh klip sebagai satu cerita, bukan mengeditnya satu per satu.</p>
                <div className="project-actions">
                  <button className="primary-button" disabled title="Menunggu konfigurasi Supabase Storage / Cloudflare R2"><UploadCloud size={17}/> Upload footage <span className="soon">SEGERA</span></button>
                  <span className="muted tiny">Upload belum diaktifkan — storage belum terhubung.</span>
                </div>
              </div>
            </div>
          </section>

          <section className="section" id="genres">
            <div className="section-heading"><div><div className="eyebrow">UNIVERSAL AI DIRECTOR</div><h2>Semua genre, satu editor</h2></div><span className="muted small">Genre otomatis menjadi pilihan utama</span></div>
            <div className="genre-grid">
              {genres.map((genre) => <button key={genre.name} className={`genre-card ${selectedGenre === genre.name ? "genre-selected" : ""}`} onClick={() => {setSelectedGenre(genre.name); setNotice(`Preferensi genre dipilih: ${genre.name}. Deteksi otomatis tetap menjadi default saat pipeline AI aktif.`);}}>
                <span className="genre-icon">{genre.icon}</span><strong>{genre.name}</strong><span>{genre.detail}</span>
              </button>)}
            </div>
            <div className="genre-footer"><span>Preferensi saat ini: <strong>{selectedGenre}</strong></span><button className="text-button" onClick={() => {setSelectedGenre("Auto-detect"); setNotice("Genre dikembalikan ke Auto-detect.");}}>Kembali ke Auto-detect <ArrowUpRight size={14}/></button></div>
          </section>

          <section className="section" id="infrastructure">
            <div className="section-heading"><div><div className="eyebrow">CLOUD PIPELINE</div><h2>Infrastruktur</h2></div><span className="muted small">Status konfigurasi awal</span></div>
            <div className="infra-grid">
              <Infra icon={<Github size={18}/>} title="GitHub Actions" state="Workflow belum diuji" detail="Cloud render worker"/>
              <Infra icon={<WandSparkles size={18}/>} title="Re:Link Gateway" state="Belum dikonfigurasi" detail="AI director & analysis"/>
              <Infra icon={<HardDrive size={18}/>} title="Storage" state="Belum dikonfigurasi" detail="Supabase / Cloudflare R2"/>
              <Infra icon={<Cloud size={18}/>} title="Vercel" state="Belum dideploy" detail="Dashboard hosting"/>
            </div>
          </section>

          <footer><span>AI VIDEO FACTORY</span><span>Built for mobile-first creation · <a href="https://github.com/Alvanza0904/ai-video-factory" target="_blank" rel="noreferrer">GitHub <ArrowUpRight size={12}/></a></span></footer>
        </div>
      </section>
    </main>
  );
}

function Infra({ icon, title, state, detail }: { icon: React.ReactNode; title: string; state: string; detail: string }) {
  return <div className="infra-card"><div className="infra-icon">{icon}</div><div className="infra-info"><strong>{title}</strong><span>{detail}</span><small>{state}</small></div><Gauge className="infra-gauge" size={17}/></div>;
}
