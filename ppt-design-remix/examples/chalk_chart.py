import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"font.family":"Liberation Serif","path.sketch":(0.8,80,2.0)})
CH="#F3F1EA"; cols={50:"#F3E28F",100:"#7FDCC4",300:"#F4A259"}
phi=np.linspace(0,0.05,51)
f,ax=plt.subplots(figsize=(7.2,4.6),dpi=200)
f.patch.set_alpha(0); ax.set_facecolor("none")
for a,c in cols.items():
    y=(1-phi)/(1+(a/2)*phi); ax.plot(phi*100,y,color=c,lw=3,label=f"Aspect ratio α = {a}")
    p=np.arange(0,6); ax.scatter(p,(1-p/100)/(1+(a/2)*p/100),color=c,s=28,zorder=3)
ax.set_xlim(0,5.1); ax.set_ylim(0,1.05)
ax.set_xlabel("Nanoclay volume fraction, φ (%)",color=CH,fontsize=14)
ax.set_ylabel("Relative permeability  P$_c$ / P$_p$",color=CH,fontsize=14)
ax.tick_params(colors=CH,labelsize=12)
for s in ["top","right"]: ax.spines[s].set_visible(False)
for s in ["left","bottom"]: ax.spines[s].set_color(CH); ax.spines[s].set_linewidth(1.5)
ax.grid(axis="y",color="#3E5049",lw=0.8)
lg=ax.legend(frameon=False,fontsize=12,loc="upper right")
for t in lg.get_texts(): t.set_color(CH)
f.tight_layout(); f.savefig("img/nielsen.png",transparent=True)
