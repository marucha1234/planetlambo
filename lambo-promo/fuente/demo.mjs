// Graba una conversación real con Lambo vía la conexión pública de ElevenLabs ConvAI.
// Uso: node demo.mjs "pregunta 1" ["pregunta 2" ...]
import fs from 'fs';
const AGENT = 'agent_1601m3mtyczvf3aaeskz38rpsc8m';
const questions = process.argv.slice(2);
const ws = new WebSocket(`wss://api.elevenlabs.io/v1/convai/conversation?agent_id=${AGENT}`);
const log = [], turns = []; let fmt = 'pcm_16000', cur = null, qi = 0, idleT = null, t0 = Date.now();
const newTurn = (role, text = '') => { cur = { role, text, chunks: [], t: (Date.now() - t0) / 1000 }; turns.push(cur); };
function idle() { clearTimeout(idleT); idleT = setTimeout(next, 3500); }
function next() {
  if (qi < questions.length) { const q = questions[qi++]; newTurn('user', q); ws.send(JSON.stringify({ type: 'user_message', text: q })); cur = null; idle(); }
  else { ws.close(); }
}
ws.onopen = () => ws.send(JSON.stringify({ type: 'conversation_initiation_client_data' }));
ws.onmessage = e => {
  const m = JSON.parse(e.data); log.push(m.type);
  if (m.type === 'conversation_initiation_metadata') { fmt = m.conversation_initiation_metadata_event.agent_output_audio_format; idle(); }
  else if (m.type === 'ping') ws.send(JSON.stringify({ type: 'pong', event_id: m.ping_event.event_id }));
  else if (m.type === 'agent_response') { if (!cur || cur.role !== 'agent') newTurn('agent'); cur.text += (cur.text ? ' ' : '') + m.agent_response_event.agent_response; idle(); }
  else if (m.type === 'audio') { if (!cur || cur.role !== 'agent') newTurn('agent'); cur.chunks.push(m.audio_event.audio_base_64); idle(); }
};
ws.onclose = ws.onerror = ev => {
  clearTimeout(idleT);
  const rate = +(fmt.match(/(\d+)/)?.[1] || 16000);
  turns.forEach((t, i) => { if (t.chunks.length) { fs.writeFileSync(`demo_${i}_${t.role}.pcm`, Buffer.concat(t.chunks.map(c => Buffer.from(c, 'base64')))); } delete t.chunks; });
  fs.writeFileSync('demo.json', JSON.stringify({ fmt, rate, turns, events: [...new Set(log)] }, null, 2));
  console.log(ev.type, fmt, JSON.stringify(turns, null, 1)); process.exit(0);
};
