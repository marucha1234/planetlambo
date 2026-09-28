# Arma la demo con el audio REAL de la conversación con Lambo (solo cortes entre turnos, sin alterar las voces)
import numpy as np, subprocess, json, imageio_ffmpeg
FF=imageio_ffmpeg.get_ffmpeg_exe(); SR=48000
x=np.frombuffer(subprocess.run([FF,'-v','error','-i','conv.mp3','-af','loudnorm=I=-15:TP=-1.5','-f','f32le','-ac','1','-ar',str(SR),'-'],capture_output=True).stdout,np.float32).copy()
# (src_start, src_end, role, [(src_t, texto)])
SEGS=[
 (0.0,10.35,'agent',[(0.0,'Hola, soy Lambo. En Planetlambo juntamos creatividad publicitaria y producción'),(5.0,'con IA de vanguardia para que tu marca llegue antes que nadie. ¿Qué querés lanzar?')]),
 (24.6,28.95,'user',[(24.6,'Quiero producir una campaña linda para mi chiringuito de playa.')]),
 (60.8,76.3,'agent',[(60.8,'Entonces lo que podemos hacer es una campaña que funciona en redes sociales'),(65.0,'y en el punto de venta, con mucho volumen de contenido sin que te cueste una fortuna.'),(69.5,'Podemos generar videos, fotos,'),(72.0,'historias, todo con IA, adaptado al estilo de tu chiringuito.')]),
]
GAP=0.45; LEAD=0.3
out=[np.zeros(int(LEAD*SR),np.float32)]; t=LEAD; turns=[]; cuts=[]
for a,b,role,phr in SEGS:
    seg=x[int(a*SR):int(b*SR)].copy(); f=int(.03*SR); seg[:f]*=np.linspace(0,1,f); seg[-f:]*=np.linspace(1,0,f)
    ends=[p[0] for p in phr[1:]]+[b]
    for (ps,txt),pe in zip(phr,ends):
        turns.append({'role':role,'text':txt,'start':round(t+ps-a,3),'dur':round(pe-ps,3),'src':round(ps,2)})
    cuts.append(round(t,3)); out.append(seg); t+=b-a
    out.append(np.zeros(int(GAP*SR),np.float32)); t+=GAP
y=np.concatenate(out); dur=len(y)/SR
fr=SR//30; env=[float(np.sqrt(np.mean(y[i:i+fr]**2))) for i in range(0,len(y),fr)]
m=np.percentile(env,97); env=[round(min(1,(e/m))**0.8,3) for e in env]
import wave; w=wave.open('demo_audio.wav','wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(y,-1,1)*32767).astype(np.int16).tobytes()); w.close()
open('demo_data.js','w').write('window.DEMO='+json.dumps({'dur':round(dur,3),'turns':turns,'env':env,'cuts':cuts,'srcStarts':[s[0] for s in SEGS]},ensure_ascii=False)+';')
print(dur, cuts)
