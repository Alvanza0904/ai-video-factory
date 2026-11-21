# AI Video Factory — Implementation Roadmap

## Phase 0 — Foundation
- [x] Create public repository
- [x] Add mobile-first Next.js dashboard shell
- [x] Add genre overview and honest infrastructure states
- [x] Add GitHub Actions web build validation
- [x] Add manual FFmpeg rendering smoke-test workflow
- [ ] Confirm CI build is green

## Phase 1 — Cloud project setup
- [ ] Choose commercial-compatible hosting plan/provider
- [ ] Connect deployment to Git repository
- [ ] Provision private object storage (R2)
- [ ] Provision Supabase project or confirm intended existing project
- [ ] Add server-side secrets without committing values
- [ ] Add authentication and private project ownership

## Phase 2 — Secure footage ingestion
- [ ] Create project and asset schema
- [ ] Implement signed upload URLs
- [ ] Support multiple source clips per project
- [ ] Validate file type, size, duration, and ownership
- [ ] Store metadata and upload progress

## Phase 3 — AI understanding
- [ ] Verify Re:Link API base URL, model catalog, and supported modalities
- [ ] Implement provider adapter and health check
- [ ] Extract thumbnails/keyframes and audio tracks
- [ ] Transcribe speech and diarize speakers where supported
- [ ] Classify genre, scenes, speakers, mood, and story beats
- [ ] Produce a validated, versioned editing blueprint

## Phase 4 — Universal editing engine
- [ ] Build deterministic FFmpeg timeline renderer
- [ ] Multi-clip selection, trimming, ordering, and transitions
- [ ] Genre-aware pacing and visual treatment
- [ ] Music and sound-effect placement with licensed/user-provided assets
- [ ] Subtitle generation and burn-in
- [ ] Preserve original vehicle/product geometry and source truth

## Phase 5 — Quality control
- [ ] Validate output duration, dimensions, codecs, audio, and black frames
- [ ] Compare rendered result against blueprint
- [ ] Limited repair pass and rerender
- [ ] Store render logs and provenance

## Phase 6 — Mobile workflow
- [ ] Real upload UI
- [ ] Project queue and progress states
- [ ] Preview and download
- [ ] Retry/cancel and cleanup controls
- [ ] End-to-end test from mobile browser

## Important
GitHub Actions is a useful on-demand prototype worker, not a permanent video-storage service or unlimited free compute. Review current GitHub limits and usage policies before production. Keep user videos in private object storage and use short-lived signed URLs.
