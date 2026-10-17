# Recording guide — 60-second demo

Target: one take, 60 seconds, 1080p, 30 fps, narration aligned to `SCRIPT-60s.md`.
Subtitle file: `VOICEOVER.txt` (feed to TTS or transcribe).

---

## Tooling option A — ffmpeg (Linux, recommended)

### 1. Capture screen + mic

```bash
# Full screen, 30 fps, system default mic:
ffmpeg -f x11grab -r 30 -s 1920x1080 -i :0.0 \
       -f pulse -i default \
       -c:v libx264 -preset fast -crf 23 \
       -c:a aac -b:a 128k \
       -movflags +faststart \
       demo/raw.mp4
```

- Replace `:0.0` with the display from `echo $DISPLAY` if not `:0`.
- If you only want a window, use `-f x11grab` with `-i :0.0+X,Y` and the window size.
- Stop with `q` in the ffmpeg terminal or Ctrl+C.

### 2. Trim to exactly 60s (if you over-ran)

```bash
ffmpeg -ss 0 -t 60 -i demo/raw.mp4 -c copy demo/trimmed.mp4
```

### 3. Burn in subtitles (from VOICEOVER.txt)

Create an SRT first (one cue per beat from SCRIPT-60s.md, times already given),
then:

```bash
ffmpeg -i demo/trimmed.mp4 \
       -vf "subtitles=demo/captions.srt:force_style='Fontsize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2'" \
       -c:a copy \
       demo/final-60s.mp4
```

### 4. Verify

```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 demo/final-60s.mp4
# expect ~60.0
```

---

## Tooling option B — OBS Studio

1. Source: Display Capture (full screen) + Audio Input Capture (mic).
2. Settings → Output → Recording: MP4, x264, CBR 6000 Kbps, 30 fps.
3. Settings → Video: 1920x1080 base, 1920x1080 output, 30 fps.
4. Start Recording, run the shotlist, Stop Recording.
5. Burn subtitles with the ffmpeg command in step 3 above.

---

## Narration

- Read `VOICEOVER.txt` aloud, or feed it to a TTS engine (piper, espeak, or a cloud
  TTS). Match pacing to the timestamps in `SCRIPT-60s.md` (~145 wpm).
- Record narration in a quiet room; normalize with `ffmpeg -af loudnorm`.
- If recording narration separately, mux: `ffmpeg -i video.mp4 -i voice.wav -c:v copy -c:a aac -shortest out.mp4`.

## TTS alignment tip

If the TTS runs long, do not speed up the video — trim words from `VOICEOVER.txt`
and re-render. The 60s limit is a submission requirement, not a suggestion.

## Deliverable

`demo/final-60s.mp4` — 60 seconds, 1080p, burned-in subtitles, testnet banner visible.