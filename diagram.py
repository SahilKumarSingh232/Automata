"""Animated SVG state diagram, rendered inside Streamlit with components.html.

The layout matches the web version: transitions between neighbouring states are
straight lines, everything else (self-loops, jumps, back edges) is a curve, and
a gold token travels along the transitions taken on each step.
"""
import json

HEIGHT = 392

_TEMPLATE = r"""
<style>
html,body{margin:0;background:transparent;font-family:ui-monospace,Menlo,Consolas,monospace}
#w{overflow-x:auto;border:1px solid rgba(111,211,255,.34);border-radius:12px;background:rgba(10,3,40,.45)}
text{fill:#eaf2ff}
.st{fill:#1a0f38;stroke:#a9c9ff;stroke-width:1.8}
.st.on{fill:#7fd9ff;stroke:#f5c451;stroke-width:2.5;animation:glow 1.3s ease-in-out infinite}
text.sl.on{fill:#04101f;font-weight:700}
.ed{fill:none;stroke:#9a8bdc;stroke-width:1.5}
.ed.on{stroke:#f5c451;stroke-width:3}
.ed.on:not([style]){stroke-dasharray:9 6;animation:dash .9s linear infinite}
.lb{font-size:12px;fill:#9fb0e0}.lb.on{fill:#ffe08a;font-weight:700}
.intro .st,.intro .st.on,.intro text.sl{transform-box:fill-box;transform-origin:center;animation:rise .55s both;animation-delay:calc(var(--i)*90ms)}
.intro .ed,.intro .lb{animation:fade .7s .45s both}
@keyframes rise{from{opacity:0;transform:translateY(14px) scale(.9)}}
@keyframes fade{from{opacity:0}}
@keyframes glow{50%{filter:drop-shadow(0 0 8px #7fd9ff) drop-shadow(0 0 16px #8b5cf6)}}
@keyframes dash{to{stroke-dashoffset:-15}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
</style>
<div id="w"></div>
<script>
const D=__DATA__;
const R=22,GAP=92,Y=190,n=D.n;
const idx=[...Array(n).keys()];
const order=idx.filter(i=>D.labels[i]!=='dead').concat(idx.filter(i=>D.labels[i]==='dead'));
const pos=[];order.forEach((s,k)=>pos[s]=k);
const X=i=>50+pos[i]*GAP;
const acc=new Set(D.accept);
const groups={},inc={};
D.trans.forEach(([a,c,b])=>{const k=a+'>'+b;(groups[k]=groups[k]||{a,b,s:[]}).s.push(c);});
function draw(on,used,intro){
  const W=Math.max(520,n*GAP+60),H=2*Y;
  let s=`<svg id="svg" class="${intro?'intro':''}" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg"><defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" style="fill:#9a8bdc"/></marker></defs>`;
  Object.values(groups).forEach(e=>{
    const u=used&&used.has(e.a+'>'+e.b),cls=u?' on':'',lab=[...e.s].sort().join(','),id=`e${e.a}-${e.b}`;
    if(e.a===e.b){
      const cx=X(e.a),top=Y-R;
      s+=`<path id="${id}" class="ed${cls}" d="M${cx-11} ${top+3} C${cx-34} ${top-46} ${cx+34} ${top-46} ${cx+11} ${top+3}" marker-end="url(#ar)"/><text class="lb${cls}" x="${cx}" y="${top-38}" text-anchor="middle">${lab}</text>`;
    }else{
      const x1=X(e.a),x2=X(e.b);
      if(pos[e.b]===pos[e.a]+1){
        s+=`<path id="${id}" class="ed${cls}" d="M${x1+R} ${Y} L${x2-R} ${Y}" marker-end="url(#ar)"/><text class="lb${cls}" x="${(x1+x2)/2}" y="${Y-8}" text-anchor="middle">${lab}</text>`;
      }else{
        const up=pos[e.b]>pos[e.a],d=Math.abs(pos[e.b]-pos[e.a]),h=Math.min(28+d*20,160),g=up?-1:1,k=(inc[e.b]=(inc[e.b]||0)+1)-1,xe=x2+(up?-8:8)*(k%3)*.9,mx=(x1+xe)/2;
        s+=`<path id="${id}" class="ed${cls}" d="M${x1} ${Y+g*R} Q${mx} ${Y+g*(R+h*1.6)} ${xe} ${Y+g*R}" marker-end="url(#ar)"/><text class="lb${cls}" x="${mx}" y="${Y+g*(R+h*.8+6)}" text-anchor="middle">${lab}</text>`;
      }
    }
  });
  s+=`<path class="ed" d="M2 ${Y} L${X(0)-R} ${Y}" marker-end="url(#ar)"/>`;
  for(let i=0;i<n;i++){
    const cx=X(i),hi=on.has(i)?' on':'';
    s+=`<circle class="st${hi}" style="--i:${pos[i]}" cx="${cx}" cy="${Y}" r="${R}"><title>${D.labels[i]}${acc.has(i)?' (accepting)':''}: ${D.tips[i]}</title></circle>`;
    if(acc.has(i))s+=`<circle class="st${hi}" style="fill:none;stroke:#f5c451;--i:${pos[i]}" cx="${cx}" cy="${Y}" r="${R-5}"/>`;
    s+=`<text class="sl${hi}" style="--i:${pos[i]}" x="${cx}" y="${Y+4}" text-anchor="middle" font-size="12">${D.labels[i]}</text>`;
  }
  document.getElementById('w').innerHTML=s+'</svg>';
}
function flow(done){
  const svg=document.getElementById('svg'),ns='http://www.w3.org/2000/svg',toks=[];
  D.used.forEach(([a,b])=>{
    const p=document.getElementById(`e${a}-${b}`);if(!p)return;
    const sym=D.trans.some(t=>t[0]===a&&t[2]===b&&t[1]===D.symbol)?D.symbol:'ε';
    p.classList.add('on');
    const g=document.createElementNS(ns,'g');
    g.innerHTML=`<circle r="11" style="fill:#f5c451"/><text text-anchor="middle" y="4" font-size="12" style="fill:#1a0f38;font-weight:700">${sym}</text>`;
    svg.appendChild(g);
    const L=p.getTotalLength();p.style.strokeDasharray=L;p.style.strokeDashoffset=L;
    toks.push({p,g,L});
  });
  const T=760,t0=performance.now();
  (function f(now){
    const t=Math.min(1,(now-t0)/T),e=t<.5?2*t*t:1-Math.pow(-2*t+2,2)/2;
    toks.forEach(o=>{const pt=o.p.getPointAtLength(o.L*e);o.g.setAttribute('transform',`translate(${pt.x},${pt.y})`);o.p.style.strokeDashoffset=o.L*(1-e);});
    if(t<1)requestAnimationFrame(f);else setTimeout(done,toks.length?120:300);
  })(t0);
}
const cur=new Set(D.active),usedSet=new Set(D.used.map(u=>u[0]+'>'+u[1]));
const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
if(D.animate&&!reduce&&D.used.length){draw(new Set(D.prev),null,false);flow(()=>draw(cur,usedSet,false));}
else draw(cur,usedSet,D.intro);
</script>
"""


def diagram_html(auto, active, used, prev=(), symbol=None, animate=False, intro=False):
    """Return the HTML for the diagram of `auto` with the given highlighted states/edges."""
    tips = []
    for i in range(auto.n):
        out = [f"{c}\u2192{auto.labels[b]}" for a, c, b in auto.trans if a == i]
        tips.append(", ".join(out) if out else "no outgoing transitions")
    data = {
        "n": auto.n, "labels": auto.labels, "accept": sorted(auto.accept),
        "trans": [list(t) for t in auto.trans], "tips": tips,
        "active": sorted(active), "prev": sorted(prev),
        "used": [list(u) for u in sorted(used)], "symbol": symbol,
        "animate": bool(animate), "intro": bool(intro),
    }
    payload = json.dumps(data).replace("</", "<\\/")
    return _TEMPLATE.replace("__DATA__", payload)
