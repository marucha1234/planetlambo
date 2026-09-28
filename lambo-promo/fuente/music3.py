import numpy as np, wave
SR=48000; DUR=38.0; N=int(SR*DUR); BPM=120; B=60/BPM
rng=np.random.default_rng(7)
L=np.zeros(N); R=np.zeros(N)
def add(sig,t0,gain=1.0,pan=0.0):
    i=int(t0*SR); n=min(len(sig),N-i)
    if n<=0: return
    L[i:i+n]+=sig[:n]*gain*np.sqrt((1-pan)/2)*1.414
    R[i:i+n]+=sig[:n]*gain*np.sqrt((1+pan)/2)*1.414
def tt(d): return np.arange(int(d*SR))/SR
def lp(x,fc):  # one-pole lowpass (fc may be array)
    fc=np.broadcast_to(fc,x.shape); a=np.exp(-2*np.pi*fc/SR); y=np.empty_like(x); s=0.0
    for i in range(len(x)): s=a[i]*s+(1-a[i])*x[i]; y[i]=s
    return y
def hp(x,fc): return x-lp(x,fc)
def mtof(m): return 440*2**((m-69)/12)

def kick():
    t=tt(.45); f=45+110*np.exp(-t*28); ph=2*np.pi*np.cumsum(f)/SR
    return np.sin(ph)*np.exp(-t*7.5)+0.3*np.sin(ph)*np.exp(-t*60)
def hat(d=.06):
    t=tt(d); return hp(rng.standard_normal(len(t)),7000)*np.exp(-t*70)
def clap():
    t=tt(.25); n=hp(rng.standard_normal(len(t)),1200)
    env=np.exp(-t*22)+0.6*np.exp(-((t-.012)*300)**2)+0.5*np.exp(-((t-.024)*300)**2)
    return lp(n*env,5000)
def saw(f,d,det=0.0):
    t=tt(d); return sum(2*((t*f*(1+k*det))%1)-1 for k in (-1,0,1))/3
KICK,CLAP=kick(),clap()
# chords: Dm Bb F C  (per bar = 2s)
prog=[[50,57,62,65,69],[46,58,62,65,70],[41,57,60,65,69],[48,55,60,64,67]]
roots=[38,34,41,36]
def pad_bar(bar,d,cut=1800,gain=.07):
    ch=prog[bar%4]; s=sum(saw(mtof(m),d,.004) for m in ch)/len(ch)
    t=tt(d); env=np.minimum(1,t/.35)*np.minimum(1,(d-t)/.25)
    return lp(s*env,cut)*gain
def bass(bar,t0):
    r=mtof(roots[bar%4]); 
    for k in range(4):
        st=t0+k*B+B/2; t=tt(B*.45)
        s=(np.sin(2*np.pi*r*t)+.35*saw(r,B*.45))*np.exp(-t*5)
        add(lp(s,900)*.28,st)
def pluck(m,t0,g=.06,pan=0):
    t=tt(.5); s=saw(mtof(m),.5,.002); s=lp(s*np.exp(-t*9),np.maximum(300,5000*np.exp(-t*12)))
    add(s*g,t0,pan=pan)
def boom(t0,g=.9):
    t=tt(1.8); f=30+60*np.exp(-t*6); s=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*2.2)
    add(s*g,t0); add(lp(rng.standard_normal(len(t))*np.exp(-t*4),2500)*.15,t0)
def riser(t0,d,g=.18):
    t=tt(d); n=rng.standard_normal(len(t)); x=t/d
    s=lp(n,300+7000*x**2)*x**2
    add(s*g,t0,pan=-.3); add(s*g,t0,pan=.3)
def whoosh(t0,g=.12):  # reverse swoosh into a cut
    riser(t0-.5,.5,g)

# pads everywhere (S3 = 8-20 is a quiet bed under the real voices)
for bar in range(19):
    t0=bar*2; quiet=4<=bar<10
    cut=900 if bar<2 else (700 if quiet else (2600 if bar==13 else 2000))
    g=.5 if quiet else 1.0
    add(pad_bar(bar,2.1,cut)*g,t0,pan=-.25); add(pad_bar(bar,2.1,cut*1.1)*g,t0+.01,pan=.25)
for k in range(8):
    pluck([62,69,65,69][k%4],k*B,g=.045+.01*k,pan=(-.4,.4)[k%2])
riser(1.5,2.5,.2)
arp=[74,69,65,69, 74,70,65,70, 72,69,65,69, 72,67,64,67]
def section(a,b,drums=True,hats=True,clapon=True,arpon=True,bassg=True,arpg=.035):
    for beat in range(int(round(a/B)),int(round(b/B))):
        t0=beat*B; bar=int(t0//2)
        if drums: add(KICK*.9,t0)
        if hats: add(hat()*.16,t0+B/2,pan=.2); add(hat(.03)*.07,t0+B/4,pan=-.3); add(hat(.03)*.07,t0+3*B/4,pan=-.3)
        if clapon and beat%2==1: add(CLAP*.33,t0)
        if bassg and beat%4==0: bass(bar,t0)
        if arpon:
            for s in range(2):
                pluck(arp[(beat*2+s)%16]+(12 if t0>=31 else 0), t0+s*B/2, g=arpg, pan=(-.35,.35)[s])
section(4,8)
section(8,20,drums=False,hats=False,clapon=False,bassg=False,arpg=.012)   # bajo las voces reales
section(20,26)
section(28,37)
add(KICK*.5,8); whoosh(20); add(KICK*.5,20); whoosh(31); add(KICK*.5,31)
riser(18.2,1.8,.22)
boom(4,.7); boom(26,1.0); boom(31,.6)
for i,m in enumerate([74,77,81,84,86]): pluck(m,27+i*.09,g=.06,pan=-.5+.25*i)
boom(37,.5)
for i,m in enumerate([62,65,69,74]): pluck(m,37+i*.06,g=.05)

mix=np.stack([L,R],1)
# master: fade out tail, soft clip
t=np.arange(N)/SR
mix*= (np.clip((38-t)/1.0,0,1)**1.5)[:,None]
mix*= np.clip(t/0.08,0,1)[:,None]
mix=np.tanh(mix*1.3)/np.tanh(1.3)
mix/=np.max(np.abs(mix))*1.12
pcm=(mix*32767).astype(np.int16)
w=wave.open('music3.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print('ok')
