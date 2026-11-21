# Mobile upload integration

- Supabase Auth authenticates the user.
- RLS-protected REST calls create projects and media metadata.
- Cloudflare Pages Function uses the MEDIA_BUCKET R2 binding.
- Multipart uploads use 8 MiB chunks, so large phone videos do not need one giant request.
- Object keys are scoped by authenticated user ID and project ID.
- R2 objects remain private; do not expose a public bucket for raw footage.

The upload path is complete only after the Pages deployment has picked up the R2 binding in wrangler.toml and the function is tested against the live bucket.
