# AI Animated Education Factory — Motion Editing Upgrade

## Visual output
- Vertical 9:16, 1080 × 1920, 30 fps.
- Scene-specific visual compositions: driving car, battery cells charging, inverter and motor energy flow, rotating rotor, torque arcs, AC/DC waveforms, charts and checklists.
- Continuous eased movement, animated particles, moving wheels, road motion, rotating motor components and bounded camera movement.
- Scene transitions are edited with alternating wipes, fades and directional transitions.
- Captions use a dedicated safe-area panel, larger type and a maximum of three lines. Each scene is timed against its actual generated speech duration.

## Voice
- The current prototype uses Microsoft Edge neural Indonesian voice id-ID-ArdiNeural through the community edge-tts client.
- The worker generates each spoken scene separately and uses the actual audio duration for scene timing.
- This is a more natural neural voice than the former local Piper news voice, but it is not expressive voice acting and the unofficial Edge TTS route has no production SLA or clear commercial API terms. For commercial-scale use, configure an official licensed TTS provider.

## Sound and editing
- Generated whoosh, impact, click, electric and motor cues are placed at scene boundaries and action beats.
- A rhythmic electronic bed is mixed beneath speech; effects have their own gain and are kept audible in the final mix.
- All audio is normalized and limited to reduce clipping.

## Supported topics
- Regenerative braking
- LFP battery basics
- BEV vs HEV vs PHEV
- AC vs DC charging
- How an electric motor works

Custom topics still use a generic deterministic script and must be fact-checked.

## Workflow
1. Cloudflare Pages Function creates the project/job and signed manifest.
2. GitHub Actions runner creates neural narration, scene clips, transitions and audio mix.
3. The final MP4 uploads to the existing R2 gateway.
4. The dashboard reconciles the render output and displays the video.

## Quality boundary
This is procedural 2D motion graphics, not fully generative video. The system still needs richer topic-specific storyboards, licensed sound libraries and a licensed expressive voice provider to reach a premium studio standard. Do not claim commercial clearance for the community Edge TTS route.
