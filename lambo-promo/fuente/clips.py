# Voces REALES de la conversación con Lambo, insertadas en el video original
import numpy as np, subprocess, json, wave, imageio_ffmpeg
FF=imageio_ffmpeg.get_ffmpeg_exe(); SR=48000
x=np.frombuffer(subprocess.run([FF,'-v','error','-i','conv.mp3','-af','loudnorm=I=-15:TP=-1.5','-f','f32le','-ac','1','-ar',str(SR),'-'],capture_output=True).stdout,np.float32).copy()
CLIPS={'client':(24.55,28.95,8.7,'Quiero producir una campaña linda para mi chiringuito de playa.'),
       'lambo':(70.0,75.9,13.5,'Podemos generar videos, fotos, historias, todo con IA, adaptado al estilo de tu chiringuito.'),
       'hola':(0.0,1.3,28.0,'Hola, soy Lambo.')}
def rd(p):
    w=wave.open(p); a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32767; return a.reshape(-1,2)
mus=rd('music3.wav'); voice=np.zeros(len(mus),np.float32); duck=np.ones(len(mus),np.float32)
data={}
for k,(a,b,at,txt) in CLIPS.items():
    seg=x[int(a*SR):int(b*SR)].copy(); f=int(.03*SR); seg[:f]*=np.linspace(0,1,f); seg[-f:]*=np.linspace(1,0,f)
    i=int(at*SR); voice[i:i+len(seg)]+=seg
    r=int(.25*SR); duck[max(0,i-r):i+len(seg)+r]=np.minimum(duck[max(0,i-r):i+len(seg)+r],.45)
    fr=SR//30; env=[float(np.sqrt(np.mean(seg[j:j+fr]**2))) for j in range(0,len(seg),fr)]; m=np.percentile(env,97)
    data[k]={'start':at,'dur':round(len(seg)/SR,3),'text':txt,'env':[round(min(1,e/m)**.8,3) for e in env]}
# smooth ducking
k=int(.12*SR); duck=np.convolve(duck,np.ones(k)/k,mode='same')
y=mus*duck[:,None]+voice[:,None]*1.0
y=np.tanh(y*1.05)/np.tanh(1.05)
w=wave.open('mix3.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(y,-1,1)*32767).astype(np.int16).tobytes()); w.close()
open('clips.js','w').write('window.CLIPS='+json.dumps(data,ensure_ascii=False)+';')
print({k:(v['start'],v['dur']) for k,v in data.items()})
