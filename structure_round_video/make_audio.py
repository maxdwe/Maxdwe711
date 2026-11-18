#!/usr/bin/env python3
"""Generate a 50 s corporate-style music bed with transition whooshes and hits -> _audio.wav"""
import wave, numpy as np
SR, T = 44100, 50.0
t = np.arange(int(SR*T))/SR
out = np.zeros_like(t)
def env(start, a, d, length):
    e = np.zeros_like(t); i0=int(start*SR); n=int(length*SR)
    seg=np.arange(n)/SR; e_=np.minimum(seg/a,1)*np.exp(-seg/d)
    e[i0:i0+n]=e_[:len(e[i0:i0+n])]; return e
# chord pad (Am F C G), 4 s per chord
chords=[[220,261.6,329.6],[174.6,220,261.6],[261.6,329.6,392],[196,246.9,293.7]]
for k in range(13):
    f=chords[k%4]; s=k*4.0
    for fr in f:
        for det in (0.997,1.003):
            out += 0.035*env(s,1.2,3.5,5.5)*np.sin(2*np.pi*fr*det*t)
    out += 0.06*env(s,0.02,1.5,4)*np.sin(2*np.pi*f[0]/2*t)  # bass
# soft pulse 120 bpm
for b in np.arange(0.0, 49.0, 0.5):
    out += 0.12*env(b,0.002,0.08,0.3)*np.sin(2*np.pi*(60+40*np.exp(-(t-b).clip(0)*30))*t)
    out += 0.015*env(b+0.25,0.001,0.03,0.1)*np.random.randn(len(t))
# whooshes at scene changes, pops at element reveals, riser into RM counter
rng=np.random.default_rng(1)
for s in [5.5,13,18,30,36.5,43,47]:
    w=env(s-0.4,0.35,0.25,1.2); out += 0.18*w*rng.standard_normal(len(t))*np.sin(2*np.pi*3*t)**2
for s in [6.2,7.3,8.4,9.5,10.6,30.5,31.6,32.7]:
    out += 0.12*env(s,0.003,0.12,0.4)*np.sin(2*np.pi*880*t)
for s in [23.3,45.6]:
    out += 0.35*env(s,0.005,0.6,2)*np.sin(2*np.pi*55*t)
r=(t>43.4)&(t<45.6); out[r]+=0.06*np.sin(2*np.pi*(300+500*((t[r]-43.4)/2.2)**2)*t[r])
out *= np.minimum(1, (T-t)/2.5)  # fade out
out = np.tanh(out*1.4)/1.2
pcm=(out*32767*0.85).astype(np.int16)
with wave.open('_audio.wav','wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
