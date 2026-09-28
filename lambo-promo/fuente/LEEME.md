# Video Lambo · fuente

- `promo.html`: versión original (32 s, sin demo).
- `promo_demo.html`: versión con interrupción: glitch → "Pará. Mejor escuchalo en vivo." → escena "Demo real · sin editar" → sigue el video.
  Lee `demo_data.js` (`window.DEMO = {dur, turns, env}`); sin datos usa un placeholder.
- `demo.mjs`: graba la conversación real con Lambo (ElevenLabs ConvAI WebSocket).
- `render2.mjs`: `PAGE=promo_demo.html node render2.mjs frames 1080 1920 fv 30` (y 1920 1080 para 16:9).
- `music.py`: música original (120 BPM). Para la versión con demo: música 0–8 s, glitch, audio de la demo, música desde 14 s.

## Demo real (conversación grabada con Lambo)
- `build_demo.py`: toma el mp3 de la conversación (ElevenLabs, conv_3701m3mwrdkgf4evqrrjrwxh1pqw), corta 3 turnos reales
  (saludo de Lambo · pedido del cliente · propuesta de Lambo) sin alterar las voces y genera `demo_audio.wav` + `demo_data.js`
  (transcripción, tiempos y envolvente de la onda). El mp3 original no está en el repo.
- `mix.py`: música 0–8 s + glitch + demo + música desde 14 s → `mix_demo.wav`.
- Render: `PAGE=promo_demo.html node render2.mjs frames 1080 1920 fv2 30` (60 s).
