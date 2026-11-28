# AI Animated Education Factory — Motion + Sound Upgrade

## What this module does
Creates vertical Indonesian educational explainers with a hook-first script, scene-specific 2D motion, animated component diagrams, moving traffic and parallax city layers, kinetic labels, captions, and a synchronized audio mix.

## Visual direction
- 9:16 output at 1080 × 1920, H.264, 30 fps.
- Each scene has its own visual treatment instead of one repeated static card.
- Battery scenes animate individual cells and charging flow.
- Electric drivetrain scenes show battery → inverter → motor, animated energy particles, a cutaway rotor, rotating spokes and torque cues.
- Road scenes include moving traffic, wheel rotation, road markings and acceleration streaks.
- Scene titles and labels enter with motion; the lower-third captions remain readable.
- This is a procedural 2D motion-graphics renderer, not frame-by-frame generative video or a fully rigged character animation system.

## Audio direction
- Indonesian Piper narration uses a slower conversational pace and revised everyday-language scripts for supported topics.
- Scene changes receive generated whoosh and pop cues; electrical and motor scenes receive matching electronic/motor textures.
- An original synthesized rhythmic bed is mixed under narration and effects.
- Important limitation: Piper remains a fixed voice and cannot reliably perform nuanced human emotion, laughter or expressive acting. The sound effects and music are procedurally synthesized, not licensed commercial sound libraries. Review the audio and licensing before commercial publication.

## Supported first topics
- Regenerative braking
- LFP battery basics
- BEV vs HEV vs PHEV
- AC vs DC charging
- How an electric motor works

Custom topics are accepted, but the deterministic fallback is a generic explainer and must be fact-checked before publication.

## Architecture
- Next.js mobile page and existing Cloudflare Pages Functions.
- Existing Supabase Auth, project/job tables, R2 manifest and signed output-upload gateway.
- GitHub Actions runner with Python, Pillow, Piper and FFmpeg.
- No paid video-generation API is called.

## Workflow
1. User starts a video job from the dashboard.
2. The Pages Function creates a project and job, stores a signed manifest in R2, and dispatches GitHub Actions.
3. The runner creates narration, scene-specific animated frames, generated music and synchronized SFX, then renders MP4.
4. The output is uploaded through the existing R2 gateway.
5. The dashboard detects the MP4 and displays the result.

## Remaining quality boundary
This upgrade materially increases object motion and sound activity, but does not yet provide a true AI storyboard director, neural expressive voice acting, lip-sync, or hand-authored professional character rigs. A more natural expressive voice will require a different voice provider/model and verified usage rights. Every model and asset license must be checked before commercial use.
