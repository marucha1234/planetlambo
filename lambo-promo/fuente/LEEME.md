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

## Versión final: original + voces reales (lambo-voz-real-*.mp4, 38 s)
- `promo_v3.html`: el video original; la escena de conversación usa el audio real (cliente + Lambo) y en la revelación
  de LAMBO suena su "Hola, soy Lambo." real. Lee `clips.js`.
- `clips.py`: corta los clips reales de la conversación y mezcla con `music3.py` (música re-arreglada a 38 s, con ducking).
- Render: `PAGE=promo_v3.html node render2.mjs frames 1080 1920 fv3 30`.
