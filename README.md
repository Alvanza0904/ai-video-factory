# AI Video Factory

Mobile-first universal automatic video editor. Target workflow: upload multiple clips from a phone, let AI understand the footage and story, automatically select an editing style, render, quality-check, and return a finished vertical MP4.

## Product direction

Supported content genres:
- Cinematic automotive / product
- Drama and storytelling
- POV
- Comedy and entertainment
- One actor playing multiple characters
- Review and talking head
- Mixed / auto-detected formats

Target output: MP4, H.264/AAC, vertical 1080x1920, 30 fps, 30–60 seconds.

## Current foundation status

This repository currently contains the initial Next.js dashboard and a manual GitHub Actions FFmpeg smoke-test workflow.

**Not yet implemented:** authenticated multi-file upload, Supabase/R2 storage integration, Re:Link AI analysis, speech transcription, editing blueprint generation, multi-clip timeline assembly, genre-specific editing intelligence, automated sound design, AI self-review, Vercel deployment, and dashboard-triggered rendering.

Do not present these capabilities as production-ready until implemented and tested end-to-end.

## Architecture

- Next.js dashboard (Vercel deployment to be configured)
- Supabase for database and auth (to be configured)
- Cloudflare R2 for source and final video storage (to be configured)
- Re:Link Gateway for AI orchestration (server-side secret only)
- GitHub Actions Ubuntu runner for on-demand FFmpeg processing
- FFmpeg as the first rendering engine; Remotion is optional for later compositions

## Local development

```bash
npm install
npm run dev
```

## GitHub Actions smoke test

Open Actions → AI Video Factory - Cloud Render → Run workflow. Provide an HTTPS URL to a video file you own or have permission to process. The job creates a basic vertical MP4 and stores it as a short-lived workflow artifact.

This is only a rendering infrastructure smoke test. It is not the final AI editor and currently accepts one source video, not a multi-footage project.

## Secrets and security

Never commit API keys, Supabase service-role keys, R2 credentials, signed URLs, or user footage into this public repository. Configure secrets in GitHub Actions / Vercel settings. Keep privileged storage operations server-side.

## Cost and privacy notes

GitHub Actions usage, artifact limits, and retention depend on GitHub's current plan and policies. Public repository runner eligibility does not make storage, AI tokens, hosting, or every external service unlimited or universally free. Source videos should be private objects in storage, accessed with short-lived signed URLs.

## Hosting

The initial mobile-first dashboard is configured for Cloudflare Pages static export at `https://ai-video-factory-43b.pages.dev`. The Pages project is connected to this public GitHub repository. Production deployment must be verified after the first build completes.
