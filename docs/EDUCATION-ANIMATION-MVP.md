# AI Animated Education Factory — MVP

## What this module does
Creates a vertical Indonesian educational animation from a topic without requiring user-uploaded footage. It uses a curated script library for supported EV topics, Piper Indonesian TTS, Pillow-generated 2D scenes, FFmpeg composition, subtitles and a low-volume synthetic audio bed.

## Supported first topics
- Regenerative braking
- LFP battery basics
- BEV vs HEV vs PHEV
- AC vs DC charging
- How an electric motor works

Custom topics are accepted by the form, but the current deterministic script fallback is a generic explainer and must be fact-checked before publication. This MVP does not claim to have an LLM research director. No paid video-generation API is called.

## Architecture
- Next.js `/education` mobile page
- Cloudflare Pages Function `/api/education/create`
- Existing Supabase Auth, `video_projects`, `editing_jobs`, and `render_outputs`
- Existing R2 manifest and signed output-upload gateway
- GitHub Actions `education-animation.yml`
- Piper TTS + Pillow + FFmpeg on the GitHub runner

## Workflow
1. User signs in on the existing dashboard and opens /education.
2. The Pages Function creates a project and editing job, stores a signed manifest in R2, and dispatches the workflow.
3. The runner downloads the Indonesian Piper voice, creates narration and animated scene frames, renders MP4, and uploads to the existing R2 output gateway.
4. Existing `/api/jobs/status` detects the MP4, registers the output and marks the job completed.
5. The mobile page polls status and displays the video player/download link.

## Limits
- GitHub Actions minutes, storage, Supabase, Cloudflare and Hugging Face availability are subject to their current free-tier limits.
- The first version uses deterministic scripts and vector illustration templates. It is not yet a fully generative LLM director or a character lip-sync engine.
- The selected Piper Indonesian voice is listed as MIT in the model repository, but its model card points to a dataset whose license is 'see source URL'. Treat this voice as experimental until its dataset rights are confirmed for commercial marketing use. Check every model and asset license before publication.
