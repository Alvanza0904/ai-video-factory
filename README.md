# Animated Video Studio

Workspace mobile-first untuk membuat video animasi edukasi otomotif OMODA dan JAECOO.

## Fitur utama
- **Generate Animasi**: pilih brand, topik, dan durasi video.
- **Proses Produksi**: pantau antrean dan progres render secara otomatis.
- **Folder Hasil Produksi**: galeri video final, dipisah ke folder OMODA dan JAECOO, dengan pemutar dan unduhan MP4.

## Arsitektur
- Next.js App Router + Cloudflare Pages Functions.
- Supabase Auth dan Postgres untuk akun, proyek, dan riwayat job.
- Cloudflare R2 untuk manifest privat dan file video final.
- GitHub Actions untuk render animasi Python + FFmpeg + Piper.

## Render animasi
Workflow aktif: `.github/workflows/education-animation.yml`
Renderer: `scripts/education_animation.py`
Smoke test: `scripts/education_smoke_test.py`

## Pengembangan
```bash
npm install
npm run dev
```

Aplikasi utama: `/`. Rute lama `/education` diarahkan ke halaman utama.
