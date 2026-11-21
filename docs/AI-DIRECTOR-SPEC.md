# Universal AI Director — Specification

The AI Director is genre-aware but not genre-locked. It analyzes all footage in a project, then produces a deterministic editing blueprint for the rendering worker.

## Inputs
- Project ID and optional creative brief.
- Asset IDs, media metadata, duration, orientation, frame rate, and audio presence.
- Sampled keyframes with timestamps.
- Audio transcript and speaker labels when available.
- User-provided music and sound-effect asset IDs with licensing metadata.

## Classification
Primary genre: cinematic, drama, POV, comedy, two_character, review, mixed, or other. Include confidence and a short story summary. Auto-detection is the default; user preferences are hints, not forced labels.

## Multi-character continuity
For one-person/two-character skits, combine transcript turn-taking with frame/shot evidence. Track role labels, camera position, wardrobe cues, and reaction shots. If identity is ambiguous, do not infer names or fabricate turns. Preserve dialogue order unless the user explicitly requests a creative restructure.

## Blueprint contract
The versioned JSON contract is in `schemas/editing-blueprint.v1.schema.json`. It records:
- Output dimensions, frame rate, duration, and codecs.
- Ordered source ranges and timeline placement.
- Genre-specific purpose, transitions, and visual profile.
- Music, ambience, and sound-effect cues.
- Caption text, timing, style, and speaker label.
- Quality-control requirements.

## Execution boundary
The AI Director does not render video. It proposes source ranges and edit decisions. A deterministic worker validates the blueprint and executes only supported operations. Unsupported effects must fail clearly or use a documented safe fallback; never silently claim an effect was applied.

## Quality gates
1. Every source range exists and is within its asset duration.
2. Timeline has no unintended gaps or overlaps.
3. Final duration is 30–60 seconds.
4. Dialogue is not clipped and subtitles match transcript.
5. No unsupported factual claims are introduced.
6. Vehicle/product visual identity remains unchanged.
7. Audio does not clip and speech remains intelligible.
8. Rendered MP4 is decodable and matches 1080x1920 / 30 fps / H.264 / AAC.
