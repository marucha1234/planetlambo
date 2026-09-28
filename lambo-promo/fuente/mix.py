import numpy as np, wave, json, re
SR=48000
def rd(p):
    w=wave.open(p); a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32767
    return a.reshape(-1,w.getnchannels()) if w.getnchannels()>1 else np.stack([a,a],1)
mus=rd('music.wav'); dem=rd('demo_audio.wav')
D=json.loads(open('demo_data.js').read()[len('window.DEMO='):-1])['dur']
A,I=8.0,2.2; DS=A+I; DE=DS+D; TOT=DE+18
y=np.zeros((int(TOT*SR)+SR//10,2),np.float32)
def put(sig,t,g=1.0):
    i=int(t*SR); n=min(len(sig),len(y)-i); y[i:i+n]+=sig[:n]*g
# part 1: music 0-8 with quick tape-stop feel (fade last 60ms)
m1=mus[:int(A*SR)].copy(); f=int(.06*SR); m1[-f:]*=np.linspace(1,0,f)[:,None]; put(m1,0)
rng=np.random.default_rng(3)
# glitch burst at 8.0 (0.35s): gated noise + bitcrushed tail of the music
t=np.arange(int(.35*SR))/SR; gate=(np.sin(2*np.pi*38*t)>0).astype(np.float32)
nz=rng.standard_normal(len(t)).astype(np.float32)*gate*np.exp(-t*6)*.22
tail=mus[int(7.65*SR):int(8.0*SR),0][:len(t)]; tail=np.repeat(tail[::24],24)[:len(t)]*gate*.8
put(np.stack([nz+tail,nz*.8+tail],1),A)
# low hit under "Pará."
t=np.arange(int(1.2*SR))/SR; hit=np.sin(2*np.pi*np.cumsum(38+50*np.exp(-t*8))/SR)*np.exp(-t*3)*.5
put(np.stack([hit,hit],1),A+.3)
# demo (real audio, untouched voices)
put(dem,DS)
# part 2: music from 14s (S4) to end
put(mus[int(14*SR):],DE)
y=np.tanh(y*1.1)/np.tanh(1.1)
w=wave.open('mix_demo.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(y,-1,1)*32767).astype(np.int16).tobytes()); w.close()
print(TOT)
