# Video Lambo · fuente

- `promo.html`: versión original (32 s, sin demo).
- `promo_demo.html`: versión con interrupción: glitch → "Pará. Mejor escuchalo en vivo." → escena "Demo real · sin editar" → sigue el video.
  Lee `demo_data.js` (`window.DEMO = {dur, turns, env}`); sin datos usa un placeholder.
- `demo.mjs`: graba la conversación real con Lambo (ElevenLabs ConvAI WebSocket).
- `render2.mjs`: `PAGE=promo_demo.html node render2.mjs frames 1080 1920 fv 30` (y 1920 1080 para 16:9).
- `music.py`: música original (120 BPM). Para la versión con demo: música 0–8 s, glitch, audio de la demo, música desde 14 s.
