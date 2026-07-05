#!/usr/bin/env python3
"""Machado-2009 colour-vision-deficiency pass for Try-Works. No dependencies.
Reports deltaE between key hue pairs under protan/deutan/tritan at full severity."""
import json, math, pathlib
D = json.loads((pathlib.Path(__file__).resolve().parent.parent / "try-works.json").read_text())
M = {"protan":[[0.152286,1.052583,-0.204868],[0.114503,0.786281,0.099216],[-0.003882,-0.048116,1.051998]],
     "deutan":[[0.367322,0.860646,-0.227968],[0.280085,0.672501,0.047413],[-0.011820,0.042940,0.968881]],
     "tritan":[[1.255528,-0.076749,-0.178779],[-0.078411,0.930809,0.147602],[0.004733,0.691367,0.303900]]}
hx=lambda h:[int(h.lstrip('#')[i:i+2],16) for i in (0,2,4)]
lin=lambda c:(c/255)/12.92 if c/255<=0.03928 else (((c/255)+0.055)/1.055)**2.4
delin=lambda c:max(0,min(1,(12.92*c if c<=0.0031308 else 1.055*c**(1/2.4)-0.055)))*255
def sim(h,k):
    r,g,b=[lin(x) for x in hx(h)];m=M[k]
    o=[delin(m[i][0]*r+m[i][1]*g+m[i][2]*b) for i in range(3)]
    return '#%02x%02x%02x'%tuple(round(x) for x in o)
def lab(h):
    r,g,b=[lin(x) for x in hx(h)]
    X=0.4124*r+0.3576*g+0.1805*b;Y=0.2126*r+0.7152*g+0.0722*b;Z=0.0193*r+0.1192*g+0.9505*b
    f=lambda t:t**(1/3) if t>0.008856 else 7.787*t+16/116
    fx,fy,fz=f(X/0.95047),f(Y),f(Z/1.08883);return(116*fy-16,500*(fx-fy),200*(fy-fz))
dE=lambda a,b:math.sqrt(sum((x-y)**2 for x,y in zip(lab(a),lab(b))))
hues={r:D["code"][r]["color"] for r in ["keyword","string","number","function","type","decorator","comment"]}
keys=list(hues)
print("Try-Works CVD pass (deltaE; <10 reinforced with weight/italics)")
for kind in M:
    pairs=sorted((dE(sim(hues[keys[i]],kind),sim(hues[keys[j]],kind)),keys[i]+"/"+keys[j])
                 for i in range(len(keys)) for j in range(i+1,len(keys)))
    print("  %-7s worst: %s"%(kind,", ".join("%s %.1f"%(p[1],p[0]) for p in pairs[:3])))
