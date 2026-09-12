---
description: Produce a ~30-40s TTS-narrated teaser video from real screen-captured site footage, reviewed as a standalone file before any site changes
---

# Teaser video for Sept 15

**Standing rule for this command, stricter than usual given the timing:** build and fully review
the finished video as a standalone file *before touching any file in the actual site*. If anything
in the pipeline is unreliable or takes too long to get right, stop and report rather than pushing a
half-working version live. The final site change (Phase 5) should be small enough to trivially
revert on its own if anything is found wrong after the fact.

## Phase 1 — Check dependencies before writing anything (read-only)

1. Check whether `ffmpeg` is available (`ffmpeg -version`). If not, check whether it can be
   installed quickly and safely via an existing package manager already on the machine (`winget`
   or `choco`, whichever is present) — do not install anything without reporting first.
2. Confirm Windows' built-in TTS is usable via PowerShell:
   `Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).GetInstalledVoices() | % { $_.VoiceInfo.Name }`
   — report which voices are available.
3. Confirm Playwright (already used for `/verify-site`) is installed and can launch Chromium with
   video recording enabled (`browserType.launchPersistentContext` with `recordVideo` produces a
   `.webm` file — confirm this works with a trivial test capture before building the real script).

**Report all three results before proceeding.** If ffmpeg is unavailable and can't be installed
without meaningful risk/time, stop and report — the fallback (silent video + separately-hosted
audio player, or captions-only with no audio muxing) should be a conscious decision, not a fallback
discovered mid-build.

## Phase 2 — Write the teaser script (short, three beats, ~30-40 seconds total)

Target ~90-110 words total, timed to these three beats:

1. **Hook (~10-12s):** the core concept — something close to "We gave a model a question and
   accidentally also gave it the answer" (already drafted in `docs/PI_DEFENSE_PREP.md` §12.1) —
   paired with the site's core-question diagram or causal DAG.
2. **Live mechanism (~12-15s):** narrate over an actual recorded interaction with the live
   visualizer — toggling the vasopressor switch, the DAG edge lighting up, the gauge moving. This
   is the most visually compelling beat and should get the most time.
3. **Close (~8-10s):** the six-variant chart with Variant F called out, ending on a clear
   call-to-action pointing to the live site.

Write the exact narration text for each beat as a plain-text file (`docs/teaser_script.txt` or
similar), with each beat's line and target duration marked — this becomes the input to Phase 3.

## Phase 3 — Generate narration audio locally

Use PowerShell's `System.Speech.Synthesis` to render each beat's line to a separate `.wav` file,
then check actual spoken duration against the target (speech rate is somewhat adjustable via the
synthesizer's `Rate` property — use this to nudge timing rather than padding/cutting the script
awkwardly). Concatenate the three `.wav` files into one narration track in the correct order, with
short silences between beats matching the visual cuts planned in Phase 4.

Report the final total narration duration once assembled.

## Phase 4 — Record the visual footage

Using Playwright against the locally-built site (`npm run build`, serve locally — do not record
against any external URL), record three short clips matching the three beats:

1. The homepage's core-question diagram or the causal DAG on `proof.html`/`mechanisms.html`
   (whichever renders more clearly at video resolution — your call, state which and why).
2. An actual interaction with `/visualizer/`: toggle the vasopressor switch, let the DAG/gauge
   animate, hold briefly on the result. This must be a genuine recorded interaction, not a static
   screenshot held for the same duration — the whole point is that it's real, working footage.
3. The six-variant chart on `/showcase/`, with Variant F's point visible.

Match each clip's length reasonably to its corresponding narration beat's actual duration from
Phase 3 (exact frame-sync isn't necessary for a teaser — approximate alignment is fine).

## Phase 5 — Assemble and review (still not touching the site)

Use `ffmpeg` to: concatenate the three video clips in order, overlay the narration track from
Phase 3, and export a single `.mp4` (H.264, web-compatible) to a location outside `src/` (e.g.
`docs/teaser_output.mp4`) — explicitly not yet in the built site.

**Stop here and report the finished file's path and duration.** Do not proceed to Phase 6 without
confirmation the video has actually been watched and approved — this is a hard gate, not a
formality.

## Phase 6 — Minimal, additive, reversible site embed (only after Phase 5 is approved)

Add the approved video to `src/showcase.html` (or the homepage, your recommendation — state which
and why) as a small, clearly-labeled addition — e.g. a "Watch the 30-second overview" card with an
embedded `<video>` element — **without removing or restructuring any existing content**. This
should be a single, small, easily-revertible commit: if a problem is found after the fact, removing
this one addition should not require touching anything else.

Copy the video file into `src/assets/` (or a dedicated `src/assets/video/` directory), add the
passthrough copy config to `.eleventy.js` if needed, rebuild, and confirm the video actually plays
in a real browser at both desktop and mobile width before committing.

## Reporting

Report after every phase. Phase 5's gate is the most important one in this command — do not treat
it as optional given how close this is to the event.
