{
/* ================= Grundlagen ================= */
let WHO=['Alltag'];const MODES=['fly','rail','road','ferry','foot'];
let WCOL={Alltag:'#8A82AA'};
const PALETTES={neon:['#0A7CFF','#FF3D9A','#8B3DFF','#00BFB3','#FF8A00','#12A84F','#E03131','#5C7CFA','#C2255C','#2B8A3E'],
 classic:['#1F77B4','#D62728','#2CA02C','#FF7F0E','#9467BD','#8C564B','#E377C2','#17BECF','#BCBD22','#7F7F7F'],
 pastel:['#6FA8DC','#F28DB2','#A98FD8','#6CC3B9','#F6B96B','#93C99A','#E88F8F','#8E9BD6','#F4A6C8','#B5D68F'],
 earth:['#2E5E4E','#B5562B','#C9A227','#5B7DB1','#8C4A6E','#6E8B3D','#A0522D','#4E6E81','#9C6B30','#556B2F'],
 contrast:['#0057FF','#FF0055','#00A86B','#FFB000','#7A00FF','#00C2D1','#FF5A00','#3A3A3A','#E600AC','#6BBF00'],
 mono:['#1B1F3B','#5C677D','#9A8C98','#33415C','#7A7F9A','#3E5C76','#979DAC','#22223B','#4A4E69','#0D1321']};
let PALETTE=PALETTES.neon;
const GROUPCOL={Paar:'#8B3DFF',Couple:'#8B3DFF',Familie:'#00BFB3',Family:'#00BFB3'};
const MCOL={fly:'#FF3D9A',rail:'#12A84F',road:'#0A7CFF',ferry:'#00BFB3',foot:'#FF8A00'};
const MNAME={fly:'Flug',rail:'Zug & ÖV',road:'Auto',ferry:'Schiff',foot:'Zu Fuss'};
const YCOL=['#FFB000','#FF9A1F','#FF7A3D','#FF5A6A','#F0458F','#D23DB0','#AD3DD2','#8B3DFF','#6A4BFF','#3F63FF','#0A7CFF'];
let Y0=2016,Y1=2026,DYEARS=[],TYEARS=[];
const ycol=y=>YCOL[Y1>Y0?Math.max(0,Math.min(10,Math.round((+y-Y0)/(Y1-Y0)*10))):10];
const WORDER=()=>['Alltag',...WHO.filter(w=>w!='Alltag')];
const TCLS={0:'road',1:'rail',2:'foot',3:'rail',4:'rail'};
const DOW=['So','Mo','Di','Mi','Do','Fr','Sa'];
let HOME=[47,8];
const $=id=>document.getElementById(id);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=n=>Math.round(n).toLocaleString('de-CH').replace(/[, \s]/g,'’');
/* map colours for light and dark mode; lakes, borders and coasts stay visible in both */
const THEMES={light:{sea:'#DCE4F6',land:'#FCFBFF',prov:'#ECE8F5',rivS:'#C4D4F2',rivB:'#B6CAEF',lake:'#C9D8F3',lakeLine:'#AFC3EA',border:'#C2B8E0',halo:'rgba(252,251,255,.92)',text:'#3C3560',strong:'#17122E',ring:'#fff',old:'#C9C3DD',oldT:'#BDB6D6',regLine:'rgba(111,104,144,.55)',regBorder:'#17122E',empty:'#F6F4FB',cal0:'#E4E0F0',calHi:'#5B5479',base:[252,251,255]},
 dark:{sea:'#0B1230',land:'#1A1C33',prov:'#2B2D4A',rivS:'#2C4B85',rivB:'#3B63AA',lake:'#1E3769',lakeLine:'#4670BD',border:'#7C74B8',halo:'rgba(17,18,36,.92)',text:'#CFCAEB',strong:'#F4F2FF',ring:'#1A1C33',old:'#454169',oldT:'#3A3760',regLine:'rgba(190,182,240,.4)',regBorder:'#BDB5F0',empty:'#1A1B30',cal0:'#2A2B48',calHi:'#B9B2E6',base:[26,28,51]}};
let THEME='light',MC=THEMES.light;
/* map style from the settings (colours, line types, areas, base map) */
let STYLE=null;
const SM=m=>(STYLE&&STYLE.modes[m])||{dash:m=='fly'?'dashed':'solid',width:1};
function setDash(m,S){const d=SM(m).dash;ctx.setLineDash(d=='dashed'?[7/S,5/S]:d=='dotted'?[.01/S,4.5/S]:d=='longdash'?[15/S,6/S]:d=='dashdot'?[9/S,4/S,.01/S,4/S]:d=='sparse'?[.01/S,9/S]:[])}
function applyStyle(st){if(!st)return;STYLE=st;PALETTE=PALETTES[st.map.palette]||PALETTES.neon;for(const m in st.modes)MCOL[m]=st.modes[m].color;if(MCOL.ferry&&!st.modes.ferry)MCOL.ferry=MCOL.road}
let SDEF=null,STV=0;const ST=k=>(STYLE&&STYLE[k])||(SDEF&&SDEF[k])||{};
function dashFor(d,S){return d=='dashed'?[7/S,5/S]:d=='dotted'?[.01/S,4.2/S]:d=='longdash'?[14/S,6/S]:d=='dashdot'?[9/S,4/S,.01/S,4/S]:d=='sparse'?[.01/S,9/S]:[]}
function themeBtn(){const b=document.getElementById('ztheme');if(b){b.textContent=THEME=='dark'?'☀':'☾';b.title=b.ariaLabel=THEME=='dark'?'Heller Modus':'Dunkler Modus'}}
const BASEMAPS={earth:{sea:'#1d4a86',land:'#7d8c4c',border:'rgba(255,255,255,.55)',text:'#1f1a10',strong:'#120d06',halo:'rgba(255,253,245,.88)'},paper:{sea:'#D7E4EA',land:'#FBF6EC',prov:'#EADFCB',rivS:'#C3D5DE',rivB:'#AFC7D4',lake:'#C9DCE4',lakeLine:'#A9C2CF',border:'#BFAE8E',text:'#5A4632',halo:'rgba(251,246,236,.92)',base:[251,246,236]},
 mono:{sea:'#E1E5EA',land:'#F8F8F8',prov:'#EBEBEB',rivS:'#D4D9DF',rivB:'#C6CDD5',lake:'#D6DBE1',lakeLine:'#BEC5CD',border:'#B4B8BF',text:'#4A4A55',halo:'rgba(248,248,248,.92)',base:[248,248,248]}};
const EMBED=new URLSearchParams(location.search).has('embed');if(EMBED)document.documentElement.classList.add('embed');
function pickTheme(){let t='auto';try{t=(EMBED?STYLE&&STYLE.map.theme:localStorage.getItem('wm-theme'))||(STYLE&&STYLE.map.theme)||'auto'}catch(e){}const dark=t=='dark'||(t=='auto'&&matchMedia('(prefers-color-scheme: dark)').matches);THEME=dark?'dark':'light';MC=THEMES[THEME];const bm=STYLE&&STYLE.map.basemap;if(bm=='earth')MC={...THEMES[THEME],...BASEMAPS.earth};else if(!dark&&BASEMAPS[bm])MC={...THEMES.light,...BASEMAPS[bm]};document.documentElement.dataset.theme=THEME}
pickTheme();
function shade(c,f){return '#'+[1,3,5].map(i=>Math.round(parseInt(c.slice(i,i+2),16)*f).toString(16).padStart(2,'0')).join('')}
function tint(c,a){const r=parseInt(c.slice(1,3),16),g=parseInt(c.slice(3,5),16),b=parseInt(c.slice(5,7),16);const m=(x,y)=>Math.round(y+(x-y)*a).toString(16).padStart(2,'0');return '#'+m(r,MC.base[0])+m(g,MC.base[1])+m(b,MC.base[2])}
const RED=matchMedia('(prefers-reduced-motion: reduce)').matches;
const last={};
function count(id,v,suf=''){const e=$(id);if(!e)return;const from=last[id]??0;last[id]=v;const t0=performance.now();function f(t){const p=RED?1:Math.min(1,(t-t0)/450),q=1-Math.pow(1-p,3);e.textContent=fmt(from+(v-from)*q)+suf;if(p<1)requestAnimationFrame(f)}requestAnimationFrame(f)}
function statHTML(items){return items.map(([id,l])=>`<div class="stat"><span class="v" id="${id}">0</span><span class="l">${l}</span></div>`).join('')}
function mbars(obj,cols,names,unit=' km'){const mx=Math.max(1,...Object.values(obj));return Object.entries(obj).filter(([k,v])=>v>0).sort((a,b)=>b[1]-a[1]).map(([k,v])=>`<div class="mbar"><span>${esc(names[k]||k)}</span><span class="tr"><div style="width:${v/mx*100}%;background:${cols[k]||cols._}"></div></span><b>${fmt(v)}${unit}</b></div>`).join('')}
const dateOf=s=>{const [y,m,d]=s.split('-').map(Number);return new Date(Date.UTC(y,m-1,d))};
const dfmt=s=>{const d=dateOf(s);return DOW[d.getUTCDay()]+' '+s.slice(8,10)+'.'+s.slice(5,7)+'.'+s.slice(0,4)};
function toggle(set,v,all,cb){if(set.size==all.length){set.clear();set.add(v)}else if(set.has(v)){set.delete(v);if(!set.size)all.forEach(x=>set.add(x))}else set.add(v);cb()}
function segBind(id,cb){document.querySelectorAll('#'+id+' button').forEach(b=>b.onclick=()=>{document.querySelectorAll('#'+id+' button').forEach(x=>x.classList.toggle('on',x==b));cb(b.dataset.v)})}
const tip=$('tip');
function showTip(e,txt){const r=$('wrap').getBoundingClientRect();tip.textContent=txt;tip.style.left=(e.clientX-r.left)+'px';tip.style.top=(e.clientY-r.top)+'px';tip.style.opacity=1}
function hideTip(){tip.style.opacity=0}
function closeDetail(){$('detail').classList.remove('show')}
function openDetail(html,onClose){$('detail').innerHTML='<button class="x" aria-label="Schliessen">✕</button>'+html;$('detail').classList.add('show');$('detail').querySelector('.x').onclick=e=>{e.stopPropagation();closeDetail();onClose&&onClose()}}

/* ================= Kartenmotor ================= */
const cv=$('cv');let ctx=cv.getContext('2d');const MAINCTX=ctx;
const MX=lon=>(lon+180)/360,MY=lat=>{const s=Math.sin(lat*Math.PI/180);return .5-Math.log((1+s)/(1-s))/(4*Math.PI)};
const IX=x=>x*360-180,IY=y=>Math.atan(Math.sinh(Math.PI*(1-2*y)))*180/Math.PI;
const V={cx:MX(9),cy:MY(47),S:60000,W:0,H:0,dpr:1};
let DRAW=()=>{};
function headerH(){const h=document.querySelector('.top');if(h)document.documentElement.style.setProperty('--th',h.offsetHeight+'px')}
function sizeCV(){headerH();const r=$('wrap').getBoundingClientRect();V.W=r.width;V.H=r.height;V.dpr=Math.min(V.W*V.H>900000?1.5:2,window.devicePixelRatio||1);cv.width=Math.round(r.width*V.dpr);cv.height=Math.round(r.height*V.dpr)}
const toS=(x,y)=>[(x-V.cx)*V.S+V.W/2,(y-V.cy)*V.S+V.H/2];
const toW=(sx,sy)=>[(sx-V.W/2)/V.S+V.cx,(sy-V.H/2)/V.S+V.cy];
const TS=256,TDPR=Math.min(2,window.devicePixelRatio||1),TC=new Map();let TKEY='',tileT=null;
function renderTile(z,x,y,fn){const n=2**z,St=TS*n,f=TDPR;const c=document.createElement('canvas');c.width=c.height=Math.round(TS*f);const g=c.getContext('2d');const bb=[x/n,y/n,(x+1)/n,(y+1)/n];const oc=ctx,oS=V.S;ctx=g;V.S=St;V.tf=f;V.tz=[z,x,y];g.setTransform(f*St,0,0,f*St,-x*TS*f,-y*TS*f);g.fillStyle=MC.sea;g.fillRect(bb[0],bb[1],1/n,1/n);try{fn(bb)}finally{ctx=oc;V.S=oS;V.tz=null}return c}
let CURKEY='',PREVKEY='';
function drawTiles(fn){
 if(TKEY!==CURKEY){PREVKEY=CURKEY;CURKEY=TKEY}
 ctx.setTransform(V.dpr,0,0,V.dpr,0,0);ctx.fillStyle=MC.sea;ctx.fillRect(0,0,V.W,V.H);
 const z=Math.max(1,Math.min(25,Math.round(Math.log2(V.S/TS)))),n=2**z,k=V.S/(TS*n),ts=TS*k;
 const x0=Math.floor((V.cx-V.W/2/V.S)*n),x1=Math.floor((V.cx+V.W/2/V.S)*n),y0=Math.floor((V.cy-V.H/2/V.S)*n),y1=Math.floor((V.cy+V.H/2/V.S)*n);
 const list=[];for(let x=x0;x<=x1;x++)for(let y=y0;y<=y1;y++)list.push([x,y]);const cx=V.cx*n,cy=V.cy*n;list.sort((a,b)=>Math.hypot(a[0]+.5-cx,a[1]+.5-cy)-Math.hypot(b[0]+.5-cx,b[1]+.5-cy));
 const t0=performance.now();let miss=0,fading=false;const FADE=RED?0:220;
 const under=(x,y,sx,sy,sz)=>{const pv=PREVKEY&&TC.get(PREVKEY+'|'+z+'|'+x+'|'+y);if(pv){ctx.drawImage(pv,sx,sy,sz,sz);return true}/* the old version of this tile until the new one is ready */for(let up=1;up<=5;up++){const m=2**up,pk=TKEY+'|'+(z-up)+'|'+Math.floor(x/m)+'|'+Math.floor(y/m);const pt=TC.get(pk);if(pt){const sub=pt.width/m;ctx.drawImage(pt,(x-Math.floor(x/m)*m)*sub,(y-Math.floor(y/m)*m)*sub,sub,sub,sx,sy,sz,sz);return true}}
  for(const dn of [1,2]){const m=2**dn;const cz=z+dn;let any=false;for(let i=0;i<m;i++)for(let j=0;j<m;j++){const ck=TKEY+'|'+cz+'|'+(x*m+i)+'|'+(y*m+j);const ct=TC.get(ck);if(ct){ctx.drawImage(ct,sx+i*sz/m,sy+j*sz/m,sz/m+1,sz/m+1);any=true}}if(any)return true}return false};
 for(const [x,y] of list){const key=TKEY+'|'+z+'|'+x+'|'+y;let t=TC.get(key);const sx=Math.floor((x/n-V.cx)*V.S+V.W/2),sy=Math.floor((y/n-V.cy)*V.S+V.H/2),sz=Math.ceil(ts)+1;
  if(!t&&performance.now()-t0<28){t=renderTile(z,x,y,fn);t._b=performance.now();TC.set(key,t)}
  if(t){TC.delete(key);TC.set(key,t);const age=performance.now()-(t._b||0);
   /* a new level of detail fades in over the old one instead of popping */
   if(age<FADE&&t._u!==false){if(t._u===undefined)t._u=under(x,y,sx,sy,sz);else under(x,y,sx,sy,sz);if(t._u){ctx.globalAlpha=age/FADE;ctx.drawImage(t,sx,sy,sz,sz);ctx.globalAlpha=1;fading=true;continue}t._u=false}
   ctx.drawImage(t,sx,sy,sz,sz);continue}
  miss++;under(x,y,sx,sy,sz)}
 const CAP=V.W<700?110:240;while(TC.size>CAP)TC.delete(TC.keys().next().value);
 window.__miss=miss;if(miss||fading){clearTimeout(tileT);tileT=setTimeout(()=>redraw(),16)}
}
function worldT(){ctx.save();ctx.translate(V.W/2,V.H/2);ctx.scale(V.S,V.S);ctx.translate(-V.cx,-V.cy)}
function begin(){ctx.setTransform(V.dpr,0,0,V.dpr,0,0);ctx.fillStyle=MC.sea;ctx.fillRect(0,0,V.W,V.H);ctx.save();ctx.translate(V.W/2,V.H/2);ctx.scale(V.S,V.S);ctx.translate(-V.cx,-V.cy)}
function endWorld(){ctx.restore();ctx.setTransform(V.dpr,0,0,V.dpr,0,0)}
let idleT=null,rq=null;
function full(){DRAW();scaleBar()}
function quick(){DRAW();scaleBar()}
function redraw(){if(!rq)rq=requestAnimationFrame(()=>{rq=null;DRAW();scaleBar()})}
function zoomAt(f,sx,sy){const ns=Math.min(6e7,Math.max(900,V.S*f));const [wx,wy]=toW(sx,sy);V.S=ns;V.cx=wx-(sx-V.W/2)/ns;V.cy=wy-(sy-V.H/2)/ns;redraw()}
let flying=null;
function flyTo(cx,cy,S,ms=750){if(flying)cancelAnimationFrame(flying);const c0=V.cx,y0=V.cy,s0=V.S,t0=performance.now();if(RED)ms=1;const f=t=>{const p=Math.min(1,(t-t0)/ms),q=p<.5?2*p*p:1-Math.pow(-2*p+2,2)/2;V.S=s0*Math.pow(S/s0,q);V.cx=c0+(cx-c0)*q;V.cy=y0+(cy-y0)*q;if(p<1){quick();flying=requestAnimationFrame(f)}else{flying=null;full()}};flying=requestAnimationFrame(f)}
function fit(la0,lo0,la1,lo1,ms,pad=50){const x0=MX(lo0),x1=MX(lo1),y0=MY(la1),y1=MY(la0);const S=Math.min((V.W-pad)/Math.max(1e-7,x1-x0),(V.H-pad)/Math.max(1e-7,y1-y0));flyTo((x0+x1)/2,(y0+y1)/2,Math.min(S,8e6),ms)}
function setFit(la0,lo0,la1,lo1,pad=40){const x0=MX(lo0),x1=MX(lo1),y0=MY(la1),y1=MY(la0);V.S=Math.min((V.W-pad)/(x1-x0),(V.H-pad)/(y1-y0));V.cx=(x0+x1)/2;V.cy=(y0+y1)/2}
function scaleBar(){const mpp=40075016*Math.cos(IY(V.cy)*Math.PI/180)/V.S;const opts=[10,20,50,100,200,500,1000,2000,5000,10000,20000,50000,100000,200000,500000];let m=opts[0];for(const o of opts)if(o/mpp<=110)m=o;const el=$('scale');el.querySelector('span').textContent=m>=1000?(m/1000)+' km':m+' m';el.querySelector('i').style.width=(m/mpp)+'px'}

/* ---- Grundkarte ---- */
let B=null,LAB=null;
function decRings(rs,q=1e4){const p=new Path2D();for(const r of rs){let x=0,y=0;for(let i=0;i<r.length;i+=2){x+=r[i];y+=r[i+1];const X=MX(x/q),Y=MY(y/q);i?p.lineTo(X,Y):p.moveTo(X,Y)}}return p}
/* fill() closes sub-paths by itself; closePath() on thousands of rings is very slow in Chrome */
function decRingsClosed(rs,q=1e4){return decRings(rs,q)}
function prepBase(j){
 const rivB=[],rivS=[];for(const r of j.rivers){const sr=r[0];(sr<=5?rivB:rivS).push(...r.slice(1))}
 B={land:decRingsClosed(j.land),lakes:decRingsClosed(j.lakes),borders:decRings(j.borders),prov:decRings(j.prov),rivB:decRings(rivB),rivS:decRings(rivS),ne:j.labels};
}
/* Earth map: ready-made picture tiles (z0–5 for the whole world); deeper zoom uses the closest level, so every place looks the same */
const EARTH_MAXZ=5,EI=new Map(),EPEND=new Map();
function earthImg(z,x,y){const k=z+'/'+x+'/'+y;let im=EI.get(k);if(!im){im=new Image();im.decoding='async';im.onload=()=>{im._ok=true;const w=EPEND.get(k);if(w){for(const tk of w)TC.delete(tk);EPEND.delete(k);redraw()}};im.onerror=()=>{im._bad=true};im.src='tiles/earth/'+k+'.webp?v=__WMV__';EI.set(k,im);if(EI.size>600)EI.delete(EI.keys().next().value)}return im}
function drawEarth(){const t=V.tz;if(!t)return false;const [z,x,y]=t,n=2**z;
 for(let zs=Math.min(z,EARTH_MAXZ);zs>=0;zs--){const m=2**(z-zs),ix=Math.floor(x/m),iy=Math.floor(y/m),im=earthImg(zs,ix,iy);
  if(!im._ok){if(!im._bad){const k=zs+'/'+ix+'/'+iy,tk=TKEY+'|'+z+'|'+x+'|'+y;let w=EPEND.get(k);if(!w){w=new Set();EPEND.set(k,w)}w.add(tk)}continue}
  const sub=256/m,sx=(x-ix*m)*sub,sy=(y-iy*m)*sub;ctx.imageSmoothingQuality='high';ctx.drawImage(im,sx,sy,sub,sub,x/n,y/n,1/n,1/n);return true}
 return true}
function drawBase(opt={}){
 const S=V.S;
 if(STYLE&&STYLE.map.basemap=='earth'&&drawEarth()){ctx.strokeStyle=MC.border;ctx.lineWidth=1/S;ctx.stroke(B.borders);return}
 ctx.fillStyle=MC.land;ctx.fill(B.land,'nonzero');
 if(S>14000&&(!STYLE||STYLE.map.provinces)){ctx.strokeStyle=MC.prov;ctx.lineWidth=.8/S;ctx.stroke(B.prov)}

 const RIV=!STYLE||STYLE.map.rivers;
 if(RIV&&S>30000){ctx.strokeStyle=MC.rivS;ctx.lineWidth=Math.min(2,S/60000)/S;ctx.stroke(B.rivS)}
 if(RIV){ctx.strokeStyle=MC.rivB;ctx.lineWidth=Math.min(2.4,.6+S/50000)/S;ctx.stroke(B.rivB)}
 ctx.fillStyle=MC.lake;ctx.fill(B.lakes);ctx.strokeStyle=MC.lakeLine;ctx.lineWidth=.7/S;ctx.stroke(B.lakes);

 ctx.strokeStyle=MC.border;ctx.lineWidth=1.2/S;ctx.stroke(B.borders);

}
const placed=[];const usedNames=new Set();
function lbl(t,x,y,fs,fw,c,anchor='left',halo=4,force=false){if(!force&&usedNames.has(t))return false;ctx.font=`${fw} ${fs}px Inter, sans-serif`;const w=ctx.measureText(t).width;let x0=anchor=='left'?x:anchor=='right'?x-w:x-w/2;const box=[x0-2,y-fs+1,x0+w+2,y+4];if(!force&&placed.some(b=>!(box[2]<b[0]||box[0]>b[2]||box[3]<b[1]||box[1]>b[3])))return false;placed.push(box);usedNames.add(t);ctx.textAlign='left';ctx.lineJoin='round';ctx.lineWidth=halo;ctx.strokeStyle=MC.halo;ctx.strokeText(t,x0,y);ctx.fillStyle=c;ctx.fillText(t,x0,y);return true}
let LALL=null;
function drawPlaceLabels(lv){
 const LV=lv||(STYLE?STYLE.map.labels:'normal');if(LV=='off')return;const S=V.S*(LV=='few'?.4:LV=='many'?2.2:1),SV=V.S;
 if(!LALL){LALL=[];for(const [n,sr,la,lo,cap] of B.ne)LALL.push([sr*10-(cap?5:0),n,MX(lo),MY(la),sr<=2?13:12,sr<=2?700:600,sr<=1?0:sr<=3?6000:sr<=5?12000:sr<=7?30000:80000]);for(const [n0,c,la,lo] of LAB){const n=String(n0).replace(/\s*\([^)]*\)/g,'').split(' / ')[0].trim();if(n)LALL.push([30+c*10,n,MX(lo),MY(la),[12.5,12,11.5,11,10.5][c],[650,600,550,500,500][c],[15000,55000,180000,600000,600000][c]]);}LALL.sort((a,b)=>a[0]-b[0])}
 const x0=V.cx-V.W/2/SV-20/SV,x1=V.cx+V.W/2/SV+20/SV,y0=V.cy-V.H/2/SV,y1=V.cy+V.H/2/SV;let n=0;
 for(const [r,t,wx,wy,fs,fw,need] of LALL){if((LV=='few'&&r>=40)||S<need||wx<x0||wx>x1||wy<y0||wy>y1)continue;const x=(wx-V.cx)*SV+V.W/2,y=(wy-V.cy)*SV+V.H/2;if(x<-50||y<-20||x>V.W+50||y>V.H+20)continue;if(lbl(t,x+4,y+4,fs,fw,'#6F6890',
 'left',3.5)){ctx.fillStyle='#8E86AE';ctx.beginPath();ctx.arc(x,y,1.8,0,7);ctx.fill();if(++n>140)break}}
}
function homeMark(){const [x,y]=toS(MX(HOME[1]),MY(HOME[0]));ctx.beginPath();ctx.arc(x,y,6,0,7);ctx.fillStyle=MC.strong;ctx.fill();ctx.lineWidth=2;ctx.strokeStyle=MC.ring;ctx.stroke();ctx.beginPath();ctx.arc(x,y,11,0,7);ctx.strokeStyle=MC.strong;ctx.lineWidth=1.8;ctx.stroke();lbl('Zuhause',x+15,y-8,14,800,MC.strong,'left',4.5,true)}
function pieS(x,y,r,cs){if(!cs.length)cs=['#B8B0D6'];if(cs.length==1){ctx.beginPath();ctx.arc(x,y,r,0,7);ctx.fillStyle=cs[0];ctx.fill()}else cs.forEach((c,i)=>{ctx.beginPath();ctx.moveTo(x,y);ctx.arc(x,y,r,2*Math.PI*i/cs.length-Math.PI/2,2*Math.PI*(i+1)/cs.length-Math.PI/2);ctx.closePath();ctx.fillStyle=c;ctx.fill()});ctx.beginPath();ctx.arc(x,y,r,0,7);ctx.lineWidth=2;ctx.strokeStyle=MC.ring;ctx.stroke()}

/* ---- Daten ---- */
let D=null,tripById={},dayInfo=[],TR=null,byDay={};
const ready={};

/* ================= Looks: game-style places and flights (Stars, Crystals, Medals) – "classic" keeps today's map untouched ================= */
const LOOK=()=>(STYLE&&STYLE.map.look)||'classic';
const H32=(a,b)=>{let h=(a*374761393+b*668265263)|0;h=(h^(h>>>13))*1274126177|0;return ((h^(h>>>16))>>>0)/4294967296};
const rgbaH=(hex,a)=>{const h=/^#[0-9a-f]{6}$/i.test(hex)?hex:'#8A82AA';return `rgba(${parseInt(h.slice(1,3),16)},${parseInt(h.slice(3,5),16)},${parseInt(h.slice(5,7),16)},${a})`};
function lkStar(x,y,s,col,ring){const g=ctx;g.save();g.translate(x,y);g.fillStyle='rgba(20,30,10,.33)';g.beginPath();g.ellipse(s*.35,s*.95,s*.75,s*.25,0,0,7);g.fill();g.translate(0,-s*.25);
 const P5=[];for(let k=0;k<10;k++){const a=k*Math.PI/5-Math.PI/2,r=k%2?s*.42:s;P5.push([Math.cos(a)*r,Math.sin(a)*r])}
 g.shadowColor='rgba(255,200,80,.7)';g.shadowBlur=6;g.fillStyle='#d99a1c';g.beginPath();P5.forEach((p,i)=>i?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1]));g.closePath();g.fill();g.shadowBlur=0;
 for(let k=0;k<10;k++){const p=P5[k],q=P5[(k+1)%10],mid=Math.atan2((p[1]+q[1])/2,(p[0]+q[0])/2),lit=Math.cos(mid+2.35)>0;g.fillStyle=lit?'#ffe27a':'#c98612';g.beginPath();g.moveTo(0,0);g.lineTo(p[0],p[1]);g.lineTo(q[0],q[1]);g.closePath();g.fill()}
 g.strokeStyle='#7a4c08';g.lineWidth=.9;g.beginPath();P5.forEach((p,i)=>i?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1]));g.closePath();g.stroke();
 g.fillStyle=col;g.beginPath();g.arc(0,0,s*.2,0,7);g.fill();g.strokeStyle='rgba(255,255,255,.8)';g.lineWidth=.8;g.stroke();
 if(ring){g.save();g.globalCompositeOperation='lighter';const h=g.createRadialGradient(0,0,s*.3,0,0,s*1.7);h.addColorStop(0,'rgba(255,220,120,.45)');h.addColorStop(1,'rgba(255,200,80,0)');g.fillStyle=h;g.beginPath();g.arc(0,0,s*1.7,0,7);g.fill();g.restore()}
 g.fillStyle='rgba(255,255,255,.95)';const sp=(x2,y2,r)=>{g.beginPath();g.moveTo(x2,y2-r);g.lineTo(x2+r*.25,y2);g.lineTo(x2,y2+r);g.lineTo(x2-r*.25,y2);g.closePath();g.fill();g.beginPath();g.moveTo(x2-r,y2);g.lineTo(x2,y2+r*.25);g.lineTo(x2+r,y2);g.lineTo(x2,y2-r*.25);g.closePath();g.fill()};sp(-s*.45,-s*.55,s*.28);if(ring)sp(s*.7,-s*.85,s*.2);g.restore()}
function lkCrystal(x,y,s,col,gold){const g=ctx,lift=s*1.25,c=gold?'#f6c64a':col;g.save();g.translate(x,y);
 const rg=g.createRadialGradient(0,0,0,0,0,s*.9);rg.addColorStop(0,rgbaH(c,.55));rg.addColorStop(1,rgbaH(c,0));g.fillStyle=rg;g.beginPath();g.ellipse(0,0,s*.9,s*.32,0,0,7);g.fill();
 g.fillStyle='rgba(20,30,10,.3)';g.beginPath();g.ellipse(s*.25,s*.08,s*.4,s*.13,0,0,7);g.fill();
 const beam=g.createLinearGradient(0,-lift,0,0);beam.addColorStop(0,rgbaH(c,0));beam.addColorStop(1,rgbaH(c,.35));g.fillStyle=beam;g.fillRect(-s*.08,-lift,s*.16,lift);
 g.translate(0,-lift);g.shadowColor=c;g.shadowBlur=12;
 const T=[0,-s*1.05],Bt=[0,s*.8],L=[-s*.52,-s*.12],Rr=[s*.52,-s*.12],ML=[-s*.2,-s*.02],MR=[s*.2,-s*.02];
 const face=(pts,fill)=>{g.fillStyle=fill;g.beginPath();pts.forEach((p,i)=>i?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1]));g.closePath();g.fill()};
 face([T,L,Bt,Rr],c);g.shadowBlur=0;face([T,L,ML],'rgba(255,255,255,.65)');face([T,ML,MR],'rgba(255,255,255,.35)');face([T,MR,Rr],'rgba(255,255,255,.12)');
 face([L,Bt,ML],'rgba(0,0,0,.08)');face([ML,Bt,MR],'rgba(0,0,0,.18)');face([MR,Bt,Rr],'rgba(0,0,0,.34)');
 g.strokeStyle='rgba(255,255,255,.9)';g.lineWidth=.8;g.beginPath();g.moveTo(...T);g.lineTo(...Rr);g.lineTo(...Bt);g.lineTo(...L);g.closePath();g.stroke();
 g.fillStyle='#fff';g.beginPath();g.arc(-s*.18,-s*.6,s*.07,0,7);g.fill();g.restore()}
function lkCoin(x,y,s,col,n,plain){const g=ctx,tier=n>=6?['#fff1a8','#e0a820','#8a5a00']:n>=3?['#ffffff','#b9c2cc','#5d6670']:['#ffd9b0','#c07a3a','#6e3a12'];g.save();g.translate(x,y-s*.6);
 g.fillStyle='rgba(20,30,10,.35)';g.beginPath();g.ellipse(s*.3,s*1.25,s*.85,s*.26,0,0,7);g.fill();
 g.fillStyle=tier[2];g.beginPath();g.arc(0,s*.14,s,0,7);g.fill();const q=g.createLinearGradient(-s,-s,s,s);q.addColorStop(0,tier[0]);q.addColorStop(1,tier[1]);g.fillStyle=q;g.beginPath();g.arc(0,0,s,0,7);g.fill();
 g.strokeStyle='rgba(0,0,0,.18)';g.lineWidth=.6;for(let k=0;k<20;k++){const a=k/20*6.283;g.beginPath();g.moveTo(Math.cos(a)*s*.86,Math.sin(a)*s*.86);g.lineTo(Math.cos(a)*s*.97,Math.sin(a)*s*.97);g.stroke()}
 g.fillStyle=col;g.beginPath();g.arc(0,0,s*.68,0,7);g.fill();g.strokeStyle='rgba(255,255,255,.75)';g.lineWidth=1;g.stroke();
 if(!plain&&s>=7){const fs=Math.max(11,Math.round(s));g.font=`900 ${fs}px Inter,system-ui,sans-serif`;g.textAlign='center';g.textBaseline='middle';g.lineWidth=3;g.strokeStyle='rgba(20,10,30,.85)';const t=n>99?'99+':String(n);g.strokeText(t,0,s*.05);g.fillStyle='#fff';g.fillText(t,0,s*.05);g.textAlign='left';g.textBaseline='alphabetic'}
 else{g.fillStyle='rgba(255,255,255,.95)';g.beginPath();for(let k=0;k<10;k++){const a=k*Math.PI/5-Math.PI/2,r=k%2?s*.2:s*.46;g.lineTo(Math.cos(a)*r,Math.sin(a)*r+s*.02)}g.closePath();g.fill()}
 g.fillStyle='rgba(255,255,255,.4)';g.beginPath();g.ellipse(-s*.38,-s*.5,s*.36,s*.15,-.6,0,7);g.fill();
 if(n>=6){g.fillStyle='#c0392b';for(const d of [-1,1]){g.beginPath();g.moveTo(d*s*.5,s*.75);g.lineTo(d*s*.75,s*1.45);g.lineTo(d*s*.42,s*1.3);g.lineTo(d*s*.22,s*1.55);g.lineTo(d*s*.05,s*.95);g.closePath();g.fill()}}g.restore()}
/* one marker for a place in the current look; returns its radius so labels can sit beside it */
function lookMark(x,y,r,cs,n,home){const lk=LOOK(),c=cs[0]||'#8A82AA',s=Math.max(7,Math.min(15,r*1.45));
 if(lk=='stars')lkStar(x,y,home?s*1.4:s*(1+Math.min(.5,n*.05)),home?'#FF2DAA':c,home||n>=5);
 else if(lk=='crystal')lkCrystal(x,y,home?s*1.3:s*(1+Math.min(.5,n*.05)),c,home);
 else lkCoin(x,y,home?s*1.25:s,home?'#FF2DAA':c,home?99:n,home);return s}
function lkPlane(x,y,a,s,body,edge){const g=ctx;g.save();g.translate(x,y);g.rotate(a);g.scale(s/10,s/10);g.beginPath();
 g.moveTo(10,0);g.quadraticCurveTo(9,-1.6,6,-1.6);g.lineTo(1,-1.6);g.lineTo(-3,-9);g.lineTo(-5.5,-9);g.lineTo(-3,-1.6);g.lineTo(-7,-1.6);g.lineTo(-9,-4.5);g.lineTo(-10.5,-4.5);g.lineTo(-9.5,0);
 g.lineTo(-10.5,4.5);g.lineTo(-9,4.5);g.lineTo(-7,1.6);g.lineTo(-3,1.6);g.lineTo(-5.5,9);g.lineTo(-3,9);g.lineTo(1,1.6);g.lineTo(6,1.6);g.quadraticCurveTo(9,1.6,10,0);g.closePath();g.fillStyle=body;g.fill();if(edge){g.strokeStyle=edge;g.lineWidth=1;g.stroke()}g.restore()}
function lkPaper(x,y,a,s,body,edge){const g=ctx;g.save();g.translate(x,y);g.rotate(a);g.scale(s/10,s/10);g.beginPath();g.moveTo(10,0);g.lineTo(-8,-7);g.lineTo(-4,0);g.lineTo(-8,7);g.closePath();g.fillStyle=body;g.fill();if(edge){g.strokeStyle=edge;g.lineWidth=1;g.stroke();g.beginPath();g.moveTo(10,0);g.lineTo(-4,0);g.stroke()}g.restore()}
/* a flight in a game look: the trail fades in towards the aircraft, the aircraft sits somewhere along the way and casts a shadow; a comet in the crystal look */
function lookFlight(a,col,seed,vehicle){const lk=LOOK(),g=ctx,P=u=>toS((1-u)*(1-u)*a[0]+2*(1-u)*u*a[2]+u*u*a[4],(1-u)*(1-u)*a[1]+2*(1-u)*u*a[3]+u*u*a[5]);
 const [hx,hy]=P(0),[ex,ey]=P(1),d=Math.hypot(ex-hx,ey-hy);if(d<40)return;const up=.38+H32(seed,7)*.34,n=Math.min(300,Math.max(24,Math.ceil(d/8))),u0=.06,s=Math.max(10,Math.min(17,8+d/60));
 g.save();g.lineCap='round';
 if(lk!='crystal')for(let i=Math.ceil(n*u0);i<n*up;i++){const u=i/n,[ax,ay]=P(u),[bx,by]=P(u+1/n);if((ax<-40&&bx<-40)||(ay<-40&&by<-40)||(ax>V.W+40&&bx>V.W+40)||(ay>V.H+40&&by>V.H+40))continue;const f=(u-u0)/(up-u0);
  if(lk=='medals'&&i%3==0)continue;g.lineWidth=.5+f*1.6;g.strokeStyle=lk=='stars'?`rgba(255,210,90,${.15+f*.75})`:`rgba(60,45,25,${.12+f*.45})`;g.beginPath();g.moveTo(ax,ay);g.lineTo(bx,by);g.stroke()}
 g.beginPath();let on=false;for(let i=Math.ceil(n*up);i<=n;i++){const [ax,ay]=P(i/n),ins=ax>-40&&ay>-40&&ax<V.W+40&&ay<V.H+40;if(ins){on?g.lineTo(ax,ay):g.moveTo(ax,ay);on=true}else on=false}
 g.strokeStyle=lk=='medals'?'rgba(60,45,25,.3)':THEME=='dark'?'rgba(255,255,255,.3)':'rgba(60,50,90,.3)';g.lineWidth=.9;g.setLineDash([1,4]);g.stroke();g.setLineDash([]);
 const [px,py]=P(up),[qx,qy]=P(up+.01),ang=Math.atan2(qy-py,qx-px);
 if(px>-30&&py>-30&&px<V.W+30&&py<V.H+30){
  if(lk=='crystal'){const m2=36,lt=[],rt=[];for(let i=0;i<=m2;i++){const u=up-.22*(1-i/m2),[ax,ay]=P(u),[bx,by]=P(u+.002),nx=-(by-ay),ny=bx-ax,ln=Math.hypot(nx,ny)||1,w=s*.45*(i/m2);lt.push([ax+nx/ln*w,ay+ny/ln*w]);rt.push([ax-nx/ln*w,ay-ny/ln*w])}
   const [tx,ty]=P(up-.22),tg=g.createLinearGradient(tx,ty,px,py);tg.addColorStop(0,rgbaH(col,0));tg.addColorStop(1,rgbaH(col,.75));g.globalCompositeOperation=THEME=='dark'?'lighter':'source-over';g.fillStyle=tg;g.beginPath();lt.forEach((p,i)=>i?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1]));for(let i=rt.length-1;i>=0;i--)g.lineTo(rt[i][0],rt[i][1]);g.closePath();g.fill();
   const q=g.createRadialGradient(px,py,0,px,py,s*1.1);q.addColorStop(0,'rgba(255,255,255,.95)');q.addColorStop(.35,rgbaH(col,.85));q.addColorStop(1,rgbaH(col,0));g.fillStyle=q;g.beginPath();g.arc(px,py,s*1.1,0,7);g.fill()}
  else if(vehicle){const alt=Math.sin(Math.PI*up)*Math.max(8,Math.min(26,d*.06)),sh='rgba(16,26,10,.26)';
   if(lk=='medals'){lkPaper(px+alt*.7,py+alt*.9,ang,s,sh);lkPaper(px,py,ang,s,'#f7efdc','#6a4a24')}
   else{for(let i=0;i<6;i++){const [sx,sy]=P(up-i*.018-.01),r=1.6-i*.18,ox=(H32(i,seed)-.5)*5,oy=(H32(i+9,seed)-.5)*5;g.fillStyle=`rgba(255,240,170,${.9-i*.13})`;g.fillRect(sx+ox-r*.4,sy+oy-r*1.6,r*.8,r*3.2);g.fillRect(sx+ox-r*1.6,sy+oy-r*.4,r*3.2,r*.8)}
    lkPlane(px+alt*.7,py+alt*.9,ang,s,sh);lkPlane(px,py,ang,s,'#fff6d8','#a8770f');g.save();g.translate(px,py);g.rotate(ang);g.fillStyle=col;g.fillRect(-s*.95,-s*.12,s*.25,s*.24);g.restore()}}}
 g.restore()}
function loadJSON(u){return fetch(u).then(r=>{if(!r.ok)throw new Error(u);return r.json()})}
function prepTracks(T){
 const thin=(a,d)=>{const o=[a[0],a[1]];let px=a[0],py=a[1];const n=a.length;for(let i=2;i<n-2;i+=2){const dx=a[i]-px,dy=a[i+1]-py;if(dx*dx+dy*dy>d*d){o.push(a[i],a[i+1]);px=a[i];py=a[i+1]}}o.push(a[n-2],a[n-1]);return Float32Array.from(o)};
 TR=T.map(r=>{const n=(r.length-2)/2;const a=new Float64Array(n*2);let la=r[2],lo=r[3];a[0]=MX(lo/1e5);a[1]=MY(la/1e5);for(let i=1;i<n;i++){la+=r[2+i*2];lo+=r[3+i*2];a[i*2]=MX(lo/1e5);a[i*2+1]=MY(la/1e5)}let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;for(let i=0;i<a.length;i+=2){if(a[i]<x0)x0=a[i];if(a[i]>x1)x1=a[i];if(a[i+1]<y0)y0=a[i+1];if(a[i+1]>y1)y1=a[i+1]}const l3=thin(a,3e-7),lm=thin(l3,1.2e-6),l1=thin(lm,5e-6),lc=thin(l1,2.4e-5);return {d:r[0],c:r[1],p:a,l3,lm,l1,lc,bb:[x0,y0,x1,y1]}});
 TR.forEach((l,i)=>{l.on=true;(byDay[l.d]=byDay[l.d]||[]).push(i)});
 for(const L in LODS){const cs=LODS[L],M=IDX[L]=new Map();TR.forEach((l,li)=>{const a=l[L];let cx=Math.floor(a[0]*cs),cy=Math.floor(a[1]*cs),st=0;const push=(e)=>{const k=cx+','+cy;let arr=M.get(k);if(!arr){arr=[];M.set(k,arr)}arr.push(li,a.subarray(st,e))};for(let j=2;j<a.length;j+=2){const nx=Math.floor(a[j]*cs),ny=Math.floor(a[j+1]*cs);if(nx!==cx||ny!==cy){push(j+2);st=j;cx=nx;cy=ny}}push(a.length)})}
}
const CHK=400;const LODS={lc:256,l1:1024,lm:4096,l3:16384,p:65536},IDX={};
function tileDraw(st,sel,order,style,bb){
 const L=lodKey(),cs=LODS[L],S=V.S;if(!st.lods)st.lods={};const cache=st.lods[L]||(st.lods[L]=new Map());
 const m=4/S,x0=Math.floor((bb[0]-m)*cs),x1=Math.floor((bb[2]+m)*cs),y0=Math.floor((bb[1]-m)*cs),y1=Math.floor((bb[3]+m)*cs);
 const by=new Map();
 for(let x=x0;x<=x1;x++)for(let y=y0;y<=y1;y++){const k=x+','+y;let ent=cache.get(k);if(!ent){ent=new Map();const pcs=IDX[L].get(k);if(pcs)for(let q=0;q<pcs.length;q+=2){const kk=sel(pcs[q]);if(kk==null)continue;let L=ent.get(kk);if(!L){L=[];ent.set(kk,L)}let p=L[L.length-1];if(!p||p.n>=CHK){p=new Path2D();p.n=0;L.push(p)}const a=pcs[q+1];p.moveTo(a[0],a[1]);for(let j=2;j<a.length;j+=2)p.lineTo(a[j],a[j+1]);p.n+=a.length/2}cache.set(k,ent);if(cache.size>6000)cache.clear()}
  for(const [kk,ps] of ent){let l=by.get(kk);if(!l){l=[];by.set(kk,l)}l.push(...ps)}}
 const keys=[...by.keys()].sort((a,b)=>order(a)-order(b));
 for(const kk of keys){style(kk);for(const p of by.get(kk))ctx.stroke(p)}
}
const lodKey=()=>{const z=Math.log2(V.S/256);return z<8.5?'lc':z<10.5?'l1':z<12.5?'lm':z<14.5?'l3':'p'};
const PC=new Map();
function pathOf(ids,key){const k=key+'#'+ids.id;let p=PC.get(k);if(p)return p;p=new Path2D();for(const i of ids){const a=TR[i][key];p.moveTo(a[0],a[1]);for(let j=2;j<a.length;j+=2)p.lineTo(a[j],a[j+1])}PC.set(k,p);if(PC.size>3000)PC.clear();return p}
let IDN=0;const idList=a=>{a.id=++IDN;return a};
function arcPts(x1,y1,x2,y2,b=.18){const dx=x2-x1,dy=y2-y1;let nx=-dy,ny=dx;if(ny>0){nx=-nx;ny=-ny}return [x1,y1,(x1+x2)/2+nx*b,(y1+y2)/2+ny*b,x2,y2]}
function strokeArc(a,cols,w,dl,gap){const S=V.S;{const f=SM('fly');w*=f.width;if(f.dash=='solid')gap=cols.length>1?0.001:0;else if(f.dash=='dotted'){dl=.01;gap=5}else if(f.dash=='sparse'){dl=.01;gap=9}else if(f.dash=='longdash'){dl=15;gap=6}}if(S>150000){ctx.beginPath();ctx.moveTo(a[0],a[1]);ctx.quadraticCurveTo(a[2],a[3],a[4],a[5]);ctx.strokeStyle=cols[0];ctx.lineWidth=w/S;ctx.globalAlpha=Math.min(ctx.globalAlpha,.5);ctx.stroke();return}const per=(dl+gap)/S,P=per*cols.length;cols.forEach((c,i)=>{ctx.beginPath();ctx.moveTo(a[0],a[1]);ctx.quadraticCurveTo(a[2],a[3],a[4],a[5]);ctx.setLineDash([dl/S,P-dl/S]);ctx.lineDashOffset=-per*i;ctx.strokeStyle=c;ctx.lineWidth=w/S;ctx.lineCap='round';ctx.stroke()});ctx.setLineDash([]);ctx.lineDashOffset=0}

/* ================= KARTE 1: REISEN ================= */
const R={w:new Set(WHO),m:new Set(MODES),y:null,color:'w'};
let RC=null;
function yearOn(y){return R.y==null||(Array.isArray(R.y)?y<=R.y[1]:y==R.y)}
function tripOn(t){return R.w.has(t.w)&&t.m.some(m=>R.m.has(m))&&yearOn(t.y)}
/* ---- "Wer": one person or one group, chosen in the bar on top of the side panel ---- */
let SEL=null,SELV=0;
const GCFG=()=>D.groups_cfg||[];
function isGroup(n){return GCFG().some(g=>g.name==n)}
function members(n){if(!n)return D.persons;const g=GCFG().find(g=>g.name==n);return g?g.members:[n]}
function selMask(){let m=0;for(const n of members(SEL)){const i=D.persons.indexOf(n);if(i>=0)m|=1<<Math.min(i,30)}return m}
function tripSel(t){if(!SEL)return true;if(!t)return false;if(t.w==SEL)return true;return !isGroup(SEL)&&members(t.w).includes(SEL)&&isGroup(t.w)}
function dayTrip(di){const r=D.days[di];return r&&r[6]>=0?tripById[r[6]]:null}
function daySel(di){if(!SEL)return true;const t=dayTrip(di);if(isGroup(SEL))return !!t&&t.w==SEL;return tripSel(t)||!!((D.dayP||[])[di]&selMask())}
function trackSel(li){if(!SEL)return true;const p=(D.trackP||[])[li],pn=p>=0?D.persons[p]:null;const t=dayTrip(TR[li].d);if(isGroup(SEL)){const ms=members(SEL);return !!t&&t.w==SEL&&(!ms.length||ms.includes(pn))}return pn==SEL}
function flightSel(f){if(!SEL)return true;const pn=f[4]>=0?D.persons[f[4]]:null;const t=dayTrip(dayIdx(f[0]));if(isGroup(SEL)){const ms=members(SEL);return !!t&&t.w==SEL&&(!ms.length||ms.includes(pn))}return pn==SEL}
function placeSel(p){if(!SEL||p[9]=='Zuhause')return true;if(p[8]>=0&&tripById[p[8]]&&tripById[p[8]].w==SEL)return true;return !isGroup(SEL)&&!!(p[10]&selMask())}
function whoBar(){const ps=D.persons||[],gs=GCFG().map(g=>g.name);const box=$('whobar');
 if(!ps.length&&!gs.length){box.innerHTML='<div class="wb-empty">Noch keine Personen oder Gruppen. <a href="app.html#people">Einrichten</a></div>';return}
 const ini=n=>n?String(n).trim().split(/\s+/).map(w=>w[0]).join('').slice(0,2).toUpperCase():'★';
 const chip=(n,ico)=>`<button class="chip ${SEL==n?'on':''}" style="--c:${n?WCOL[n]||'#8B3DFF':MC.strong}" data-n="${esc(n||'')}" aria-pressed="${SEL==n}"><i></i><b class="av" aria-hidden="true">${esc(ini(n))}</b>${ico}<span class="cn">${esc(n||'Alle')}</span></button>`;
 box.innerHTML='<div class="wb-t">ANZEIGEN FÜR <span class="r"><label class="aswitch" title="Flugzeuge, Züge und Autos bewegen sich"><input type="checkbox" id="animT"'+(animWanted()?' checked':'')+'><span></span>ANIMATION</label><a href="app.html#people" title="Personen und Gruppen bearbeiten">bearbeiten</a></span></div><div class="chips">'+chip(null,'')+ps.map(n=>chip(n,'<span class="wi" aria-hidden="true">👤</span>')).join('')+gs.map(n=>chip(n,'<span class="wi" aria-hidden="true">👥</span>')).join('')+'</div>';
 box.querySelectorAll('.chip').forEach(b=>b.onclick=()=>setSel(b.dataset.n||null));const at=$('animT');if(at)at.onchange=()=>{try{localStorage.setItem('wm-anim',at.checked?'1':'0')}catch(e){}full();animRestart()}}
function setSel(n){SEL=SEL==n?null:n;SELV++;
 R.w=new Set(SEL?WHO.filter(w=>tripSel({w})):WHO);
 if(TR){for(let i=0;i<TR.length;i++)TR[i].on=trackSel(i);byDay={};TR.forEach((l,i)=>{if(l.on)(byDay[l.d]=byDay[l.d]||[]).push(i)})}
 O.pl=null;F.sc=null;F.st=null;F.done=-1;RG.groups=null;RG.agg=null;
 whoBar();enter(TAB)}
function alltagKm(){const o={};if(!R.w.has('Alltag'))return o;for(const y in D.alltagYear){if(!yearOn(+y))continue;for(const m in D.alltagYear[y])if(R.m.has(m))o[m]=(o[m]||0)+D.alltagYear[y][m]}return o}
const GRP={};
const km2=(a,b,c,d)=>Math.hypot((a-c)*111,(b-d)*111*Math.cos(a*Math.PI/180));
function ptGroup(A,t){if(!A)return null;if(km2(A[0],A[1],HOME[0],HOME[1])<70)return 'home';let best=null,bd=1e9;for(const g of D.groups){const d=km2(g[2],g[3],A[0],A[1]);if(d<bd){bd=d;best=g[0]}}if(bd<80)return best;return t.g||'p:'+A[0]+','+A[1]}
function buildR(){
 const on=D.trips.filter(tripOn),onIds=new Set(on.map(t=>t.id));
 // cells
 const G=.02,col=R.color=='w'?WCOL:MCOL,AI=WHO.indexOf('Alltag'),layers=R.color=='w'?[[AI],WHO.map((_,i)=>i).filter(i=>i!=AI)]:[WHO.map((_,i)=>i)];
 const out=[];
 for(const L of layers){const cells=new Map();for(const [a,b,w,m,yr,v] of D.cells){if(!L.includes(w)||!R.w.has(WHO[w])||!R.m.has(MODES[m])||!yearOn(yr))continue;const k=a+','+b;let c=cells.get(k);if(!c){c={};cells.set(k,c)}const kk=R.color=='w'?WHO[w]:MODES[m];c[kk]=(c[kk]||0)+v}
  out.push(cells)}
 // far routes: tracks on days of far trips
 const far=[],near=[],est=[];
 // estimates
 for(const [ti,la,lo,rk] of D.est){const t=tripById[ti];if(!t||!onIds.has(t.id))continue;est.push([la,lo,rk,R.color=='w'?WCOL[t.w]:MCOL[t.m[0]]])}
 // flights
 const pairs=new Map();if(R.m.has('fly'))for(const t of on){for(const [x,y,ia,ib,sp] of t.fl){const A=ia?'ap:'+ia:ptGroup(x,t),Bg=ib?'ap:'+ib:ptGroup(y,t);if(!A||!Bg||A==Bg)continue;const hm=q=>q=='home'||(q.startsWith('ap:')&&D.airports[q.slice(3)]&&km2(D.airports[q.slice(3)][0],D.airports[q.slice(3)][1],HOME[0],HOME[1])<150);const k=[A,Bg].sort((p,q)=>hm(q)-hm(p)||p.localeCompare(q)).join('>');let e=pairs.get(k);if(!e){e={k,ws:new Set(),g:new Set(),sp:false};pairs.set(k,e)}if(sp)e.sp=true;e.ws.add(t.w);if(t.g&&!t.gps)e.g.add(t.g)}}
 const gr=[];for(const t of on){if(!t.gr||!(t.g||t.st))continue;/* only trips far away: short day trips stay dots */const m=t.m.find(x=>x=='rail'||x=='road')||'road';gr.push({t,m,col:R.color=='w'?WCOL[t.w]:MCOL[m]})}
 RC={own:out,far,est,near,gr,pairs:[...pairs.values()],on,onIds,st:{},ver:(RC?RC.ver:0)+1};
}
/* airports at the ends of flight arcs: a small tag with the IATA code */
function apMarks(keys){const S=V.S;if(S<1500)return;const seen=new Set();ctx.font='800 10.5px Inter,system-ui,sans-serif';ctx.textBaseline='middle';
 for(const k of keys){if(!k.startsWith('ap:')||seen.has(k))continue;seen.add(k);const code=k.slice(3),a=D.airports[code];if(!a)continue;const [x,y]=toS(MX(a[1]),MY(a[0]));if(x<-30||y<-30||x>V.W+30||y>V.H+30)continue;
  const w=ctx.measureText(code).width+20;ctx.fillStyle=MC.land;ctx.strokeStyle=MCOL.fly;ctx.lineWidth=1.4;ctx.beginPath();ctx.roundRect(x+6,y-9,w,18,9);ctx.fill();ctx.stroke();
  ctx.fillStyle=MCOL.fly;ctx.fillText('✈',x+10,y+.5);ctx.fillStyle=MC.strong;ctx.fillText(code,x+21,y+.5);ctx.beginPath();ctx.arc(x,y,3.2,0,7);ctx.fillStyle=MCOL.fly;ctx.fill();ctx.strokeStyle=MC.ring;ctx.lineWidth=1.5;ctx.stroke();placed.push([x+6,y-9,x+6+w,y+9])}
 ctx.textBaseline='alphabetic'}
function gpos(g){if(g=='home')return [MX(HOME[1]),MY(HOME[0])];if(g.startsWith('ap:')){const a=D.airports[g.slice(3)];return [MX(a[1]),MY(a[0])]}if(g.startsWith('p:')){const [a,b]=g.slice(2).split(',').map(Number);return [MX(b),MY(a)]}const G=D.groups.find(x=>x[0]==g);return [MX(G[3]),MY(G[2])]}
/* estimated way of a trip without GPS (from the server: straight runs over land / sea), gently curved, in world units */
function estRoute(t){if(!t.gr)return null;if(t._er)return t._er;
 /* the server sends the way over land (and ferries where needed) as runs of lat/lon pairs */
 t._er=t.gr.map(([sea,a,m])=>{const pts=[];for(let i=0;i+1<a.length;i+=2)pts.push([MX(a[i+1]),MY(a[i])]);return {sea:!!sea,pts,m:m||null}});return t._er}
function drawEst(list,lwBase){const E=ST('est');if(E.show===false||!list||!list.length)return;const S=V.S;ctx.save();ctx.lineCap='round';ctx.lineJoin='round';ctx.globalAlpha=(E.opacity??.8)*(S>60000?.45:S>25000?.7:1);
 for(const g of list){const rs=estRoute(g.t);if(!rs)continue;for(const r of rs){if(r.sea&&E.ferry===false)continue;const m=r.sea?'ferry':(r.m||g.m);if(!r.sea&&!R.m.has(m))continue;ctx.beginPath();r.pts.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));
  if(r.sea){ctx.strokeStyle=R.color=='w'?g.col:MCOL.ferry;ctx.lineWidth=lwBase*1.1;ctx.setLineDash([.01/S,5.5/S])}else{ctx.strokeStyle=R.color=='w'?g.col:MCOL[m]||g.col;ctx.lineWidth=lwBase;ctx.setLineDash(dashFor(E.dash||'solid',S))}ctx.stroke()}}
 ctx.setLineDash([]);ctx.restore()}
/* areas that melt together: every place is a soft blob, where blobs overlap they grow into one shape (metaballs) */
let MB=null;
function metaAreas(own,r0,AR,col,bb){
 const c=ctx.canvas,W=c.width,H=c.height,T=ctx.getTransform(),k=T.a;if(r0*k<.5)return;
 const R=r0*(1+.9*(AR.connect??1)),th=Math.max(.04,1-r0/R),Rpx=R*k,e=Math.max(.008,(.9*(AR.smooth??1))/Rpx);
 const ow=AR.outline!==false&&AR.outline_color!='none'?(AR.outline_width??1.4):0,owf=ow/Rpx,op=AR.opacity??1;
 if(!MB){MB=document.createElement('canvas')}if(MB.width!==W||MB.height!==H){MB.width=W;MB.height=H}
 const g=MB.getContext('2d',{willReadFrequently:true});const hex=h=>[parseInt(h.slice(1,3),16),parseInt(h.slice(3,5),16),parseInt(h.slice(5,7),16)];
 for(const q in own){const pts=own[q].filter(([x,y])=>x>bb[0]-R&&x<bb[2]+R&&y>bb[1]-R&&y<bb[3]+R);if(!pts.length)continue;
  g.setTransform(1,0,0,1,0,0);g.clearRect(0,0,W,H);g.setTransform(T);g.globalCompositeOperation='lighter';
  for(const [x,y] of pts){const gr=g.createRadialGradient(x,y,0,x,y,R);gr.addColorStop(0,'rgba(255,255,255,1)');gr.addColorStop(.35,'rgba(255,255,255,.72)');gr.addColorStop(1,'rgba(255,255,255,0)');g.fillStyle=gr;g.beginPath();g.arc(x,y,R,0,7);g.fill()}
  g.setTransform(1,0,0,1,0,0);g.globalCompositeOperation='source-over';
  const id=g.getImageData(0,0,W,H),d=id.data,F=hex(tint(col[q],q=='Alltag'?.2:.3)),C=hex(col[q]),O=AR.outline_color=='white'?[255,255,255]:AR.outline_color=='darker'?C.map(v=>Math.round(v*.6)):C;
  for(let i=0;i<d.length;i+=4){const a=d[i+3]/255;if(a<th-e){d[i+3]=0;continue}const m=Math.min(1,(a-th+e)/(2*e));let ol=0;if(owf>0)ol=1-Math.max(0,Math.min(1,(a-th-owf)/e));
   d[i]=F[0]+(O[0]-F[0])*ol;d[i+1]=F[1]+(O[1]-F[1])*ol;d[i+2]=F[2]+(O[2]-F[2])*ol;d[i+3]=255*m*op}
  g.putImageData(id,0,0);ctx.save();ctx.setTransform(1,0,0,1,0,0);ctx.drawImage(MB,0,0);ctx.restore()}}
function areaLayer(cells,S){
 const G=.02,cellpx=G*1.4/360*S,k=Math.max(1,Math.round(7*(STYLE?STYLE.areas.size:1)/cellpx));const key=k;if(cells._k===key)return cells._own;
 const agg=new Map();for(const [kk,c] of cells){const [a,b]=kk.split(',').map(Number);const A=Math.floor(a/k),Bb=Math.floor(b/k),K=A+','+Bb;let o=agg.get(K);if(!o){o={};agg.set(K,o)}for(const q in c)o[q]=(o[q]||0)+c[q]}
 const own={};for(const [kk,c] of agg){const [a,b]=kk.split(',').map(Number);let nb=0;for(const da of[-1,0,1])for(const db of[-1,0,1])if(agg.has((a+da)+','+(b+db)))nb++;if(nb<(k>1?2:3))continue;let best=null,bv=-1;for(const q in c)if(c[q]>bv){bv=c[q];best=q}(own[best]=own[best]||[]).push([MX((b+.5)*k*G*1.4),MY((a+.5)*k*G)])}
 cells._k=key;cells._own=own;cells._r=k*G*1.4/360*.8;return own}
function contentR(bb){
 drawBase();
 const S=V.S,col=R.color=='w'?WCOL:MCOL;
 const ZOOMED=S>=55000;

 // areas
 const AR=ST('areas');
 for(const cells of (AR.show===false||S>=150000?[]:ZOOMED?RC.own.slice(0,R.color=='w'?1:0):RC.own)){const own=areaLayer(cells,S),r0=cells._r;
  if(AR.shape!='circles'){metaAreas(own,r0,AR,col,bb);continue}
  ctx.globalAlpha=AR.opacity??1;const ow=AR.outline!==false&&AR.outline_color!='none'?(AR.outline_width??1.4):0;
  if(ow>0)for(const q in own){ctx.fillStyle=AR.outline_color=='white'?'#ffffff':AR.outline_color=='darker'?shade(col[q],.6):col[q];ctx.beginPath();const r=r0+ow/S;for(const [x,y] of own[q]){ctx.moveTo(x+r,y);ctx.arc(x,y,r,0,7)}ctx.fill()}
  for(const q in own){ctx.fillStyle=tint(col[q],q=='Alltag'?.2:.3);ctx.beginPath();for(const [x,y] of own[q]){ctx.moveTo(x+r0,y);ctx.arc(x,y,r0,0,7)}ctx.fill()}
 }
 ctx.globalAlpha=1;
 // far routes
 ctx.lineJoin='round';ctx.lineCap='round';
 const lw=Math.max(1.6,Math.min(3.2,S/6000))/S*(ST('trips').line_width??1);
 const vb=[V.cx-V.W/2/S,V.cy-V.H/2/S,V.cx+V.W/2/S,V.cy+V.H/2/S];
 tileDraw(RC.st,li=>{const l=TR[li],r=D.days[l.d];if(!l.on)return null;if(!r||r[6]<0)return null;const t=tripById[r[6]];if(!RC.onIds.has(t.id))return null;if(!t.g&&!ZOOMED)return null;const m=TCLS[l.c];if(!R.m.has(m))return null;return (R.color=='w'?WCOL[t.w]:MCOL[m])+'|'+m+(t.g?'|f':'|n')},k=>k.endsWith('|f')?1:0,k=>{const f=k.endsWith('|f'),m=k.slice(8,-2);ctx.strokeStyle=k.slice(0,7);ctx.lineWidth=(f?lw:lw*.75)*SM(m).width;setDash(m,V.S);ctx.globalAlpha=1},bb);ctx.setLineDash([]);ctx.globalAlpha=1;
 drawGaps(g=>{const r=D.days[g[0]];if(!r||r[6]<0||!gapSel(g))return null;const t=tripById[r[6]];if(!RC.onIds.has(t.id)||(!t.g&&!ZOOMED))return null;const m=TCLS[g[1]];if(!R.m.has(m))return null;return R.color=='w'?WCOL[t.w]:MCOL[m]},lw,bb)}
function drawR(){
 TKEY='R'+RC.ver+'_'+STV+(V.S>=150000?'Z':V.S>=55000?'z':'');drawTiles(contentR);worldT();const S=V.S;ctx.globalAlpha=1;
 const soft=ST('areas').shape!='circles';for(const [la,lo,rk,c] of RC.est){const r=rk/(40075*Math.cos(la*Math.PI/180)),x=MX(lo),y=MY(la);ctx.beginPath();ctx.arc(x,y,r,0,7);
  if(soft){const g=ctx.createRadialGradient(x,y,0,x,y,r);g.addColorStop(0,tint(c,.55));g.addColorStop(.6,tint(c,.4));g.addColorStop(1,'rgba(0,0,0,0)');ctx.fillStyle=g;ctx.globalAlpha=.5*(ST('areas').opacity??1);ctx.fill();ctx.globalAlpha=1;continue}
  ctx.fillStyle=tint(c,.82);ctx.globalAlpha=.55;ctx.fill();ctx.globalAlpha=1;ctx.setLineDash([1/S,5/S]);ctx.lineCap='round';ctx.strokeStyle=c;ctx.lineWidth=2.8/S;ctx.stroke();ctx.setLineDash([])}
 // flights
 const TP=ST('trips'),AH=TP.arc_height??1,LWm=TP.line_width??1;
 drawEst(RC.gr,2.2/S*LWm);
 /* lines always stay on the map; the animation only moves the vehicles */const LK=LOOK(),LKF=[];for(const e of RC.pairs){const [A,Bg]=e.k.split('>');const [x1,y1]=gpos(A),[x2,y2]=gpos(Bg);const a=arcPts(x1,y1,x2,y2,(e.sp?.07:A=='home'?.2:.18)*AH);const cols=R.color=='w'?WHO.filter(w=>e.ws.has(w)).map(w=>WCOL[w]):[MCOL.fly];if(LK!='classic'){LKF.push([a,cols[0],e.k]);continue}strokeArc(a,cols,2.4*LWm,8,6)}
 endWorld();
 /* game looks: flights are drawn on the screen (trail, aircraft, shadow); the moving planes of the animation take over when it runs */
 if(LK!='classic'){const veh=!(animOn()&&ST('anim').planes!==false);let k=0;for(const [a,c,key] of LKF){let h=0;for(let i=0;i<key.length;i++)h=(h*31+key.charCodeAt(i))|0;lookFlight(a,c,h&0xffff,veh&&k++<14)}}placed.length=0;usedNames.clear();
 for(const t of RC.on){if(!t.st)continue;t.st.forEach(([la,lo,nm,ap],k)=>{const [x,y]=toS(MX(lo),MY(la));if(x<-20||y<-20||x>V.W+20||y>V.H+20)return;const c=WCOL[t.w]||MC.strong;ctx.beginPath();ctx.arc(x,y,3.6,0,7);ctx.fillStyle=MC.ring;ctx.fill();ctx.beginPath();ctx.arc(x,y,2.6,0,7);ctx.fillStyle=c;ctx.fill();if((k>0||ap)&&V.S>12000)lbl(ap?'✈ '+ap:nm,x+6,y+4,11,600,MC.text)})}
 if(LK!='classic'){const [hx,hy]=toS(MX(HOME[1]),MY(HOME[0]));lookMark(hx,hy,7,['#FF2DAA'],99,true);lbl('Zuhause',hx+15,hy-8,14,800,MC.strong,'left',4.5,true)}else homeMark();if(TP.airports!==false)apMarks(RC.pairs.flatMap(e=>e.k.split(">")));const DS=TP.dot_size??1,LS=TP.label_size??1,LM=TP.labels||'normal';
 // destinations
 RC.mbox=null;let off=null;
 for(const G of D.groups){const [g,name,la,lo,an,fs,major,gkm]=G;const ts=RC.on.filter(t=>t.g==g);if(!ts.length)continue;const [x,y]=toS(MX(lo),MY(la));if(x<-80||y<-40||x>V.W+80||y>V.H+40){if(gkm>1500&&(!off||gkm>off[0][7]))off=[G,ts];continue}
  const cs=R.color=='w'?WHO.filter(w=>ts.some(t=>t.w==w)).map(w=>WCOL[w]):[...new Set(ts.flatMap(t=>t.m).filter(m=>R.m.has(m)))].map(m=>MCOL[m]);let r=(major?7.5:5.5)*DS;if(LK!='classic')r=lookMark(x,y,r,cs,ts.length,false)*.8;else pieS(x,y,r,cs);
  if(LM!='off'&&(LM!='few'||major))lbl(name,an=='end'?x-r-6:an=='middle'?x:x+r+6,an=='middle'?y-r-6:y+5,fs*LS,major?780:650,major?MC.strong:MC.text,an=='end'?'right':an=='middle'?'center':'left',4.5,LM=='all'||(major&&LM!='normal'))}
 // near trips
 const near={};for(const t of RC.on){if(t.g||t.nopos)continue;const k=t.name;(near[k]=near[k]||{name:k,p:t.p,ts:[]}).ts.push(t)}
 const ns=Object.values(near).sort((a,b)=>b.ts.length-a.ts.length);
 for(const q of ns){const [x,y]=toS(MX(q.p[1]),MY(q.p[0]));if(x<-20||y<-20||x>V.W+20||y>V.H+20)continue;const r=Math.min(9,3+Math.sqrt(q.ts.length)*1.3)*(S>40000?1:.75)*DS;const cs=R.color=='w'?WHO.filter(w=>q.ts.some(t=>t.w==w)).map(w=>WCOL[w]):[...new Set(q.ts.flatMap(t=>t.m).filter(m=>R.m.has(m)))].map(m=>MCOL[m]);if(LK!='classic')lookMark(x,y,r,cs,q.ts.length,false);else pieS(x,y,r,cs);q.sx=x;q.sy=y;q.r=r;if(LM=='all'||(LM=='normal'&&S>45000))lbl(q.name,x+r+4,y+4,12*LS,650,MC.text)}
 RC.ndots=ns;
 if(off)edgeBadge(off[0],off[1]);
 drawPlaceLabels();
}
function edgeBadge(G,ts){if(V.S>40000)return;const x=V.W-70,y=V.H-58;const c=R.color=='w'?WCOL[ts[0].w]:MCOL.fly;ctx.font='800 13px Inter, sans-serif';const [gx,gy]=toS(MX(G[3]),MY(G[2]));const ar=(gy>V.H?'↓':gy<0?'↑':'')+(gx>V.W?'→':gx<0?'←':'');const txt=G[1]+' '+ar+' '+fmt(G[7])+' km';RC.mg=[G[1],ts];const w=ctx.measureText(txt).width+20;ctx.fillStyle=MC.land;ctx.strokeStyle=c;ctx.lineWidth=1.5;ctx.beginPath();ctx.roundRect(x-w,y-14,w,28,10);ctx.fill();ctx.stroke();ctx.fillStyle=MC.strong;ctx.fillText(txt,x-w+10,y+5);RC.mbox=[x-w,y-14,x,y+14]}
function sideR(){
 const on=RC.on,ak=alltagKm(),tk={};on.forEach(t=>{for(const k in t.k)if(R.m.has(k))tk[k]=(tk[k]||0)+t.k[k]});
 const ts=Object.values(tk).reduce((a,b)=>a+b,0),as=Object.values(ak).reduce((a,b)=>a+b,0);
 if(!$('r1'))$('r-stats').innerHTML=statHTML([['r1','Reisen'],['r2','Nächte weg'],['r3','km unterwegs'],['r4','Länder']]);
 count('r1',on.length);count('r2',on.reduce((s,t)=>s+t.n,0));count('r3',ts+as);count('r4',new Set(on.map(t=>t.c)).size);
 const both={};for(const k of MODES){const v=(tk[k]||0)+(ak[k]||0);if(v)both[k]=v}
 $('r-split').innerHTML=mbars({Reisen:ts,Alltag:as},{Reisen:'#8B3DFF',Alltag:WCOL.Alltag},{})+'<div style="height:8px"></div>'+mbars(both,MCOL,MNAME);
 const yrs=[];TYEARS.forEach((y,i)=>{if(i&&y-TYEARS[i-1]>2)yrs.push('gap');else if(i)for(let q=TYEARS[i-1]+1;q<y;q++)yrs.push(q);yrs.push(y)});
 const all=D.trips.filter(t=>R.w.has(t.w)&&t.m.some(m=>R.m.has(m)));const by={};all.forEach(t=>{(by[t.y]=by[t.y]||[]).push(t)});const mx=Math.max(1,...Object.values(by).map(a=>a.length));
 $('r-years').innerHTML=yrs.map(y=>{if(y=='gap')return '<div class="yb gap"><span>…</span></div>';const a=by[y]||[];const keys=R.color=='w'?WHO.filter(w=>w!='Alltag'):MODES.slice(0,4),col=R.color=='w'?WCOL:MCOL;const segs=keys.map(q=>{const n=a.filter(t=>R.color=='w'?t.w==q:t.m[0]==q).length;return n?`<div style="height:${n/mx*76}px;background:${col[q]}"></div>`:''}).join('');return `<div class="yb${yearOn(y)?'':' off'}" data-y="${y}" title="${y}: ${a.length} Reisen"><span>${a.length||''}</span><div class="bar">${segs}</div><span>${String(y).slice(2)}</span></div>`}).join('');
 $('r-years').querySelectorAll('.yb[data-y]').forEach(b=>b.onclick=()=>{stopR();const y=+b.dataset.y;R.y=R.y===y?null:y;updR()});
 $('r-ylab').textContent=R.y==null?'Alle Jahre':Array.isArray(R.y)?`bis ${R.y[1]}`:`Nur ${R.y}`;
 const grp={};on.forEach(t=>{const G=t.g&&D.groups.find(g=>g[0]==t.g);const key=G?G[1]:t.name;(grp[key]=grp[key]||{name:key,g:t.g,ts:[]}).ts.push(t)});
 const top=Object.values(grp).sort((a,b)=>b.ts.reduce((s,t)=>s+t.n,0)-a.ts.reduce((s,t)=>s+t.n,0)||b.ts.length-a.ts.length).slice(0,8);
 $('r-top').innerHTML=top.length?top.map((q,i)=>`<div class="trow" data-i="${i}"><span class="n">${i+1}</span><span class="nm">${esc(q.name)} <em>· ${q.ts.length}×</em></span><span class="d">${WHO.filter(w=>q.ts.some(t=>t.w==w)).map(w=>`<i style="background:${WCOL[w]}"></i>`).join('')}<em style="margin-left:6px">${q.ts.reduce((s,t)=>s+t.n,0)} Nächte</em></span></div>`).join(''):'<div class="empty">Keine Reisen mit diesem Filter.</div>';
 $('r-top').querySelectorAll('.trow').forEach(r=>r.onclick=()=>{const q=top[+r.dataset.i];const G=q.g&&D.groups.find(g=>g[0]==q.g);const la=G?G[2]:q.ts[0].p[0],lo=G?G[3]:q.ts[0].p[1];flyTo(MX(lo),MY(la),G?Math.max(V.S,90000):220000);showTrips(q.name,q.ts)});
}
function showTrips(name,ts){ts=[...ts].sort((a,b)=>b.a.localeCompare(a.a));const n=ts.reduce((s,t)=>s+t.n,0),km=ts.reduce((s,t)=>s+t.km,0);
 openDetail(`<h3>${esc(name)}</h3><div class="dsub">${ts.length} ${ts.length==1?'Reise':'Reisen'} · ${esc(n)} Nächte · ${fmt(km)} km · ${esc(ts[0]?ts[0].c:'')}</div>`+ts.map(t=>`<div class="trip"><div class="s" style="background:${WCOL[t.w]}"></div><div><div class="t1">${tWhen(t)||dfmt(t.a)+(t.n?' – '+dfmt(t.b):'')}</div><div class="t2"><span class="pill" style="background:${tint(WCOL[t.w],.18)}">${esc(t.w)}</span>${t.m.map(m=>`<span class="pill">${MNAME[m]}</span>`).join('')}${t.n?t.n+(t.n==1?' Nacht':' Nächte'):'Tagesausflug'} · ${fmt(t.km)} km${t.name!=name?' · '+esc(t.name):''}${t.approx?' · geschätzt':''} · <a href="#" class="edit" data-id="${t.dbid}">bearbeiten</a></div></div></div>`).join(''));$('detail').querySelectorAll('a.edit').forEach(a=>a.onclick=e=>{e.preventDefault();editTrip(+a.dataset.id)})}
function chipsR(){
 $('r-mode').innerHTML=MODES.map(m=>`<button class="chip ${R.m.has(m)?'on':''}" style="--c:${MCOL[m]}" data-m="${m}"><i></i>${MNAME[m]}</button>`).join('');
 $('r-mode').querySelectorAll('.chip').forEach(b=>b.onclick=()=>toggle(R.m,b.dataset.m,MODES,updR))}
function updR(){chipsR();buildR();sideR();legend();full();animRestart()}
let rT=null;function stopR(){if(rT){clearInterval(rT);rT=null;$('r-pico').setAttribute('d','M3 1.5L12 7L3 12.5Z')}}
$('r-play').onclick=()=>{if(rT){stopR();return}const ys=TYEARS;let i=0;R.y=[0,ys[0]];updR();$('r-pico').setAttribute('d','M2.5 1.5H5.5V12.5H2.5ZM8.5 1.5H11.5V12.5H8.5Z');rT=setInterval(()=>{i++;if(i>=ys.length){stopR();return}R.y=[0,ys[i]];updR()},1000)};
$('r-yall').onclick=()=>{stopR();R.y=null;updR()};
segBind('r-color',v=>{R.color=v;updR()});
function hitR(sx,sy){
 if(RC.mbox&&RC.mg&&sx>=RC.mbox[0]&&sx<=RC.mbox[2]&&sy>=RC.mbox[1]&&sy<=RC.mbox[3])return ()=>showTrips(RC.mg[0],RC.mg[1]);
 for(const [g,name,la,lo] of D.groups){const [x,y]=toS(MX(lo),MY(la));if(Math.hypot(x-sx,y-sy)<14){const ts=RC.on.filter(t=>t.g==g);if(ts.length)return ()=>showTrips(name,ts)}}
 for(const q of RC.ndots||[]){if(q.sx!=null&&Math.hypot(q.sx-sx,q.sy-sy)<Math.max(10,q.r+3))return ()=>showTrips(q.name,q.ts)}
 return null}

/* ================= KARTE 2: SPUREN ================= */
const SP={color:'m',modes:new Set(['road','rail','foot','fly']),cat:new Set(['Alltag','Reise']),wd:'all',years:null,chunks:null};
function dayOk(di){const I=dayInfo[di];if(!I||!daySel(di))return false;if(SP.years&&!SP.years.has(I.y))return false;if(SP.wd=='wk'&&(I.dow==0||I.dow==6))return false;if(SP.wd=='we'&&I.dow>0&&I.dow<6)return false;return SP.cat.has(I.cat)}
function keyS(l){const I=dayInfo[l.d];return SP.color=='m'?TCLS[l.c]:SP.color=='y'?String(I.y):I.who}
function colS(k){return SP.color=='m'?MCOL[k]:SP.color=='y'?ycol(k):WCOL[k]}
function buildS(){
 SP.st={};SP.ver=(SP.ver||0)+1;const ch=new Map();
 if(0)TR.forEach((l,i)=>{if(!SP.modes.has(TCLS[l.c])||!dayOk(l.d))return;const k=keyS(l);const ck=k+'|'+(l.d>>3);let c=ch.get(ck);if(!c){c={k,ids:idList([]),bb:[1,1,0,0]};ch.set(ck,c)}c.ids.push(i);c.bb=[Math.min(c.bb[0],l.bb[0]),Math.min(c.bb[1],l.bb[1]),Math.max(c.bb[2],l.bb[2]),Math.max(c.bb[3],l.bb[3])]});
 const order=SP.color=='m'?['foot','road','rail']:SP.color=='w'?WORDER():null;
 SP.chunks=[...ch.values()].sort((a,b)=>order?order.indexOf(a.k)-order.indexOf(b.k):(+a.k)-(+b.k));
 SP.fl=[];if(SP.modes.has('fly')){const d0=dateOf(D.days[0][0]);for(const f of D.flights){const [ds,A,Bp]=f;const di=Math.round((dateOf(ds)-d0)/864e5);if(!dayOk(di)||!flightSel(f))continue;SP.fl.push([arcPts(MX(A[1]),MY(A[0]),MX(Bp[1]),MY(Bp[0])),SP.color=='m'?MCOL.fly:SP.color=='y'?ycol(dayInfo[di].y):WCOL[dayInfo[di].who]])}}
}
/* gaps without a known route: a soft dotted link instead of an interrupted line (setting: dotted / straight / open) */
function gapSel(g){if(!SEL)return true;const pn=g[6]>=0?D.persons[g[6]]:null;const t=dayTrip(g[0]);if(isGroup(SEL)){const ms=members(SEL);return !!t&&t.w==SEL&&(!ms.length||ms.includes(pn))}return pn==SEL}
function drawGaps(colOf,lw,bb){const st=STYLE?STYLE.map.gaps:'dotted';if(st=='open'||!D.gaps)return;const S=V.S,by=new Map(),rt=new Map();
 /* long gaps come with a way along the main roads / railways (g[7]): drawn as a soft solid line, short ones as dots */
 for(const g of D.gaps){const c=colOf(g);if(!c)continue;const x1=MX(g[3]),y1=MY(g[2]),x2=MX(g[5]),y2=MY(g[4]);if(!g[7]&&(Math.max(x1,x2)<bb[0]||Math.min(x1,x2)>bb[2]||Math.max(y1,y2)<bb[1]||Math.min(y1,y2)>bb[3]))continue;
  if(g[7]){let p=rt.get(c);if(!p){p=new Path2D();rt.set(c,p)}const a=g[7];p.moveTo(MX(a[1]),MY(a[0]));for(let k=2;k+1<a.length;k+=2)p.lineTo(MX(a[k+1]),MY(a[k]));continue}
  let p=by.get(c);if(!p){p=new Path2D();by.set(c,p)}p.moveTo(x1,y1);p.lineTo(x2,y2)}
 ctx.save();ctx.lineCap='round';ctx.lineJoin='round';
 ctx.setLineDash([]);ctx.lineWidth=lw*1.1;ctx.globalAlpha=.6;for(const [c,p] of rt){ctx.strokeStyle=c;ctx.stroke(p)}
 ctx.setLineDash(st=='straight'?[]:[.01/S,Math.max(3.2,lw*S*2.4)/S]);ctx.lineWidth=lw*(st=='straight'?.7:1.15);ctx.globalAlpha=st=='straight'?.55:.8;for(const [c,p] of by){ctx.strokeStyle=c;ctx.stroke(p)}ctx.restore()}
function contentS(bb){
 drawBase();const TK=ST('tracks'),S=V.S,lw=(S<300000?1/(S*(V.tf||1)):Math.min(2.4,S/250000)/S)*(TK.width??1),op=TK.opacity??1,eo=TK.everyday_opacity??.7;
 ctx.lineWidth=lw;ctx.lineJoin='round';ctx.lineCap='round';ctx.globalAlpha=1;
 if(TK.glow){ctx.shadowBlur=5*TDPR}
 tileDraw(SP.st,li=>{const l=TR[li];return l.on&&SP.modes.has(TCLS[l.c])&&dayOk(l.d)?keyS(l)+'|'+TCLS[l.c]+'|'+(dayInfo[l.d].cat=='Alltag'?'a':'t'):null},kk=>{const k=kk.split('|')[0];return (kk.endsWith('|t')?100:0)+(SP.color=='m'?['foot','road','rail'].indexOf(k):SP.color=='w'?WORDER().indexOf(k):+k)},kk=>{const [k,m,c]=kk.split('|');const cc=S<300000?colS(k):tint(colS(k),.85);ctx.strokeStyle=cc;if(TK.glow)ctx.shadowColor=cc;ctx.globalAlpha=op*(c=='a'?eo:1);ctx.lineWidth=lw*SM(m).width;setDash(m,S)},bb);ctx.setLineDash([]);ctx.globalAlpha=1;ctx.shadowBlur=0;
 drawGaps(g=>SP.modes.has(TCLS[g[1]])&&dayOk(g[0])&&gapSel(g)?colS(keyS({d:g[0],c:g[1]})):null,lw,bb)}
function drawS(){
 TKEY='S'+SP.ver+'_'+STV;drawTiles(contentS);worldT();const S=V.S;
 ctx.globalAlpha=S>40000?.4:.75;for(const [a,c] of SP.fl)strokeArc(a,[c],S>40000?1.3:1.8,7,5);
 ctx.globalAlpha=1;endWorld();placed.length=0;usedNames.clear();homeMark();if(SP.modes.has('fly')&&ST('tracks').airports!==false)apMarks((SP.flKeys=SP.flKeys||D.flights.flatMap(f=>[f[5]?'ap:'+f[5]:'',f[6]?'ap:'+f[6]:''])).filter(Boolean));drawPlaceLabels();
}
function sideS(){
 const km={road:0,rail:0,foot:0,fly:0},I=[['road',1],['rail',2],['foot',3],['fly',4]];let nd=0;
 D.days.forEach((r,di)=>{if(!dayOk(di))return;let any=0;for(const [m,i] of I){if(!SP.modes.has(m))continue;km[m]+=r[i];if(r[i]>0)any=1}nd+=any});
 const tot=km.road+km.rail+km.foot+km.fly;
 if(!$('sp1'))$('s-stats').innerHTML=statHTML([['sp1','km in der Auswahl'],['sp2','Tage mit Bewegung'],['sp3','km pro Tag (Ø)'],['sp4','Erdumrundungen']]);
 count('sp1',tot);count('sp2',nd);count('sp3',nd?tot/nd:0);$('sp4').textContent=(tot/40075).toFixed(1).replace('.',',');
 $('s-split').innerHTML=mbars(km,MCOL,MNAME);
 const ys=DYEARS,all={};
 D.days.forEach((r,di)=>{const J=dayInfo[di];if(!SP.cat.has(J.cat)||!daySel(di))return;if(SP.wd=='wk'&&(J.dow==0||J.dow==6))return;if(SP.wd=='we'&&J.dow>0&&J.dow<6)return;const o=all[J.y]=all[J.y]||{road:0,rail:0,foot:0,fly:0};for(const [m,i] of I)if(SP.modes.has(m))o[m]+=r[i]});
 const mx=Math.max(1,...ys.map(y=>{const o=all[y]||{};return (o.road||0)+(o.rail||0)+(o.foot||0)+(o.fly||0)}));
 $('s-years').innerHTML=ys.map(y=>{const o=all[y]||{road:0,rail:0,foot:0,fly:0};const t=o.road+o.rail+o.foot+o.fly;const segs=['road','rail','foot','fly'].map(m=>o[m]?`<div style="height:${o[m]/mx*76}px;background:${SP.color=='y'?ycol(y):MCOL[m]}"></div>`:'').join('');return `<div class="yb${SP.years&&!SP.years.has(y)?' off':''}" data-y="${y}" title="${y}: ${fmt(t)} km"><span>${t?Math.round(t/1000)+'k':''}</span><div class="bar">${segs}</div><span>${String(y).slice(2)}</span></div>`}).join('');
 $('s-years').querySelectorAll('.yb').forEach(b=>b.onclick=()=>{const y=+b.dataset.y;SP.years=SP.years&&SP.years.size==1&&SP.years.has(y)?null:new Set([y]);updS()});
}
function chipsS(){const ms=['road','rail','foot','fly'];
 $('s-modes').innerHTML=ms.map(m=>`<button class="chip ${SP.modes.has(m)?'on':''}" style="--c:${MCOL[m]}" data-v="${m}"><i></i>${MNAME[m]}</button>`).join('');
 $('s-modes').querySelectorAll('.chip').forEach(b=>b.onclick=()=>toggle(SP.modes,b.dataset.v,ms,updS));
 $('s-cat').innerHTML=[['Alltag',WCOL.Alltag,'Alltag'],['Reise','#8B3DFF','Reisen']].map(([v,c,n])=>`<button class="chip ${SP.cat.has(v)?'on':''}" style="--c:${c}" data-v="${v}"><i></i>${esc(n)}</button>`).join('');
 $('s-cat').querySelectorAll('.chip').forEach(b=>b.onclick=()=>toggle(SP.cat,b.dataset.v,['Alltag','Reise'],updS))}
function updS(){chipsS();buildS();sideS();legend();full();animRestart()}
segBind('s-color',v=>{SP.color=v;updS()});segBind('s-wd',v=>{SP.wd=v;updS()});

/* ================= KARTE 3: ORTE & TAGE ================= */
const O={day:null,pl:null,hit:[],q:''};
let PCOL={Zuhause:MC.strong,Arbeit:'#FFB000'};
function placeCat(p){if(p[9]=='Zuhause')return 'Zuhause';if(p[7]=='Work'||p[7]=='Inferred Work')return 'Arbeit';if(p[8]>=0&&tripById[p[8]])return tripById[p[8]].w;return 'Alltag'}
function catOfDay(di){const r=D.days[di];return r[6]>=0?tripById[r[6]].w:'Alltag'}
function drawO(){
 TKEY='O'+SELV;drawTiles(()=>drawBase());worldT();const S=V.S;
 if(O.day!=null){ctx.lineJoin='round';ctx.lineCap='round';for(const i of byDay[O.day]||[]){const l=TR[i],a=l.p;ctx.beginPath();ctx.moveTo(a[0],a[1]);for(let j=2;j<a.length;j+=2)ctx.lineTo(a[j],a[j+1]);ctx.strokeStyle=MC.ring;ctx.lineWidth=7/S;ctx.stroke();const mm=TCLS[l.c];ctx.strokeStyle=MCOL[mm];ctx.lineWidth=3.6/S*SM(mm).width;setDash(mm,S);ctx.stroke();ctx.setLineDash([])}
  const ds=D.days[O.day][0];for(const f of D.flights){const [fd,A,Bp]=f;if(fd!=ds||!flightSel(f))continue;strokeArc(arcPts(MX(A[1]),MY(A[0]),MX(Bp[1]),MY(Bp[0])),[MCOL.fly],2.4,8,6)}}
 endWorld();placed.length=0;usedNames.clear();O.hit=[];
 const P=ST('places'),fade=(O.day!=null?.3:1)*(P.opacity??.85),zf=Math.max(.6,Math.min(1.6,Math.log2(S/8000)/4));
 const by=P.size_by||'days',vi=by=='visits'?3:4;if(!O.vmax||O.vmaxBy!==by){O.vmax=Math.max(1,...O.pl.map(p=>p[vi]||0));O.vmaxBy=by}
 const s0=P.size_min??3,s1=Math.max(s0,P.size_max??16),rad=p=>(by=='same'?s0+(s1-s0)*.35:s0+(s1-s0)*Math.log1p(p[vi]||0)/Math.log1p(O.vmax))*zf;
 const colP=p=>P.color_by=='year'?ycol(+String(p[5]).slice(0,4)):P.color_by=='days'?DCOL[p[4]>=60?5:p[4]>=20?4:p[4]>=7?3:p[4]>=3?2:p[4]>=2?1:0]:PCOL[p.cat];
 const list=O.pl.slice().sort((a,b)=>rad(b)-rad(a));
 for(const p of list){const [x,y]=toS(MX(p[1]),MY(p[0]));if(x<-40||y<-40||x>V.W+40||y>V.H+40)continue;const r=rad(p);const c=colP(p);ctx.globalAlpha=fade;
  if(P.style=='glow'){const g=ctx.createRadialGradient(x,y,0,x,y,r*1.6);g.addColorStop(0,c);g.addColorStop(.45,tint(c,.6));g.addColorStop(1,'rgba(0,0,0,0)');ctx.fillStyle=g;ctx.beginPath();ctx.arc(x,y,r*1.6,0,7);ctx.fill()}
  else{ctx.beginPath();ctx.arc(x,y,r,0,7);if(P.style!='ring'){ctx.fillStyle=tint(c,.55);ctx.fill()}ctx.lineWidth=P.style=='ring'?2.2:1.3;ctx.strokeStyle=c;ctx.stroke()}
  O.hit.push([x,y,Math.max(r,9),p])}
 ctx.globalAlpha=1;homeMark();
 const NM=P.names||'big',md=P.name_min_days??2,fs=12*(P.name_size??1),cap=NM=='all'?400:50;
 if(O.day==null&&NM!='none'){let n=0;const seen=new Set();for(const p of O.pl){if(n>cap)break;if(p[9]=='Zuhause'||seen.has(p[9])||(p[4]||0)<md)continue;const [x,y]=toS(MX(p[1]),MY(p[0]));if(x<0||y<0||x>V.W||y>V.H)continue;const r=rad(p);if(lbl(p[9],x+r+3,y+4,fs,650,MC.text,'left',4,P.collide===false)){seen.add(p[9]);n++}}}
 drawPlaceLabels();
}
function calLayout(){const c=$('calc'),w=c.parentElement.clientWidth;const yrs=DYEARS;const lab=28,cell=Math.max(4,Math.floor((w-lab)/53)),rowH=cell*7+10;return {c,w,yrs,lab,cell,rowH,h:rowH*yrs.length}}
function drawCal(){
 const L=calLayout(),c=L.c,dpr=Math.min(2,window.devicePixelRatio||1);c.style.height=L.h+'px';c.width=Math.round(L.w*dpr);c.height=Math.round(L.h*dpr);const g=c.getContext('2d');g.setTransform(dpr,0,0,dpr,0,0);g.clearRect(0,0,L.w,L.h);
 g.font='700 11px Inter, sans-serif';g.fillStyle='#5B5479';L.yrs.forEach((y,i)=>g.fillText(i==0?String(y):"'"+String(y).slice(2),0,i*L.rowH+L.cell*4+2));
 O.calHit=[];const d0=dateOf(D.days[0][0]);
 D.days.forEach((r,di)=>{const d=new Date(d0.getTime()+di*864e5),y=d.getUTCFullYear(),yi=y-DYEARS[0];const jan1=Date.UTC(y,0,1),doy=Math.round((d-jan1)/864e5),wd0=(new Date(jan1).getUTCDay()+6)%7,wd=(d.getUTCDay()+6)%7,col=Math.floor((doy+wd0)/7);
  const x=L.lab+col*L.cell,yy=yi*L.rowH+wd*L.cell;const cat=catOfDay(di),km=r[1]+r[2]+r[3]+r[4];let fill;
  if(!daySel(di))fill=MC.empty;else if(cat!='Alltag')fill=WCOL[cat];else if(!r[7])fill=MC.empty;else if(km<1)fill=MC.cal0;else{const t=Math.min(1,Math.log10(km)/2.6);fill=tint(MC.calHi,.12+t*.6)}
  g.fillStyle=fill;g.fillRect(x,yy,L.cell-1,L.cell-1);if(O.day===di){g.lineWidth=2;g.strokeStyle=MC.strong;g.strokeRect(x-1,yy-1,L.cell+1,L.cell+1)}if(daySel(di))O.calHit.push([x,yy,L.cell,di])});
}
function calAt(e){const r=$('calc').getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;return O.calHit.find(([cx,cy,s])=>x>=cx&&x<cx+s&&y>=cy&&y<cy+s)}
$('calc').addEventListener('click',e=>{const h=calAt(e);if(h)selectDay(h[3])});
$('calc').addEventListener('mousemove',e=>{const h=calAt(e);$('o-hint').textContent=h?dfmt(D.days[h[3]][0])+' · '+fmt(D.days[h[3]][1]+D.days[h[3]][2]+D.days[h[3]][3]+D.days[h[3]][4])+' km':'Tag antippen'});
function bboxOfDay(di){let x0=1,y0=1,x1=0,y1=0;for(const i of byDay[di]||[]){const b=TR[i].bb;x0=Math.min(x0,b[0]);y0=Math.min(y0,b[1]);x1=Math.max(x1,b[2]);y1=Math.max(y1,b[3])}const ds=D.days[di][0];for(const [fd,a,b] of D.flights)if(fd==ds)for(const A of [a,b]){x0=Math.min(x0,MX(A[1]));x1=Math.max(x1,MX(A[1]));y0=Math.min(y0,MY(A[0]));y1=Math.max(y1,MY(A[0]))}return x0<=x1?[x0,y0,x1,y1]:null}
function selectDay(di){
 O.day=di;drawCal();const r=D.days[di],cat=catOfDay(di),t=r[6]>=0?tripById[r[6]]:null;
 const b=bboxOfDay(di);if(b){const pw=(b[2]-b[0])*.15+3e-6,ph=(b[3]-b[1])*.15+3e-6;const S=Math.min((V.W-60)/(b[2]-b[0]+2*pw),(V.H-60)/(b[3]-b[1]+2*ph));flyTo((b[0]+b[2])/2,(b[1]+b[3])/2,Math.min(S,1.5e6))}
 openDetail(`<h3>${dfmt(r[0])}</h3><div class="dsub">${t?`<span class="pill" style="background:${tint(WCOL[cat],.2)}">${esc(cat)}</span>${esc(t.name)} · Tag ${Math.round((dateOf(r[0])-dateOf(t.a))/864e5)+1} von ${t.n+1}`:'Alltag'} · bis ${fmt(r[5])} km weg von zuhause</div>`+mbars({road:r[1],rail:r[2],foot:r[3],fly:r[4]},MCOL,MNAME)+((byDay[di]||[]).length||r[4]?'':'<div class="empty">Keine Bewegung aufgezeichnet.</div>')+`<div class="row" style="margin-top:10px"><button class="btn" id="dprev">← Vortag</button><button class="btn" id="dnext">Folgetag →</button></div>`,()=>{O.day=null;drawCal();full()});
 $('dprev').onclick=e=>{e.stopPropagation();if(di>0)selectDay(di-1)};$('dnext').onclick=e=>{e.stopPropagation();if(di<D.days.length-1)selectDay(di+1)};
 full();
}
function sideO(){
 const sd=D.days.filter((r,i)=>daySel(i)),tripDays=sd.filter(r=>r[6]>=0).length,big=sd.reduce((b,r)=>{const k=r[1]+r[2]+r[3]+r[4];return k>b?k:b},0);
 if(!$('o1'))$('o-stats').innerHTML=statHTML([['o1','Tage auf Reisen'],['o2','Tage nie weiter als 30 km'],['o3','Orte mit Aufenthalt'],['o4','km am längsten Tag']]);
 count('o1',tripDays);count('o2',sd.filter(r=>r[7]&&r[6]<0&&r[5]<30).length);count('o3',O.pl.length);count('o4',big);
 $('o-legend').innerHTML=[...WHO.filter(w=>w!='Alltag').map(w=>[w,WCOL[w]]),['Alltag wenig',MC.cal0],['Alltag viel',tint(MC.calHi,.72)],['keine Daten',MC.empty]].map(([n,c])=>`<span style="display:inline-flex;align-items:center;gap:6px"><i style="width:11px;height:11px;border-radius:2px;background:${c};box-shadow:inset 0 0 0 1px #E4DFF3"></i>${esc(n)}</span>`).join('');
 topO();
}
function topO(){const q=O.q.trim().toLowerCase();const list=O.pl.filter(p=>p[9]!='Zuhause'&&(!q||p[9].toLowerCase().includes(q))).slice(0,q?20:10);
 $('o-top').innerHTML=list.length?list.map((p,i)=>`<div class="trow" data-i="${i}"><span class="n">${i+1}</span><span class="nm">${esc(p[9])}</span><span class="d"><i style="background:${PCOL[p.cat]}"></i><em style="margin-left:6px">${fmt(p[2])} h</em></span></div>`).join(''):'<div class="empty">Kein Ort gefunden.</div>';
 $('o-top').querySelectorAll('.trow').forEach(r=>r.onclick=()=>{const p=list[+r.dataset.i];flyTo(MX(p[1]),MY(p[0]),Math.max(V.S,300000));placeDetail(p)})}
$('o-search').addEventListener('input',e=>{O.q=e.target.value;topO()});
function placeDetail(p){openDetail(`<h3>${esc(p[9])}</h3><div class="dsub"><span class="pill" style="background:${tint(PCOL[p.cat],.2)}">${p.cat}</span>${fmt(p[2])} Stunden · ${fmt(p[3])} Aufenthalte</div><div class="trip"><div class="s" style="background:${PCOL[p.cat]}"></div><div><div class="t1">Zum ersten Mal: ${dfmt(p[5])}</div><div class="t2">Zuletzt: ${dfmt(p[6])}${p[8]>=0&&tripById[p[8]]?' · Reise: '+esc(tripById[p[8]].name):''}</div></div></div>`)}
$('o-rand').onclick=()=>{const c=D.days.map((r,i)=>[r,i]).filter(([r,i])=>r[6]>=0&&(r[1]+r[2]+r[4])>40&&daySel(i));if(!c.length)return;const [r,i]=c[Math.floor(Math.random()*c.length)];selectDay(i)};
$('o-clear').onclick=()=>{O.day=null;closeDetail();drawCal();fit(HOME[0]-.35,HOME[1]-.7,HOME[0]+.3,HOME[1]+.5)};

/* ================= KARTE 4: REGIONEN (weltweit) ================= */
const RG={color:'y',hit:null,list:null,countries:{},groups:null,agg:null,cc:null};
const DCOL=['#EAE6F7','#CFC6F2','#AE9CEB','#8B70E0','#6A47D2','#4A28B8'];
function prepReg(meta,rows){RG.countries=meta.countries;RG.rows=rows;
 RG.list=meta.regions.map(([id,name,a3,la,lo,rings])=>{const p=new Path2D();let x0=1,y0=1,x1=0,y1=0;for(const r of rings){let x=0,y=0;for(let i=0;i<r.length;i+=2){x+=r[i];y+=r[i+1];const X=MX(x/1e3),Y=MY(y/1e3);if(X<x0)x0=X;if(X>x1)x1=X;if(Y<y0)y0=Y;if(Y>y1)y1=Y;i?p.lineTo(X,Y):p.moveTo(X,Y)}p.closePath()}return {id,name,a3,la,lo,p,bb:[x0,y0,x1,y1]}});
 RG.byId=new Map(RG.list.map(r=>[r.id,r]));
 const hx=MX(HOME[1]),hy=MY(HOME[0]);const h=RG.list.find(r=>hx>=r.bb[0]&&hx<=r.bb[2]&&hy>=r.bb[1]&&hy<=r.bb[3]&&ctx.isPointInPath(r.p,hx,hy,'evenodd'));RG.cc=h?h.a3:null}
function aggReg(){if(RG.agg)return RG.agg;const m=selMask(),grp=SEL&&isGroup(SEL),ms=members(SEL),A=new Map();
 const okDay=d=>{if(!grp)return true;const di=dayIdx(d);const t=dayTrip(di);return !!t&&t.w==SEL};
 for(const [rid,pi,first,days,stay] of RG.rows){if(SEL){if(pi<0||!(m&(1<<Math.min(pi,30))))continue;if(grp&&!ms.length)continue;if(grp&&!okDay(first))continue}
  const o=A.get(rid);if(!o)A.set(rid,{first,days,stay});else{if(first<o.first)o.first=first;o.days=Math.max(o.days,days);o.stay=o.stay||stay}}
 RG.agg=A;return A}
function regFill(r){const v=aggReg().get(r.id);if(!v)return null;if(RG.color=='y')return ycol(+v.first.slice(0,4));if(RG.color=='d'){const i=v.days>=200?5:v.days>=50?4:v.days>=15?3:v.days>=5?2:v.days>=2?1:0;return DCOL[i]}return v.stay?'#00BFB3':'#B3ECE8'}
function contentRG(){
 ctx.fillStyle=MC.land;ctx.fill(B.land);const S=V.S,A=aggReg(),G=ST('regions'),BM=G.borders||'visited';
 if(!RG.groups||RG.bm!==BM){RG.bm=BM;RG.groups=new Map();RG.lines=new Path2D();const cs=new Set([...A.keys()].map(id=>RG.byId.get(id)?.a3));if(RG.cc)cs.add(RG.cc);
  for(const r of RG.list){if(BM=='all'||(BM=='visited'&&cs.has(r.a3)))RG.lines.addPath(r.p);const c=regFill(r);if(!c)continue;let p=RG.groups.get(c);if(!p){p=new Path2D();RG.groups.set(c,p)}p.addPath(r.p)}}
 ctx.globalAlpha=G.fill_opacity??.8;for(const [c,p] of RG.groups){ctx.fillStyle=c;ctx.fill(p,'evenodd')}ctx.globalAlpha=1;
 ctx.fillStyle=MC.lake;ctx.fill(B.lakes);
 if(BM!='none'&&(G.border_width??1)>0){ctx.globalAlpha=G.border_opacity??.6;ctx.strokeStyle=G.border_color||MC.regLine;ctx.lineWidth=(G.border_width??1)*.8/S;ctx.stroke(RG.lines);ctx.globalAlpha=1}
 if((G.country_width??1.8)>0){ctx.strokeStyle=MC.regBorder;ctx.lineWidth=(G.country_width??1.8)*.72/S;ctx.stroke(B.borders)}}
function drawRG(){
 TKEY='G'+RG.color+'_'+SELV+'_'+STV;drawTiles(contentRG);worldT();const S=V.S;
 if(RG.hit){ctx.strokeStyle=MC.strong;ctx.lineWidth=3/S;ctx.stroke(RG.hit.p)}
 endWorld();placed.length=0;usedNames.clear();homeMark();
 if(S>2500&&ST('regions').names!==false){const A=aggReg();const vis=RG.list.filter(r=>A.has(r.id)).map(r=>[r,toS(MX(r.lo),MY(r.la))]).filter(([,[x,y]])=>x>0&&y>0&&x<V.W&&y<V.H).sort((a,b)=>A.get(b[0].id).days-A.get(a[0].id).days);for(const [r,[x,y]] of vis.slice(0,120))lbl(r.name.replace(/^(Kanton|Département|Gespanschaft|Provinz|Provincia|Region|Regierungsbezirk|Bezirk|Comté|County of) /,''),x,y,S>20000?12:11,650,MC.text,'center',3)}
}
function regAt(sx,sy){const [wx,wy]=toW(sx,sy);for(const r of RG.list){const b=r.bb;if(wx<b[0]||wx>b[2]||wy<b[1]||wy>b[3])continue;if(ctx.isPointInPath(r.p,wx,wy,'evenodd'))return r}return null}
function sideRG(){
 const A=aggReg(),vis=RG.list.filter(r=>A.has(r.id)),stay=vis.filter(r=>A.get(r.id).stay),cs=new Set(vis.map(r=>r.a3));
 const home=RG.cc?RG.list.filter(r=>r.a3==RG.cc):[],hv=home.filter(r=>A.has(r.id)).length;
 if(!$('g1'))$('g-stats').innerHTML=statHTML([['g1','Regionen besucht'],['g2','Länder'],['g3','mit Aufenthalt'],['g4','im Heimatland']]);
 count('g1',vis.length);count('g2',cs.size);count('g3',stay.length);$('g4').textContent=home.length?hv+' / '+home.length:'–';
 const ny={};vis.forEach(r=>{const y=+A.get(r.id).first.slice(0,4);ny[y]=(ny[y]||0)+1});const ys=DYEARS,mx=Math.max(1,...ys.map(y=>ny[y]||0));
 $('g-years').innerHTML=ys.map(y=>`<div class="yb" style="cursor:default"><span>${ny[y]||''}</span><div class="bar"><div style="height:${(ny[y]||0)/mx*76}px;background:${ycol(y)}"></div></div><span>${String(y).slice(2)}</span></div>`).join('');
 const by={};RG.list.forEach(r=>{if(!cs.has(r.a3))return;const k=by[r.a3]=by[r.a3]||{n:0,v:0};k.n++;if(A.has(r.id))k.v++});
 const rows=Object.entries(by).map(([k,o])=>[k,RG.countries[k]||k,o.v,o.n]).sort((a,b)=>(b[0]==RG.cc)-(a[0]==RG.cc)||b[2]-a[2]).slice(0,14);
 $('g-cant').innerHTML=rows.length?rows.map(([k,n,v,t])=>`<div class="mbar" data-a3="${esc(k)}"><span title="${esc(n)}">${esc(n)}</span><span class="tr"><div style="width:${v/t*100}%;background:#8B3DFF"></div></span><b>${v}/${t}</b></div>`).join(''):'<div class="empty">Noch keine Regionen – sobald GPS-Daten da sind, füllt sich die Karte.</div>';
 $('g-cant').querySelectorAll('.mbar').forEach(el=>el.onclick=()=>{const rs=RG.list.filter(r=>r.a3==el.dataset.a3);let b=null;for(const r of rs)b=ub(b,r.bb);if(b){const S=Math.min((V.W-80)/(b[2]-b[0]),(V.H-80)/(b[3]-b[1]));flyTo((b[0]+b[2])/2,(b[1]+b[3])/2,Math.min(S,200000))}});
 legendG();
}
function legendG(){const L=$('g-legend');if(RG.color=='y')L.innerHTML='<div class="row" style="gap:4px">'+YCOL.map(c=>`<span style="flex:1;height:10px;border-radius:3px;background:${c}"></span>`).join('')+'</div><div class="row" style="justify-content:space-between;font-size:12px;font-weight:600;color:#5B5479;margin-top:4px"><span>'+Y0+'</span><span>'+Y1+'</span></div>';else if(RG.color=='d')L.innerHTML='<div class="row" style="gap:4px">'+DCOL.map(c=>`<span style="flex:1;height:10px;border-radius:3px;background:${c}"></span>`).join('')+'</div><div class="row" style="justify-content:space-between;font-size:12px;font-weight:600;color:#5B5479;margin-top:4px"><span>1 Tag</span><span>200+ Tage</span></div>';else L.innerHTML='<div class="row" style="gap:12px;font-size:12px;font-weight:600"><span><i style="display:inline-block;width:11px;height:11px;border-radius:2px;background:#00BFB3"></i> übernachtet / länger dort</span><span><i style="display:inline-block;width:11px;height:11px;border-radius:2px;background:#B3ECE8"></i> durchgefahren</span></div>'}
segBind('g-color',v=>{RG.color=v;if(STYLE)STYLE.regions.fill_by={y:'first',d:'days',v:'stay'}[v]||'first';RG.groups=null;legendG();legend();full()});

/* ================= KARTE 5: ZEITRAFFER ================= */
const Z={t:0,play:false,speed:7,cam:'follow',trail:'all',last:0,cum:null,cl:new Map(),boxes:new Map(),drag:false};
const dayIdx=ds=>Math.round((dateOf(ds)-dateOf(D.days[0][0]))/864e5);
const PLAY='M2.5 1.5H5.5V12.5H2.5ZM8.5 1.5H11.5V12.5H8.5Z',PAUSE='M3 1.5L12 7L3 12.5Z';
function trackT(i){return D.trackT&&D.trackT[i]?D.trackT[i]:[0,1]}
function cumLen(i){let c=Z.cl.get(i);if(c)return c;const a=TR[i].p;c=new Float64Array(a.length/2);for(let j=1;j<c.length;j++)c[j]=c[j-1]+Math.hypot(a[j*2]-a[j*2-2],a[j*2+1]-a[j*2-1]);Z.cl.set(i,c);if(Z.cl.size>4000)Z.cl.clear();return c}
function partial(i,p){/* draws track i up to share p, returns the head point */const a=TR[i].p,c=cumLen(i),L=c[c.length-1]*p;ctx.moveTo(a[0],a[1]);let j=1;for(;j<c.length&&c[j]<=L;j++)ctx.lineTo(a[j*2],a[j*2+1]);if(j>=c.length)return [a[a.length-2],a[a.length-1]];const f=(L-c[j-1])/Math.max(1e-12,c[j]-c[j-1]);const x=a[j*2-2]+(a[j*2]-a[j*2-2])*f,y=a[j*2-1]+(a[j*2+1]-a[j*2-1])*f;ctx.lineTo(x,y);return [x,y]}
function ptAt(i,p){const a=TR[i].p,c=cumLen(i),L=c[c.length-1]*p;let j=1;while(j<c.length&&c[j]<L)j++;if(j>=c.length)return [a[a.length-2],a[a.length-1]];const f=(L-c[j-1])/Math.max(1e-12,c[j]-c[j-1]);return [a[j*2-2]+(a[j*2]-a[j*2-2])*f,a[j*2-1]+(a[j*2+1]-a[j*2-1])*f]}
function bez(a,t){const u=1-t;return [u*u*a[0]+2*u*t*a[2]+t*t*a[4],u*u*a[1]+2*u*t*a[3]+t*t*a[5]]}
function groundBox(d){let x0=1,y0=1,x1=0,y1=0;for(const i of byDay[d]||[]){const b=TR[i].bb;x0=Math.min(x0,b[0]);y0=Math.min(y0,b[1]);x1=Math.max(x1,b[2]);y1=Math.max(y1,b[3])}return x0<=x1?[x0,y0,x1,y1]:null}
const ub=(a,b)=>!a?b:!b?a:[Math.min(a[0],b[0]),Math.min(a[1],b[1]),Math.max(a[2],b[2]),Math.max(a[3],b[3])];
function boxScale(b,pad=.62){const w=Math.max(b[2]-b[0],1e-6),h=Math.max(b[3]-b[1],1e-6);return Math.min(260000,Math.max(1800,Math.min(V.W*pad/w,V.H*pad/h)))}
/* ================= KARTE 5: REISEFILM =================
   Scenes: intro → (year chapter) → trip → trip … → end. Each trip: the camera flies there, the route draws itself
   with its vehicle, a title card shows who/where/when, then it stays on the map. Everything is a function of the
   film time F.t, so the slider can jump anywhere. */
const F={t:0,play:false,last:0,sc:null,dur:0,st:null,done:-1,doneIds:new Set(),rec:null,chunks:[]};
const FC=()=>ST('timelapse');
const ICO={fly:'✈️',rail:'🚆',road:'🚗',ferry:'⛴️',foot:'🚶'};
function plen(pts){let L=0;for(let i=1;i<pts.length;i++)L+=Math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]);return L}
function tripPath(t){if(t._fp&&t._fpv===STV)return t._fp;const out=[];
 const arc=(A,Bp)=>{const a=arcPts(MX(A[1]),MY(A[0]),MX(Bp[1]),MY(Bp[0]),.2*(ST('trips').arc_height??1));return {k:'arc',m:'fly',a,L:Math.hypot(a[4]-a[0],a[5]-a[1])*1.15}};
 const poly=(pts,m)=>({k:'poly',m,pts,L:plen(pts)});
 if(t.lg){for(const it of t.lg){if(it[0]=='fly'){const c=it[1];out.push(arc([c[0],c[1]],[c[2],c[3]]))}else for(const r of it[1]){const pts=[];for(let i=0;i+1<r[1].length;i+=2)pts.push([MX(r[1][i+1]),MY(r[1][i])]);out.push(poly(pts,r[0]?'ferry':(r[2]||'road')))}}}
 else if(t.gr){for(const r of estRoute(t)||[])out.push(poly(r.pts,r.sea?'ferry':(r.m||t.m.find(x=>x=='rail'||x=='road')||'road')))}
 else{const items=[],d0=dayIdx(t.a),d1=dayIdx(t.b);
  if(TR)for(let d=d0;d<=d1;d++)for(const i of byDay[d]||[]){const a=TR[i].p;if(a.length<4)continue;const pts=[];for(let j=0;j<a.length;j+=2)pts.push([a[j],a[j+1]]);items.push({tk:d+trackT(i)[0],...poly(pts,TCLS[TR[i].c])})}
  for(const f of D.flights||[]){if(f[0]<t.a||f[0]>t.b||!flightSel(f))continue;items.push({tk:dayIdx(f[0])+(f[3]??.4),...arc(f[1],f[2])})}
  items.sort((p,q)=>p.tk-q.tk);out.push(...items);
  if(!items.length&&t.fl&&t.fl.length)out.push(arc(t.fl[0][0],t.fl[0][1]))}
 let L=0;for(const p of out){p.c0=L;L+=p.L}
 let bb=[MX(HOME[1]),MY(HOME[0]),MX(HOME[1]),MY(HOME[0])];bb=ub(bb,[MX(t.p[1]),MY(t.p[0]),MX(t.p[1]),MY(t.p[0])]);
 for(const p of out){if(p.k=='arc')bb=ub(bb,[Math.min(p.a[0],p.a[4]),Math.min(p.a[1],p.a[3],p.a[5]),Math.max(p.a[0],p.a[4]),Math.max(p.a[1],p.a[5])]);else for(const [x,y] of p.pts)bb=ub(bb,[x,y,x,y])}
 t._fp={pieces:out,L,bb};t._fpv=STV;return t._fp}
function viewOf(b){const pad=.66,w=Math.max(b[2]-b[0],2e-4),h=Math.max(b[3]-b[1],2e-4);return {cx:(b[0]+b[2])/2,cy:(b[1]+b[3])/2,S:Math.min(240000,Math.max(1200,Math.min(V.W*pad/w,(V.H-90)*pad/h)))}}
function buildF(){const C=FC(),sp=Math.max(.25,C.speed||1),min=C.min_km||0;
 const trips=D.trips.filter(t=>tripSel(t)&&!t.nopos&&km2(HOME[0],HOME[1],t.p[0],t.p[1])>=min).sort((a,b)=>a.a<b.a?-1:a.a>b.a?1:0);
 let all=null;for(const t of trips)all=ub(all,tripPath(t).bb);if(!all){const x=MX(HOME[1]),y=MY(HOME[0]);all=[x-.002,y-.002,x+.002,y+.002]}
 const hx=MX(HOME[1]),hy=MY(HOME[0]),homeB=[hx-.0012,hy-.0012,hx+.0012,hy+.0012];
 const sc=[];let T=0,y=null;const add=o=>{o.t0=T;sc.push(o);T+=o.d};
 add({k:'intro',d:2.6/sp,box:all,from:homeB});
 for(const t of trips){if(C.chapters!==false&&t.y!==y){y=t.y;let b=null;for(const q of trips)if(q.y==y)b=ub(b,tripPath(q).bb);add({k:'year',y,d:2.4/sp,box:b})}
  const P=tripPath(t),km=km2(HOME[0],HOME[1],t.p[0],t.p[1]);const fly=1.25/sp,route=Math.min(5.5,1.8+Math.log2(1+km/150)*.55)/sp,stay=(.35+1.3*(C.pause??1))/sp;
  add({k:'trip',t,d:fly+route+stay,fly,route,box:P.bb})}
 add({k:'end',d:3.2/sp,box:all});
 /* counters at the start of each scene */
 let km=0,n=0;const cs=new Set();for(const o of sc){o.km=km;o.n=n;o.cn=cs.size;if(o.k=='trip'){km+=o.t.km||0;n++;if(o.t.c)cs.add(o.t.c)}}
 F.sc=sc;F.dur=T;F.trips=trips;F.tot={km,n,cn:cs.size};F.st=null;F.done=-1;F.t=Math.min(F.t,T);sideF()}
function sceneAt(T){const sc=F.sc;let lo=0,hi=sc.length-1;while(lo<hi){const m=(lo+hi+1)>>1;if(sc[m].t0<=T)lo=m;else hi=m-1}return lo}
const ease=u=>u<.5?4*u*u*u:1-Math.pow(-2*u+2,3)/2;
function camF(T){const i=sceneAt(T),o=F.sc[i],prev=i?F.sc[i-1]:null;const to=viewOf(o.box),from=viewOf(o.from||(prev?prev.box:o.box));
 const fd=o.k=='trip'?o.fly:o.d*.55;const u=ease(Math.max(0,Math.min(1,(T-o.t0)/fd)));
 /* far jumps zoom out on the way (like a plane), short ones glide */
 const mid=viewOf(ub(o.box,o.from||(prev?prev.box:o.box)));const l0=Math.log(from.S),l1=Math.log(to.S),lm=Math.min(l0,l1,Math.log(mid.S*.92));
 const lS=(1-u)*(1-u)*l0+2*u*(1-u)*lm+u*u*l1;return {cx:from.cx+(to.cx-from.cx)*u,cy:from.cy+(to.cy-from.cy)*u,S:Math.exp(lS)}}
function drawPiece(p,upto,lw){/* draws piece p up to length upto (world units); returns [x,y,angle] of the head */
 if(p.k=='arc'){const f=Math.max(0,Math.min(1,upto/p.L)),N=Math.max(2,Math.ceil(48*f));ctx.beginPath();ctx.moveTo(p.a[0],p.a[1]);let q=[p.a[0],p.a[1]];for(let k=1;k<=N;k++){q=bez(p.a,f*k/N);ctx.lineTo(q[0],q[1])}ctx.stroke();const q2=bez(p.a,Math.max(0,f-.01));return [q[0],q[1],Math.atan2(q[1]-q2[1],q[0]-q2[0])]}
 const P=p.pts;ctx.beginPath();ctx.moveTo(P[0][0],P[0][1]);let L=0,hx=P[0][0],hy=P[0][1],ang=0;
 for(let i=1;i<P.length;i++){const l=Math.hypot(P[i][0]-P[i-1][0],P[i][1]-P[i-1][1]);if(L+l>=upto){const f=(upto-L)/Math.max(1e-12,l);hx=P[i-1][0]+(P[i][0]-P[i-1][0])*f;hy=P[i-1][1]+(P[i][1]-P[i-1][1])*f;ang=Math.atan2(P[i][1]-P[i-1][1],P[i][0]-P[i-1][0]);ctx.lineTo(hx,hy);ctx.stroke();return [hx,hy,ang]}L+=l;ctx.lineTo(P[i][0],P[i][1]);hx=P[i][0];hy=P[i][1];if(l>0)ang=Math.atan2(P[i][1]-P[i-1][1],P[i][0]-P[i-1][0])}
 ctx.stroke();return [hx,hy,ang]}
function styleFor(m,col,S,lw){ctx.strokeStyle=col;ctx.lineWidth=lw*SM(m).width;ctx.setLineDash(m=='ferry'?[.01/S,5/S]:m=='fly'?[8/S,6/S]:dashFor(SM(m).dash,S))}
function drawF(){const C=FC();const M0=MC;if(C.cinema!==false)MC=THEMES.dark;try{drawF0(C)}finally{MC=M0}}
function drawF0(C){
 if(!F.sc)buildF();const T=F.t,i=sceneAt(T),o=F.sc[i];
 const v=camF(T);V.cx=v.cx;V.cy=v.cy;V.S=v.S;
 /* trips already shown: drawn into the cached map tiles */
 let done=0;for(const q of F.sc){if(q.k=='trip'&&q.t0+q.d<=T)done++}
 if(done!==F.done){F.done=done;F.doneIds=new Set(F.trips.slice(0,done).map(t=>t.id));F.st={}}
 TKEY='F'+done+'_'+SELV+'_'+STV+(C.cinema!==false?'c':'');
 drawTiles(bb=>{drawBase();const S=V.S;ctx.lineJoin='round';ctx.lineCap='round';ctx.globalAlpha=.6;ctx.lineWidth=Math.max(1,Math.min(2,S/30000))/S;
  if(TR&&done)tileDraw(F.st,li=>{const t=dayTrip(TR[li].d);return t&&F.doneIds.has(t.id)?WCOL[t.w]||'#8B3DFF':null},()=>0,k=>{ctx.strokeStyle=k},bb);ctx.globalAlpha=1});
 worldT();const S=V.S,lw=Math.max(1.6,Math.min(3,S/20000))/S;ctx.lineJoin='round';ctx.lineCap='round';
 /* earlier flights and estimated ways stay as soft lines */
 ctx.globalAlpha=.45;for(const t of F.trips.slice(0,done))for(const p of tripPath(t).pieces){if(p.k=='arc'||t.gr){styleFor(p.m,WCOL[t.w]||MCOL[p.m],S,lw*.8);drawPiece(p,p.L,lw)}}ctx.globalAlpha=1;ctx.setLineDash([]);
 let head=null,hm='road',hc=MCOL.road;
 if(o.k=='trip'){const t=o.t,P=tripPath(t),col=WCOL[t.w]||'#8B3DFF';const pr=Math.max(0,Math.min(1,(T-o.t0-o.fly)/o.route)),upto=pr*P.L;
  if(C.glow!==false&&C.cinema!==false)ctx.globalCompositeOperation='lighter';
  for(const p of P.pieces){if(p.c0>upto)break;const u=Math.min(p.L,upto-p.c0);
   ctx.globalAlpha=.35;styleFor(p.m,col,S,lw*3.2);ctx.setLineDash([]);drawPiece(p,u,lw);ctx.globalAlpha=1;
   styleFor(p.m,p.m=='fly'?MCOL.fly:MCOL[p.m]||col,S,lw*1.25);const h=drawPiece(p,u,lw);if(pr<1||p===P.pieces[P.pieces.length-1]){head=h;hm=p.m;hc=MCOL[p.m]||col}}
  ctx.globalCompositeOperation='source-over';ctx.setLineDash([]);
  if(pr>=1)head=[MX(t.p[1]),MY(t.p[0]),0,1]}
 endWorld();placed.length=0;usedNames.clear();homeMark();drawPlaceLabels('few');
 const sz=1.45;
 if(head){const [x,y]=toS(head[0],head[1]);if(head[3]){const pulse=RED?0:(performance.now()/900)%1;ctx.beginPath();ctx.arc(x,y,8+pulse*18,0,7);ctx.fillStyle=WCOL[o.t.w]||hc;ctx.globalAlpha=.4*(1-pulse);ctx.fill();ctx.globalAlpha=1;ctx.beginPath();ctx.arc(x,y,6.5,0,7);ctx.fillStyle=WCOL[o.t.w]||hc;ctx.fill();ctx.lineWidth=2.5;ctx.strokeStyle=MC.ring;ctx.stroke()}
  else (hm=='fly'?drawPlane:hm=='rail'?drawTrain:hm=='ferry'?drawShip:hm=='foot'?(g,x,y,a,c,s)=>{g.beginPath();g.arc(x,y,5*s,0,7);g.fillStyle=c;g.fill()}:drawCar)(ctx,x,y,head[2],hc,sz)}
 overlayF(C,o,T)}
/* cards and counters are painted into the picture, so a recorded video has them too */
function rrect(x,y,w,h,r){ctx.beginPath();ctx.roundRect(x,y,w,h,r)}
function overlayF(C,o,T){const W=V.W,H=V.H,ph=(T-o.t0)/o.d,fade=Math.min(1,(T-o.t0)/.35,(o.t0+o.d-T)/.35);ctx.save();ctx.textBaseline='alphabetic';
 const dark=C.cinema!==false,bg=dark?'rgba(14,15,34,.86)':'rgba(255,255,255,.92)',fg=dark?'#F4F2FF':'#17122E',mu=dark?'#B8B3DA':'#5B5479';
 if(o.k=='year'||o.k=='intro'||o.k=='end'){const a=Math.max(0,Math.min(1,fade));ctx.globalAlpha=a;const big=o.k=='year'?String(o.y):o.k=='intro'?'Eure Reisen':'Das waren '+fmt(F.tot.n)+' Reisen';
  const sub=o.k=='year'?(()=>{const ts=F.trips.filter(t=>t.y==o.y);return ts.length+(ts.length==1?' Reise':' Reisen')+' · '+fmt(ts.reduce((s,t)=>s+(t.km||0),0))+' km · '+new Set(ts.map(t=>t.c).filter(Boolean)).size+' Länder'})():o.k=='intro'?(F.trips.length?F.trips[0].a.slice(0,4)+' – '+F.trips[F.trips.length-1].a.slice(0,4):''):fmt(F.tot.km)+' km · '+F.tot.cn+' Länder';
  ctx.font=`900 ${o.k=='year'?Math.min(120,W/5):Math.min(64,W/10)}px Inter,system-ui,sans-serif`;const tw=ctx.measureText(big).width;ctx.font='700 17px Inter,system-ui,sans-serif';const sw=ctx.measureText(sub).width;const bw=Math.max(tw,sw)+64,bh=(o.k=='year'?Math.min(120,W/5):Math.min(64,W/10))+70;
  ctx.fillStyle=bg;rrect((W-bw)/2,H/2-bh/2-10,bw,bh,24);ctx.fill();ctx.fillStyle=fg;ctx.textAlign='center';ctx.font=`900 ${o.k=='year'?Math.min(120,W/5):Math.min(64,W/10)}px Inter,system-ui,sans-serif`;ctx.fillText(big,W/2,H/2+(o.k=='year'?Math.min(120,W/5):Math.min(64,W/10))*.3-14);ctx.font='700 17px Inter,system-ui,sans-serif';ctx.fillStyle=mu;ctx.fillText(sub,W/2,H/2+bh/2-26);ctx.globalAlpha=1}
 if(o.k=='trip'&&C.cards!==false){const t=o.t,G=t.g&&D.groups.find(g=>g[0]==t.g),name=(t.name||(G&&G[1])||'Reise');const a=Math.max(0,Math.min(1,(T-o.t0-o.fly*.5)/.4,(o.t0+o.d-T)/.3));ctx.globalAlpha=a;
  const l1=t.w,l3=(tWhen(t)||dfmt(t.a)+(t.n?' – '+dfmt(t.b):''))+' · '+t.m.map(m=>ICO[m]||'').join(' ')+(t.km?' · '+fmt(t.km)+' km':'');ctx.font='850 26px Inter,system-ui,sans-serif';const w1=ctx.measureText(name).width;ctx.font='600 14px Inter,system-ui,sans-serif';const w3=ctx.measureText(l3).width;
  const bw=Math.min(W-28,Math.max(w1,w3)+40),bx=(W-bw)/2,by=H-(W<600?124:136);ctx.fillStyle=bg;rrect(bx,by,bw,104,18);ctx.fill();
  ctx.fillStyle=WCOL[t.w]||'#8B3DFF';ctx.beginPath();ctx.arc(bx+24,by+27,6,0,7);ctx.fill();ctx.font='800 13px Inter,system-ui,sans-serif';ctx.fillStyle=mu;ctx.textAlign='left';ctx.fillText(l1.toUpperCase(),bx+38,by+32);
  ctx.font='850 26px Inter,system-ui,sans-serif';ctx.fillStyle=fg;ctx.fillText(name,bx+18,by+64,bw-36);ctx.font='600 14px Inter,system-ui,sans-serif';ctx.fillStyle=mu;ctx.fillText(l3,bx+18,by+88,bw-36);ctx.globalAlpha=1}
 if(C.counters!==false&&o.k!='intro'){const pr=o.k=='trip'?Math.max(0,Math.min(1,(T-o.t0-o.fly)/o.route)):o.k=='end'?1:0;const km=o.km+(o.k=='trip'?(o.t.km||0)*pr:0),n=o.n+(o.k=='trip'&&pr>=1?1:0),cn=o.cn+(o.k=='trip'&&pr>=1&&o.t.c&&!F.trips.slice(0,o.n).some(q=>q.c==o.t.c)?1:0);
  const items=[[fmt(km),'km'],[fmt(n),n==1?'Reise':'Reisen'],[fmt(cn),cn==1?'Land':'Länder']];ctx.font='850 20px Inter,system-ui,sans-serif';let x=16;const y=16;ctx.fillStyle=bg;rrect(x-2,y-2,W<600?250:300,56,14);ctx.fill();
  for(const [v,l] of items){ctx.textAlign='left';ctx.font='850 20px Inter,system-ui,sans-serif';ctx.fillStyle=fg;ctx.fillText(v,x+12,y+26);const w=ctx.measureText(v).width;ctx.font='700 11px Inter,system-ui,sans-serif';ctx.fillStyle=mu;ctx.fillText(l.toUpperCase(),x+12,y+43);x+=Math.max(w,ctx.measureText(l.toUpperCase()).width)+26}}
 if(F.rec){ctx.fillStyle='#FF3B4E';ctx.beginPath();ctx.arc(W-24,H-24,7,0,7);ctx.fill()}
 ctx.restore()}
function sideF(){if(!F.sc)return;const mm=s=>Math.floor(s/60)+':'+String(Math.round(s%60)).padStart(2,'0');
 $('f-stats').innerHTML=statHTML([['f1','Reisen im Film'],['f2','km'],['f3','Länder'],['f4','Filmlänge']]);$('f1').textContent=fmt(F.tot.n);$('f2').textContent=fmt(F.tot.km);$('f3').textContent=fmt(F.tot.cn);$('f4').textContent=mm(F.dur);
 const ys=F.sc.filter(o=>o.k=='year');$('f-years').innerHTML=ys.map(o=>`<button class="chip on" style="--c:${ycol(o.y)}" data-t="${o.t0}"><i></i>${o.y}</button>`).join('')||'<div class="empty">Keine Reisen in dieser Auswahl.</div>';
 $('f-years').querySelectorAll('button').forEach(b=>b.onclick=()=>{F.t=+b.dataset.t+.01;infoF();DRAW()});infoF()}
function infoF(){if(!F.sc)return;const o=F.sc[sceneAt(F.t)];$('f-slider').value=Math.round(F.t/Math.max(.001,F.dur)*1000);
 $('f-now').textContent=o.k=='trip'?o.t.name:o.k=='year'?String(o.y):o.k=='intro'?'Anfang':'Ende';$('f-what').textContent=o.k=='trip'?`${o.t.w} · ${tWhen(o.t)||dfmt(o.t.a)}`:o.k=='year'?'Kapitel':F.play?'läuft':'bereit'}
function setPlayF(p){F.play=p;$('f-pico').setAttribute('d',p?PLAY:PAUSE);$('f-play').setAttribute('aria-label',p?'Pause':'Abspielen');if(p){F.last=0;requestAnimationFrame(tickF)}else{full();infoF()}}
function tickF(ts){if(!F.play||TAB!='zeit')return;const dt=Math.min(.1,(ts-(F.last||ts))/1000);F.last=ts;F.t=Math.min(F.dur,F.t+dt);DRAW();infoF();if(F.t>=F.dur){setPlayF(false);if(F.rec)F.rec.stop()}else requestAnimationFrame(tickF)}
$('f-play').onclick=()=>{if(!F.sc)buildF();if(!F.play&&F.t>=F.dur)F.t=0;setPlayF(!F.play)};
$('f-slider').addEventListener('input',e=>{if(!F.sc)return;F.t=+e.target.value/1000*F.dur;infoF();if(!F.q)F.q=requestAnimationFrame(()=>{F.q=0;DRAW()})});
$('f-style').onclick=()=>openStyle();
$('f-rec').onclick=()=>{const msg=$('f-recmsg');if(F.rec){F.rec.stop();return}
 if(!window.MediaRecorder||!cv.captureStream){msg.textContent='Dieser Browser kann keine Videos aufnehmen – versuche Chrome oder Edge.';return}
 const type=['video/webm;codecs=vp9','video/webm;codecs=vp8','video/webm','video/mp4'].find(t=>MediaRecorder.isTypeSupported(t));if(!type){msg.textContent='Kein Videoformat verfügbar.';return}
 F.chunks=[];const rec=new MediaRecorder(cv.captureStream(30),{mimeType:type,videoBitsPerSecond:8e6});F.rec=rec;
 rec.ondataavailable=e=>{if(e.data&&e.data.size)F.chunks.push(e.data)};
 rec.onstop=()=>{F.rec=null;$('f-rec').textContent='🎥 Als Video speichern';const blob=new Blob(F.chunks,{type:type.split(';')[0]});const url=URL.createObjectURL(blob);const a=$('f-dl');a.href=url;a.download='reisefilm.'+(type.includes('mp4')?'mp4':'webm');a.hidden=false;msg.textContent='Fertig – '+Math.round(blob.size/1e6)+' MB.';setPlayF(false)};
 rec.start(500);$('f-rec').textContent='⏹ Aufnahme stoppen';$('f-dl').hidden=true;msg.textContent='Aufnahme läuft … der Film spielt einmal ganz durch.';F.t=0;setPlayF(true)};
document.addEventListener('keydown',e=>{if(TAB!='zeit'||e.target.closest('input,select,textarea'))return;if(e.code=='Space'){e.preventDefault();$('f-play').click()}
 else if(e.key=='ArrowRight'||e.key=='ArrowLeft'){if(!F.sc)return;const i=sceneAt(F.t)+(e.key=='ArrowRight'?1:-1);F.t=F.sc[Math.max(0,Math.min(F.sc.length-1,i))].t0+.01;infoF();DRAW()}});


/* ================= Animierte Ebene: Flugzeuge, Züge, Autos ================= */
const cva=$('cva'),actx=cva.getContext('2d');
const AN={on:false,raf:0,arcs:[],cars:[],hidden:false};
function animWanted(){const a=STYLE?STYLE.anim:{on:true};let on=a.on;try{const v=localStorage.getItem('wm-anim');if(v!=null)on=v=='1'}catch(e){}return on}
function animOn(){return animWanted()&&!RED&&(TAB=='reisen'||TAB=='spuren')}
function sizeA(){cva.width=cv.width;cva.height=cv.height;cva.style.width=V.W+'px';cva.style.height=V.H+'px'}
function polyOf(li){const a=TR[li].l1;const n=a.length/2;const cum=new Float64Array(n);for(let j=1;j<n;j++)cum[j]=cum[j-1]+Math.hypot(a[j*2]-a[j*2-2],a[j*2+1]-a[j*2-1]);return {a,cum,len:cum[n-1],bb:TR[li].bb}}
/* km between two world points */
function wkm(x1,y1,x2,y2){return km2(IY(y1),IX(x1),IY(y2),IX(x2))}
function polyFrom(pts){const a=new Float64Array(pts.length*2);let x0=1,y0=1,x1=0,y1=0;pts.forEach(([x,y],i)=>{a[i*2]=x;a[i*2+1]=y;x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y)});const n=pts.length,cum=new Float64Array(n);for(let j=1;j<n;j++)cum[j]=cum[j-1]+Math.hypot(a[j*2]-a[j*2-2],a[j*2+1]-a[j*2-1]);return {a,cum,len:cum[n-1],bb:[x0,y0,x1,y1]}}
function animBuild(){
 AN.arcs=[];AN.cars=[];const A=ST('anim');let seed=1;const rnd=()=>{seed=(seed*16807)%2147483647;return seed/2147483647};
 const minP=A.min_km_plane??0,minT=A.min_km_train??0,minC=A.min_km_car??150,minF=A.min_km_ferry??0,MAX=A.max_count??60;
 const okV=(m,km)=>m=='rail'?A.trains!==false&&km>=minT:m=='ferry'?A.ferries!==false&&km>=minF:A.cars!==false&&km>=minC;
 const arcs=[],veh=[];
 if(TAB=='reisen'&&RC){const AH=ST('trips').arc_height??1;
  if(A.planes!==false)for(const e of RC.pairs){const [a1,b1]=e.k.split('>');const [x1,y1]=gpos(a1),[x2,y2]=gpos(b1);const km=wkm(x1,y1,x2,y2);if(km<minP)continue;arcs.push({km,sp:e.sp,a:arcPts(x1,y1,x2,y2,(e.sp?.07:a1=='home'?.2:.18)*AH),cols:R.color=='w'?WHO.filter(w=>e.ws.has(w)).map(w=>WCOL[w]):[MCOL.fly],ph:rnd()*2})}
  if(TR){const hc=(D.region&&D.region.name)||'';
   for(const t of RC.on){if(!t.g||t.gr||!t.m.some(m=>m=='road'||m=='rail'))continue;if(hc&&t.c&&t.c==hc)continue;const km=km2(HOME[0],HOME[1],t.p[0],t.p[1]);
    let best=null,bl=0;for(let d=dayIdx(t.a);d<=dayIdx(t.b);d++)for(const li of byDay[d]||[]){const m=TCLS[TR[li].c];if(m!='road'&&m!='rail')continue;if(!R.m.has(m)||!okV(m,km))continue;const b=TR[li].bb;const l=Math.hypot(b[2]-b[0],b[3]-b[1]);if(l>bl){bl=l;best=li}}
    if(best!=null&&bl>1e-3){const m=TCLS[TR[best].c];veh.push({km,...polyOf(best),m,col:R.color=='w'?WCOL[t.w]:MCOL[m],ph:rnd()*2})}}}
  if(ST('est').show!==false)for(const g of RC.gr){const km=km2(HOME[0],HOME[1],g.t.p[0],g.t.p[1]);const rs=estRoute(g.t)||[];
   const land=rs.filter(r=>!r.sea);if(land.length&&okV(g.m,km)){const L=rs.filter(r=>!r.sea).sort((p,q)=>q.pts.length-p.pts.length)[0];if(L)veh.push({km,...polyFrom(L.pts),m:g.m,col:g.col,ph:rnd()*2})}
   if(ST('est').ferry!==false)for(const r of rs)if(r.sea&&okV('ferry',km))veh.push({km,...polyFrom(r.pts),m:'ferry',col:MCOL.ferry,ph:rnd()*2})}}
 else if(TAB=='spuren'&&SP.fl&&A.planes!==false){const seen=new Set();for(const [a,c] of SP.fl){const k=Math.round(a[0]*2e3)+','+Math.round(a[1]*2e3)+','+Math.round(a[4]*2e3)+','+Math.round(a[5]*2e3)+c;if(seen.has(k))continue;seen.add(k);const km=wkm(a[0],a[1],a[4],a[5]);if(km<minP)continue;arcs.push({km,a,cols:[c],ph:rnd()*2})}}
 /* at most MAX at the same time: the longest ones first, planes and ground vehicles share the room */
 arcs.sort((p,q)=>q.km-p.km);veh.sort((p,q)=>q.km-p.km);const nv=Math.min(veh.length,Math.max(Math.ceil(MAX*.4),MAX-arcs.length));AN.cars=veh.slice(0,nv);AN.arcs=arcs.slice(0,Math.max(0,MAX-AN.cars.length));
}
function animRestart(){const on=animOn();AN.on=on;if(on){animBuild();sizeA();cva.hidden=false;if(!AN.raf)AN.raf=requestAnimationFrame(animFrame)}else{cva.hidden=true;if(AN.raf){cancelAnimationFrame(AN.raf);AN.raf=0}}}
document.addEventListener('visibilitychange',()=>{if(!document.hidden&&AN.on&&!AN.raf)AN.raf=requestAnimationFrame(animFrame)});
const pingpong=p=>{const q=p%2;const u=q<1?q:2-q;return u<.5?2*u*u:1-Math.pow(-2*u+2,2)/2};
function dashArr(m){const d=SM(m).dash;return d=='dashed'?[8,6]:d=='dotted'?[.1,5]:d=='longdash'?[16,7]:d=='dashdot'?[10,4,.1,4]:d=='sparse'?[.1,10]:[]}
/* seaplane: the plane with two floats underneath */
function drawSeaplane(g,x,y,ang,col,s){g.save();g.translate(x,y);g.rotate(ang);g.scale(s,s);g.lineCap='round';for(const [w,c] of [[3.6,MC.ring],[1.8,col]]){g.strokeStyle=c;g.lineWidth=w;g.beginPath();g.moveTo(-4,-3);g.lineTo(5,-3);g.moveTo(-4,3);g.lineTo(5,3);g.stroke()}g.restore();drawPlane(g,x,y,ang,col,s*.85)}
function drawPlane(g,x,y,ang,col,s){g.save();g.translate(x,y);g.rotate(ang);g.scale(s,s);g.fillStyle=col;g.strokeStyle=MC.ring;g.lineWidth=1.6;g.lineJoin='round';g.beginPath();g.moveTo(9,0);g.lineTo(2,-1.6);g.lineTo(-2,-7.5);g.lineTo(-4,-7.5);g.lineTo(-1.6,-1.6);g.lineTo(-6,-1.4);g.lineTo(-8,-4);g.lineTo(-9,-4);g.lineTo(-8,0);g.lineTo(-9,4);g.lineTo(-8,4);g.lineTo(-6,1.4);g.lineTo(-1.6,1.6);g.lineTo(-4,7.5);g.lineTo(-2,7.5);g.lineTo(2,1.6);g.closePath();g.stroke();g.fill();g.restore()}
function drawCar(g,x,y,ang,col,s){g.save();g.translate(x,y);const flip=Math.abs(ang)>Math.PI/2;g.rotate(flip?ang+Math.PI:ang);g.scale(flip?-s:s,s);g.fillStyle=col;g.strokeStyle=MC.ring;g.lineWidth=1.5;g.beginPath();g.roundRect(-7,-3.2,14,5.2,2.2);g.moveTo(-3.6,-3.2);g.lineTo(-1.8,-6.4);g.lineTo(3.4,-6.4);g.lineTo(5,-3.2);g.closePath();g.stroke();g.fill();g.fillStyle=MC.ring;g.fillRect(-1.2,-5.6,1.6,2.1);g.fillRect(1.2,-5.6,1.8,2.1);g.fillStyle=MC.strong;for(const wx of [-4,4]){g.beginPath();g.arc(wx,2.2,1.9,0,7);g.fill()}g.restore()}
function drawTrain(g,x,y,ang,col,s){g.save();g.translate(x,y);const flip=Math.abs(ang)>Math.PI/2;g.rotate(flip?ang+Math.PI:ang);g.scale(flip?-s:s,s);g.fillStyle=col;g.strokeStyle=MC.ring;g.lineWidth=1.5;g.beginPath();g.moveTo(-10,-4.5);g.lineTo(6,-4.5);g.quadraticCurveTo(10.5,-4.5,10.5,1.5);g.lineTo(10.5,3);g.lineTo(-10,3);g.closePath();g.stroke();g.fill();g.fillStyle=MC.ring;for(const wx of [-8,-4,0])g.fillRect(wx,-3,2.6,2.2);g.beginPath();g.moveTo(5,-3);g.lineTo(8,-3);g.lineTo(9.3,-.8);g.lineTo(5,-.8);g.fill();g.restore()}
function drawShip(g,x,y,ang,col,s){g.save();g.translate(x,y);const flip=Math.abs(ang)>Math.PI/2;g.rotate(flip?ang+Math.PI:ang);g.scale(flip?-s:s,s);g.fillStyle=col;g.strokeStyle=MC.ring;g.lineWidth=1.5;g.lineJoin='round';g.beginPath();g.moveTo(-10,-1);g.lineTo(10,-1);g.lineTo(7,4);g.lineTo(-8,4);g.closePath();g.stroke();g.fill();g.beginPath();g.roundRect(-5,-5.5,9,4.5,1.2);g.stroke();g.fill();g.fillStyle=MC.ring;g.fillRect(-3.5,-4.4,1.6,1.8);g.fillRect(-.6,-4.4,1.6,1.8);g.fillStyle=col;g.fillRect(2.2,-8.5,2.2,3.2);g.restore()}
function animFrame(ts){
 AN.raf=0;if(!AN.on||document.hidden)return;
 const A=ST('anim'),t=ts/1000*(A.speed||1),tp=ts/1000,sz=(A.size||1)*1.25*(V.W<600?.9:1);
 actx.setTransform(V.dpr,0,0,V.dpr,0,0);actx.clearRect(0,0,V.W,V.H);actx.lineCap='round';actx.lineJoin='round';
 for(const A2 of AN.arcs){const a=A2.a;const P=[toS(a[0],a[1]),toS(a[2],a[3]),toS(a[4],a[5])];
  const x0=Math.min(P[0][0],P[1][0],P[2][0]),x1=Math.max(P[0][0],P[1][0],P[2][0]),y0=Math.min(P[0][1],P[1][1],P[2][1]),y1=Math.max(P[0][1],P[1][1],P[2][1]);
  if(x1<-20||y1<-20||x0>V.W+20||y0>V.H+20)continue;
  const len=Math.hypot(P[2][0]-P[0][0],P[2][1]-P[0][1]);/* every plane flies the same speed: time by km, not by screen size */const per=Math.max(.8,A2.km/(380*(A.plane_speed||1)));const raw=tp/per+A2.ph;const u=pingpong(raw),back=(raw%2)>=1;
  const at=s=>{const v=1-s;return [v*v*P[0][0]+2*v*s*P[1][0]+s*s*P[2][0],v*v*P[0][1]+2*v*s*P[1][1]+s*s*P[2][1]]};
  if(len<40)continue;
  A2.cols.forEach((c,ci)=>{const uu=Math.max(0,Math.min(1,u-(back?-1:1)*ci*Math.min(.08,14/len)));const [px,py]=at(uu),[qx,qy]=at(Math.min(1,uu+.01)),[rx,ry]=at(Math.max(0,uu-.01));let ang=Math.atan2(qy-ry,qx-rx);if(back)ang+=Math.PI;if(A.hide_line){actx.globalAlpha=.85;actx.fillStyle=MC.land;actx.beginPath();actx.arc(px,py,9*sz,0,7);actx.fill();actx.globalAlpha=1}(A2.sp?drawSeaplane:drawPlane)(actx,px,py,ang,c,sz)});
 }
 for(const v of AN.cars){const b=v.bb;const [sx0,sy0]=toS(b[0],b[1]),[sx1,sy1]=toS(b[2],b[3]);if(sx1<-20||sy1<-20||sx0>V.W+20||sy0>V.H+20)continue;
  const lenpx=v.len*V.S;if(lenpx<40)continue;const lkm=v.len*40075*Math.cos(IY((b[1]+b[3])/2)*Math.PI/180);const per=Math.max(2.5,lkm/(v.m=='ferry'?45:v.m=='rail'?110:90));const raw=t/per+v.ph,u=pingpong(raw),back=(raw%2)>=1;
  const L=u*v.len;let lo=0,hi=v.cum.length-1;while(hi-lo>1){const mid=(lo+hi)>>1;if(v.cum[mid]<L)lo=mid;else hi=mid}
  const f=(L-v.cum[lo])/Math.max(1e-12,v.cum[hi]-v.cum[lo]);const wx=v.a[lo*2]+(v.a[hi*2]-v.a[lo*2])*f,wy=v.a[lo*2+1]+(v.a[hi*2+1]-v.a[lo*2+1])*f;
  const [px,py]=toS(wx,wy);let ang=Math.atan2(v.a[hi*2+1]-v.a[lo*2+1],v.a[hi*2]-v.a[lo*2]);if(back)ang+=Math.PI;ang=Math.atan2(Math.sin(ang),Math.cos(ang));
  if(A.hide_line){actx.globalAlpha=.85;actx.fillStyle=MC.land;actx.beginPath();actx.arc(px,py,9*sz,0,7);actx.fill();actx.globalAlpha=1}
  (v.m=='rail'?drawTrain:v.m=='ferry'?drawShip:drawCar)(actx,px,py,ang,v.col,sz)}
 AN.raf=requestAnimationFrame(animFrame);
}

/* ================= Legende ================= */
function legend(){const L=$('legend');const DA={dashed:'5 4',dotted:'0.1 5',longdash:'10 4',dashdot:'6 3 0.1 3',sparse:'0.1 8'};const ln=(c,n,dash)=>{const d=MODES.includes(dash)?SM(dash).dash:dash===true?'dashed':'solid';return `<div><svg width="26" height="10" aria-hidden="true"><path d="M2 5H24" stroke="${c}" stroke-width="3.2" stroke-linecap="round" ${DA[d]?`stroke-dasharray="${DA[d]}"`:''}/></svg>${esc(n)}</div>`};let it=[];
 if(TAB=='reisen'){it=R.color=='w'?WHO.map(w=>ln(WCOL[w],w)):MODES.map(m=>ln(MCOL[m],MNAME[m],m));it.push('<div><svg width="26" height="12" aria-hidden="true"><rect x="2" y="1" width="22" height="10" rx="5" fill="#E6E1F5" stroke="#8E86AE" stroke-width="1.2"/></svg>viele kurze Wege</div>')}
 else if(TAB=='spuren'){it=SP.color=='m'?['road','rail','foot','fly'].map(m=>ln(MCOL[m],MNAME[m],m)):SP.color=='w'?WORDER().map(w=>ln(WCOL[w],w)):[`<div><svg width="130" height="10" aria-hidden="true"><defs><linearGradient id="yg">${YCOL.map((c,i)=>`<stop offset="${i/10}" stop-color="${c}"/>`).join('')}</linearGradient></defs><rect x="0" y="2" width="130" height="6" rx="3" fill="url(#yg)"/></svg></div><div style="justify-content:space-between;width:130px"><span>${Y0}</span><span>${Y1}</span></div>`]}
 else if(TAB=='orte')it=[['Zuhause',MC.strong],...((O.pl||[]).some(p=>p.cat=='Arbeit')?[['Arbeit','#FFB000']]:[]),['Alltag',WCOL.Alltag],...WHO.filter(w=>w!='Alltag').map(w=>['Reise '+w,WCOL[w]])].map(([n,c])=>`<div><svg width="14" height="14" aria-hidden="true"><circle cx="7" cy="7" r="5.5" fill="${tint(c,.55)}" stroke="${c}" stroke-width="1.3"/></svg>${esc(n)}</div>`);
 else if(TAB=='regionen')it=['<div>Region antippen für Details</div>'];
 else it=['road','rail','foot','fly'].map(m=>ln(MCOL[m],MNAME[m],m)).concat(['<div><svg width="26" height="10" aria-hidden="true"><path d="M2 5H24" stroke="#8A82AA" stroke-width="2" opacity=".6"/></svg>früher</div>']);
 L.innerHTML=it.join('')}

/* ================= Interaktion ================= */
const wrap=$('wrap');const ptrs=new Map();let pinch=null,moved=false,downAt=null;
wrap.addEventListener('wheel',e=>{if(e.target.closest('.detail,.sdrawer'))return;e.preventDefault();const r=wrap.getBoundingClientRect();zoomAt(Math.exp(-e.deltaY*.0018),e.clientX-r.left,e.clientY-r.top)},{passive:false});
wrap.addEventListener('pointerdown',e=>{if(e.target.closest('.ctrl,.detail,.legend,.sdrawer,.presets'))return;ptrs.set(e.pointerId,{x:e.clientX,y:e.clientY});moved=false;downAt={x:e.clientX,y:e.clientY};wrap.setPointerCapture(e.pointerId);wrap.classList.add('drag');if(ptrs.size==2){const [a,b]=[...ptrs.values()];pinch={d:Math.hypot(a.x-b.x,a.y-b.y)}}});
wrap.addEventListener('pointermove',e=>{
 const r=wrap.getBoundingClientRect(),sx=e.clientX-r.left,sy=e.clientY-r.top;
 if(!ptrs.size&&e.pointerType=='mouse'){if(TAB=='orte'&&O.hit){const h=O.hit.findLast(([hx,hy,hr])=>Math.hypot(hx-sx,hy-sy)<hr);h?showTip(e,`${h[3][9]} · ${fmt(h[3][2])} h`):hideTip()}else if(TAB=='regionen'&&RG.list){const r=regAt(sx,sy);const v=r&&aggReg().get(r.id);r?showTip(e,r.name+' · '+(RG.countries[r.a3]||r.a3)+(v?` · seit ${v.first.slice(0,4)}`:' · noch nie')):hideTip()}}
 if(!ptrs.has(e.pointerId))return;const prev=ptrs.get(e.pointerId),cur={x:e.clientX,y:e.clientY};ptrs.set(e.pointerId,cur);
 if(Math.hypot(cur.x-downAt.x,cur.y-downAt.y)>5)moved=true;
 if(ptrs.size==2&&pinch){const [a,b]=[...ptrs.values()];const d=Math.hypot(a.x-b.x,a.y-b.y);zoomAt(d/pinch.d,(a.x+b.x)/2-r.left,(a.y+b.y)/2-r.top);pinch.d=d;return}
 V.cx-=(cur.x-prev.x)/V.S;V.cy-=(cur.y-prev.y)/V.S;redraw()});
function up(e){ptrs.delete(e.pointerId);if(ptrs.size<2)pinch=null;if(!ptrs.size){wrap.classList.remove('drag');clearTimeout(idleT);idleT=setTimeout(full,60)}}
wrap.addEventListener('pointerup',e=>{const wasMoved=moved;up(e);if(wasMoved||e.target.closest('.ctrl,.detail,.legend,.sdrawer,.presets'))return;const r=wrap.getBoundingClientRect(),sx=e.clientX-r.left,sy=e.clientY-r.top;
 if(TAB=='reisen'){const f=hitR(sx,sy);f?f():closeDetail()}
 else if(TAB=='orte'){const h=O.hit.findLast(([hx,hy,hr])=>Math.hypot(hx-sx,hy-sy)<hr);if(h)placeDetail(h[3])}
 else if(TAB=='regionen'){const r=regAt(sx,sy);RG.hit=r;full();if(r){const v=aggReg().get(r.id);openDetail(`<h3>${esc(r.name)}</h3><div class="dsub">${esc(RG.countries[r.a3]||r.a3)}</div>`+(v?`<div class="trip"><div class="s" style="background:${regFill(r)}"></div><div><div class="t1">Zum ersten Mal: ${dfmt(v.first)}</div><div class="t2">an ${fmt(v.days)} ${v.days==1?'Tag':'Tagen'} dort oder durchgefahren${v.stay?' · mit Aufenthalten':''}</div></div></div>`:'<div class="empty">Hier wart ihr laut den Daten noch nie.</div>'),()=>{RG.hit=null;full()})}else closeDetail()}});
wrap.addEventListener('pointercancel',up);
$('ztheme').onclick=()=>{const next=THEME=='dark'?'light':'dark';try{localStorage.setItem('wm-theme',next)}catch(e){}pickTheme();themeBtn();TC.clear();RG.groups=null;F.st=null;F.done=-1;if(PCOL)PCOL.Zuhause=MC.strong;whoBar();if(TAB=='orte')drawCal();enter(TAB)};
matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>{let t='auto';try{t=localStorage.getItem('wm-theme')||'auto'}catch(e){}if(t=='auto'){pickTheme();TC.clear();RG.groups=null;if(D)enter(TAB)}});
themeBtn();
$('zin').onclick=()=>zoomAt(1.7,V.W/2,V.H/2);$('zout').onclick=()=>zoomAt(1/1.7,V.W/2,V.H/2);
$('zhome').onclick=()=>flyTo(MX(HOME[1]),MY(HOME[0]),260000);
$('zch').onclick=()=>{const b=D.region.box;fit(b[0],b[1],b[2],b[3])};$('zeu').onclick=()=>{const s=V.S;fitTrips();const t={cx:V.cx,cy:V.cy,S:V.S};V.S=s;flyTo(t.cx,t.cy,t.S)};

/* ================= 🎨 Stil live auf der Karte ================= */
const SDR={saved:null,q:0};
function regColorFromStyle(){const v={first:'y',days:'d',stay:'v'}[ST('regions').fill_by]||'y';RG.color=v;document.querySelectorAll('#g-color button').forEach(b=>b.classList.toggle('on',b.dataset.v==v))}
function restyle(k){
 applyStyle(STYLE);STV++;
 if(k=='map.theme'&&!EMBED){try{if(STYLE.map.theme=='auto')localStorage.removeItem('wm-theme');else localStorage.setItem('wm-theme',STYLE.map.theme)}catch(e){}}
 if(k=='regions.fill_by'||k=='preview')regColorFromStyle();
 if(k&&(k.startsWith('est.')||k=='preview')){for(const t of D.trips)t._er=null}
 if(!SDR.q)SDR.q=requestAnimationFrame(()=>{SDR.q=0;pickTheme();themeBtn();assignColors();if(PCOL)PCOL.Zuhause=MC.strong;TC.clear();RG.groups=null;O.vmax=0;if(F)F.st=null;whoBar();enter(TAB)});
 sdState();presetsUI()}
function sdState(){const e=$('sd-st');if(!e)return;const ch=SDR.saved!=null&&JSON.stringify(STYLE)!==SDR.saved;e.textContent=ch?'Geändert – noch nicht gespeichert.':'Jede Änderung siehst du sofort auf der Karte.';e.style.color=ch?'#D9480F':''}
function openStyle(){if(!STYLE||typeof WM_SPEC=='undefined')return;if(SDR.saved==null)SDR.saved=JSON.stringify(STYLE);const d=$('sdrawer');closeDetail();
 /* only the essentials here: the look of the map and this map's own settings (folded); everything else lives in "Alle Einstellungen" */
 const mapSec=WM_SPEC.find(x=>x.id=='map'),quick={...mapSec,id:'quick',icon:'✨',title:'Aussehen',fields:mapSec.fields.filter(f=>['map.basemap','map.theme','map.look'].includes(f[0]))};
 const mine=WM_SPEC.filter(x=>x.tabs[0]==TAB&&x.id!='map');
 const names={reisen:'Reisen',spuren:'Spuren',orte:'Orte & Tage',regionen:'Regionen',zeit:'Reisefilm'};$('sd-t').textContent='🎨 Design';
 $('sd-b').innerHTML=wmSection(quick,STYLE)+(mine.length?`<details><summary class="sd-more">Mehr für die Karte „${names[TAB]||'Karte'}“</summary>${mine.map(x=>wmSection(x,STYLE)).join('')}</details>`:'');
 d.hidden=false;$('wrap').classList.add('sd-open');sdState()}
const sdClose=()=>{$('sdrawer').hidden=true;$('wrap').classList.remove('sd-open')};
$('zstyle').onclick=()=>{$('sdrawer').hidden?openStyle():sdClose()};
$('sd-x').onclick=sdClose;
/* the drawer edits the live STYLE; the proxy also answers 'own property?' – the safe setter (no prototype pollution) asks that before it writes */
if(typeof wmBind=='function')wmBind($('sd-b'),new Proxy({},{get:(_,k)=>STYLE[k],has:(_,k)=>k in STYLE,getOwnPropertyDescriptor:(_,k)=>Object.getOwnPropertyDescriptor(STYLE,k)}),k=>restyle(k));
$('sd-save').onclick=async()=>{try{const r=await fetch('api/style',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({style:STYLE,note:'auf der Karte ('+($('sd-t').textContent.split('· ')[1]||'')+')'})});if(!r.ok)throw new Error();const j=await r.json();STYLE=j.style;applyStyle(STYLE);SDR.saved=JSON.stringify(STYLE);sdState();$('sd-st').textContent='✓ Gespeichert – neue Version angelegt.'}catch(e){$('sd-st').textContent='Speichern ging nicht – bitte nochmals versuchen.'}};
$('sd-undo').onclick=()=>{if(SDR.saved==null)return;STYLE=JSON.parse(SDR.saved);restyle('map.theme');openStyle()};

/* ---------- Preset 1–3: three saved designs, quick choice on the map, one of them can be the default at start ---------- */
const PRE={list:[],def:-1};
const sameStyle=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function presetsUI(){const q=$('presets');if(q)q.innerHTML=PRE.list.map((p,i)=>`<button type="button" data-pload="${i+1}" aria-pressed="${!!STYLE&&sameStyle(STYLE,p.style)}" title="${esc(p.name)} laden">${PRE.def==i?'★ ':''}${esc(p.name)}</button>`).join('');
 const d=$('sd-pre');if(d)d.innerHTML='<h4>Meine Designs</h4>'+PRE.list.map((p,i)=>`<div class="pr"><input value="${esc(p.name)}" maxlength="24" data-pname="${i+1}" aria-label="Name von Preset ${i+1}"><button type="button" data-pload="${i+1}">Laden</button><button type="button" data-psave="${i+1}" title="Das aktuelle Aussehen hier speichern">💾 Hier speichern</button><button type="button" data-pdef="${i+1}" aria-pressed="${PRE.def==i}" aria-label="Beim Start verwenden: ${esc(p.name)}">${PRE.def==i?'★':'☆'}</button></div>`).join('')+'<p class="hint">Laden = sofort auf der Karte. 💾 speichert das, was du gerade siehst. ★ = dieses Design beim Öffnen.</p>'}
async function presetCall(n,body){try{const r=await fetch('api/style/presets/'+n,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!r.ok)throw new Error();const j=await r.json();PRE.list=j.presets||[];PRE.def=j.preset_default??-1;
  if(body.action=='load'&&j.style&&!sameStyle(j.style,STYLE)){/* only loading changes the map; saving keeps what you see */STYLE=j.style;SDR.saved=JSON.stringify(STYLE);restyle('map.theme');if(!$('sdrawer').hidden)openStyle()}presetsUI();return j}catch(e){const st=$('sd-st');if(st)st.textContent='Das ging nicht – bitte nochmals versuchen.';return null}}
document.addEventListener('click',e=>{const b=e.target.closest('[data-pload],[data-psave],[data-pdef]');if(!b)return;
 if(b.dataset.pload)presetCall(+b.dataset.pload,{action:'load'});
 else if(b.dataset.psave){const n=+b.dataset.psave,inp=document.querySelector(`[data-pname="${n}"]`);presetCall(n,{action:'save',name:inp?inp.value:null,style:STYLE}).then(j=>{if(j){SDR.saved=JSON.stringify(STYLE);const st=$('sd-st');if(st)st.textContent='✓ In „'+(j.presets[n-1]||{}).name+'“ gespeichert.'}})}
 else if(b.dataset.pdef)presetCall(+b.dataset.pdef,{action:'default'})});
document.addEventListener('change',e=>{const i=e.target.closest('[data-pname]');if(i)presetCall(+i.dataset.pname,{action:'rename',name:i.value})});
/* live preview inside the settings page: the page sends its draft style */
window.addEventListener('message',e=>{if(e.origin!==location.origin||!e.data||e.data.wm!=='style'||!D||typeof e.data.style!='object')return;STYLE=e.data.style;applyStyle(STYLE);if(ENTERED)restyle('preview');else pickTheme()});
/* ================= Daten aus der App ================= */
function assignColors(){WCOL={};let pi=0;const CC=D.colors||{};const used=new Set(Object.values(CC));
 for(const w of WHO){if(CC[w])WCOL[w]=CC[w];else if(w=='Alltag')WCOL[w]='#8A82AA';else if(w=='offen')WCOL[w]='#B8B0D6';else if(PALETTE==PALETTES.neon&&GROUPCOL[w]&&!D.persons.includes(w))WCOL[w]=GROUPCOL[w];else{while((used.has(PALETTE[pi%PALETTE.length])||Object.values(GROUPCOL).includes(PALETTE[pi%PALETTE.length])&&!D.persons.includes(w))&&pi<PALETTE.length*2)pi++;WCOL[w]=PALETTE[pi++%PALETTE.length]}}
 PCOL={Zuhause:MC.strong,Arbeit:'#FFB000',...WCOL};
}
function initData(){
 if(!D.days.length){const t=new Date().toISOString().slice(0,10);D.days=[[t,0,0,0,0,0,-1,0]]}
 HOME=D.home;WHO=D.who.slice();for(const n of [...(D.persons||[]),...GCFG().map(g=>g.name)])if(!WHO.includes(n))WHO.splice(WHO.length-1,0,n);
 assignColors();
 R.w=new Set(WHO);
 TYEARS=[...new Set(D.trips.map(t=>t.y))].sort((a,b)=>a-b);
 const dy0=+D.days[0][0].slice(0,4),dy1=+D.days[D.days.length-1][0].slice(0,4);DYEARS=[];for(let y=dy0;y<=dy1;y++)DYEARS.push(y);
 Y0=dy0;Y1=Math.max(dy1,dy0+1);
 const ay=[...TYEARS,...DYEARS];$('brandyears').textContent=ay.length?Math.min(...ay)+'–'+Math.max(...ay):'';
 $('r-sub').textContent=`Alle ${fmt(D.trips.length)} Reisen${TYEARS.length?' seit '+TYEARS[0]:''} plus der Alltag. Lücken zwischen GPS-Punkten folgen echten Strassen, Flüge als Bögen.`;

 const rb=$('zch');rb.textContent=D.region.cc||'⌖';rb.title=D.region.name?('Ganz '+D.region.name):'Heimatregion';rb.setAttribute('aria-label',rb.title);
 const ab=$('zeu');ab.textContent='Alle';ab.title='Alle Reisen';ab.setAttribute('aria-label','Alle Reisen');
 $('s-since').textContent=(D.since||D.days[0][0]).slice(0,4);
 $('s-note').textContent=`Zahlen aus den GPS-Daten ab ${dfmt(D.days[0][0])}. ${fmt(D.routed)} Lücken über das Strassennetz ergänzt; wo es nicht eindeutig ging, bleibt eine Lücke statt einer geraden Linie. Karte 1 zählt zusätzlich geschätzte Reisen ohne GPS.`;
}
function fitTrips(){const ps=(D.groups.length?D.groups.map(g=>[g[2],g[3]]).filter(p=>Math.hypot(p[0]-HOME[0],p[1]-HOME[1])<25):D.trips.filter(t=>t.p).map(t=>t.p));if(!ps.length){setFit(HOME[0]-2,HOME[1]-3,HOME[0]+2,HOME[1]+3);return}
 const la=ps.map(p=>p[0]).sort((a,b)=>a-b),lo=ps.map(p=>p[1]).sort((a,b)=>a-b);const q=a=>[a[Math.floor(a.length*.05)],a[Math.ceil(a.length*.95)-1]];const [a0,a1]=q(la),[o0,o1]=q(lo);
 setFit(Math.min(a0,HOME[0])-1,Math.min(o0,HOME[1])-1.5,Math.max(a1,HOME[0])+1,Math.max(o1,HOME[1])+1.5)}
function emptyState(){const e=$('empty');const pts=D.days.some(r=>r[7]);if(D.trips.length||pts){e.hidden=true;return}
 const ps=D.persons||[];e.hidden=false;e.innerHTML=`<h2>Noch nichts auf der Karte</h2><p>${ps.length?`Der Live-Standort von ${ps.map(esc).join(', ')} wird ab jetzt gesammelt. Reisen erscheinen, sobald jemand weiter als ${fmt(D.min_trip_km||30)} km weg ist.`:'Lege zuerst die Personen und Gruppen an.'}</p><p>Für die Vergangenheit: Google-Maps-Zeitachse (Android und iPhone) oder eine Reiseliste importieren.</p><div class="row"><a class="btn pri" href="app.html#import">Daten importieren</a><a class="btn" href="app.html#people">Personen &amp; Gruppen</a></div>`}
function routeNote(){const el=$('s-route'),s=window.STATS;if(!el||!s||!s.routes)return;const r=s.routes;if(s.routing=='off'||(!r.todo&&!r.running)){el.hidden=true;return}
 el.hidden=false;const tot=(r.segments||0)+(r.todo||0),pc=tot?Math.round((r.segments||0)/tot*100):0;
 el.innerHTML=`<div class="ct">🛤️ BAHN- &amp; STRASSENNETZ <small>${r.paused_s?'Kartenserver bittet um Pause – weiter in '+Math.ceil(r.paused_s/60)+' Min.':r.running?'wird berechnet …':'wartet'}</small></div><div class="rbar"><i style="width:${pc}%"></i></div><p class="small">${fmt(r.segments||0)} Abschnitte liegen schon auf echten Linien, ${fmt(r.todo||0)} folgen. Bis dahin bleiben dort Lücken statt gerader Striche. Neue Linien erscheinen beim nächsten Öffnen der Karte.</p>`}
function editTrip(dbid){location.href='app.html#edit-'+encodeURIComponent(dbid)}
function badge(){loadJSON('api/stats').then(s=>{window.STATS=s;routeNote();const q=$('qbtn');q.hidden=!s.open_questions;$('qbadge').textContent=s.open_questions;q.title=s.open_questions+(s.open_questions==1?' offene Frage':' offene Fragen')}).catch(()=>{})}
let ovlChanged=false;
function overlay(what){ovlChanged=false;$('ovl').querySelector('.ovl-box').classList.toggle('bare',what==='new');$('ovlf').src='app.html?embed='+what;$('ovl').hidden=false;$('ovlx').focus()}
function closeOverlay(){$('ovl').hidden=true;$('ovlf').src='about:blank';if(ovlChanged)location.reload();else badge()}
$('qbtn').onclick=()=>overlay('questions');$('addbtn').onclick=()=>overlay('new');$('ovlx').onclick=closeOverlay;
$('ovl').addEventListener('click',e=>{if(e.target.id==='ovl')closeOverlay()});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('ovl').hidden)closeOverlay()});
window.addEventListener('message',e=>{if(e.origin!==location.origin||e.source!==$('ovlf').contentWindow)return;const t=(e.data||{}).type;if(t==='worldmap-changed')ovlChanged=true;if(t==='worldmap-close')closeOverlay()});

/* ================= Tabs ================= */
let TAB='reisen';
const NEEDS={reisen:['tracks'],spuren:['tracks'],orte:['tracks'],regionen:['reg'],zeit:['tracks'],dash:[]};
function need(k){if(!window.__T.t0)__T.t0=performance.now();if(ready[k])return ready[k];if(k=='tracks')ready[k]=loadJSON('api/atlas/tracks').then(T=>{const t=performance.now();__T.fetch=t-__T.t0;prepTracks(T);__T.prep=performance.now()-t});if(k=='reg')ready[k]=Promise.all([loadJSON('regions.json?v=__WMV__'),loadJSON('api/atlas/reg')]).then(([m,g])=>prepReg(m,g));return ready[k]}
function setTab(t){
 TAB=t;closeDetail();hideTip();stopR();if(F.play)setPlayF(false);
 document.querySelectorAll('#tabs button').forEach(b=>b.classList.toggle('on',b.dataset.t==t));
 document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('on',p.id=='p-'+t));
 $('hud').style.display='none';$('ztitle').classList.remove('show');
 try{history.replaceState(null,'','#'+t)}catch(e){}
 $('load').style.display='grid';
 Promise.all(NEEDS[t].map(need)).then(()=>{$('load').style.display='none';enter(t)}).catch(()=>{$('load').textContent='Daten konnten nicht geladen werden.'});
}
const fitted={};let ENTERED=false;
function enter(t){ENTERED=true;
 if(t=='dash'){DRAW=()=>{};animRestart();dashEnter();return}dashLeave();
 legend();$('legend').style.display=t=='zeit'?'none':'';const _e=performance.now();setTimeout(()=>{__T.enter=performance.now()-_e},0);
 if(t=='reisen'){DRAW=drawR;chipsR();let _t=performance.now();buildR();__T.buildR=performance.now()-_t;sideR();if(!fitted.r){fitted.r=1;fitTrips()}}
 if(t=='spuren'){routeNote();DRAW=drawS;chipsS();let _t=performance.now();buildS();__T.buildS=performance.now()-_t;_t=performance.now();sideS();__T.sideS=performance.now()-_t;if(!fitted.s){fitted.s=1;const b=D.region.box;setFit(b[0],b[1],b[2],b[3])}}
 if(t=='orte'){DRAW=drawO;if(!O.pl)O.pl=D.places.filter(placeSel).map(p=>{p.cat=placeCat(p);return p}).sort((a,b)=>b[2]-a[2]);sideO();drawCal();if(!fitted.o){fitted.o=1;setFit(HOME[0]-.35,HOME[1]-.7,HOME[0]+.3,HOME[1]+.5)}}
 if(t=='regionen'){if(!fitted.g)regColorFromStyle();DRAW=drawRG;sideRG();if(!fitted.g){fitted.g=1;const A=aggReg();let b=null;for(const id of A.keys()){const r=RG.byId.get(id);if(r)b=ub(b,r.bb)}if(b){const S=Math.min((V.W-80)/(b[2]-b[0]),(V.H-80)/(b[3]-b[1]));V.cx=(b[0]+b[2])/2;V.cy=(b[1]+b[3])/2;V.S=Math.min(S,120000)}else{const q=D.region.box;setFit(q[0],q[1],q[2],q[3])}}}
 if(t=='zeit'){DRAW=drawF;if(!F.sc)buildF();else sideF()}
 full();animRestart();if(!$('sdrawer').hidden)openStyle();
}
document.querySelectorAll('#tabs button').forEach(b=>b.onclick=()=>setTab(b.dataset.t));
window.addEventListener('hashchange',()=>{const h=location.hash.slice(1);if(D&&NEEDS[h]&&h!=TAB)setTab(h)});
let rsz=null;window.addEventListener('resize',()=>{clearTimeout(rsz);rsz=setTimeout(()=>{sizeCV();sizeA();full();if(TAB=='orte')drawCal()},120)});
/* descriptions live behind a small (i) button so the panels stay calm */
document.querySelectorAll('.panel').forEach(pn=>{const h=pn.querySelector('h1');if(!h)return;const head=h.parentElement;const bits=[...pn.querySelectorAll('.sub,details.note')];if(!bits.length)return;
 const box=document.createElement('div');box.className='infobox';box.hidden=true;box.id='info-'+pn.id;
 for(const b of bits){const q=document.createElement('p');if(b.tagName=='DETAILS'){const sm=b.querySelector('summary');if(sm)sm.remove();while(b.firstChild)q.appendChild(b.firstChild)}else{q.id=b.id||'';while(b.firstChild)q.appendChild(b.firstChild)}box.appendChild(q);b.remove()}
 const wrapH=document.createElement('div');wrapH.className='ph';head.insertBefore(wrapH,h);wrapH.appendChild(h);
 const btn=document.createElement('button');btn.className='info';btn.textContent='i';btn.setAttribute('aria-label','Was zeigt diese Karte?');btn.setAttribute('aria-expanded','false');btn.setAttribute('aria-controls',box.id);
 btn.onclick=()=>{box.hidden=!box.hidden;btn.setAttribute('aria-expanded',String(!box.hidden))};wrapH.appendChild(btn);head.appendChild(box)});
/* Dashboard: the trips as numbers and small pictures instead of a map.
   Uses the globals of atlas.js (D, SEL, tripSel, members, WCOL, MCOL, MNAME, esc, fmt …). */
const DASH={tiles:null,pc:null,year:null,preset:null,kt:0};
/* five ready-made dashboards; "eigene" is the user's own choice of tiles */
const DPRESETS=[
 ['all','Übersicht','Alles auf einer Seite.',null,{},'🗺️','#2D7BFF'],
 ['year','Jahresrückblick','Ein Jahr wählen – alle Kacheln zeigen nur dieses Jahr.',['kpi','calendar','records','postcard','passport','wheel','co2'],{year:1},'📅','#FF2DAA'],
 ['family','Familie','Wer war wann wo – und die Orte, an die ihr immer wieder geht.',['kpi','lanes','postcard','favs','passport'],{},'👨‍👩‍👧','#00C26E'],
 ['explorer','Entdecker','Wie viel Welt ihr schon gesehen habt – und was noch fehlt.',['earth','passport','blank','records','co2'],{},'🧭','#FF8A00'],
 ['kiosk','Wandtablet','Grosse Schrift für das Tablet am Kühlschrank; die Postkarte wechselt alle 15 Sekunden.',['postcard','kpi','earth','calendar'],{kiosk:1},'🖼️','#00B8C9'],
];
const DOWN=['own','Eigene','Deine eigene Auswahl über „Anpassen“.',null,{},'✏️','#8B3DFF'];
function dPreset(){if(DASH.preset)return DASH.preset;let v='all';try{v=localStorage.getItem('wm-dash-preset')||'all'}catch(e){}DASH.preset=DPRESETS.some(p=>p[0]==v)||v=='own'?v:'all';return DASH.preset}
function dOpts(){const p=DPRESETS.find(x=>x[0]==dPreset());return p?p[4]:{}}
function dOrder(){const p=DPRESETS.find(x=>x[0]==dPreset());if(p&&p[3])return p[3];const on=dTilesOn();return DTILES.map(t=>t[0]).filter(k=>p||on.has(k))}
const DTILES=[
 ['kpi','Auf einen Blick','Die wichtigsten Zahlen der gewählten Person oder Gruppe.'],
 ['postcard','Reise-Postkarte','Jede Reise als Postkarte mit der echten Karte, Route, Briefmarke und Poststempel. Antippen dreht sie um, Wischen oder ‹ › blättert, 🎲 zeigt eine zufällige Erinnerung, ⬇ speichert die Vorderseite als Bild.'],
 ['earth','Um die Erde','Alle Reise-Kilometer zusammen, gemessen am Erdumfang (40’075 km) und am Weg zum Mond (384’400 km). Alltag zählt nicht mit.'],
 ['records','Rekorde','Weiteste, längste und kilometerreichste Reise, längste Autofahrt und das Jahr mit den meisten Ländern. Antippen öffnet die Postkarte.'],
 ['passport','Länder-Pass','Ein Stempel pro Land, mit dem Jahr des ersten Besuchs. Je mehr Reisen, desto kräftiger der Stempel.'],
 ['calendar','Reise-Kalender','Alle Tage eines Jahres; farbig sind die Reisetage, nach Person oder Gruppe gefärbt.'],
 ['lanes','Familien-Zeitstrahl','Eine Spur pro Person über die Jahre. Gemeinsame Reisen verbinden die Spuren mit einer Linie.'],
 ['wheel','Reise-Rad','Wann im Jahr ihr reist: pro Monat die Reisenächte, nach dem wichtigsten Verkehrsmittel der Reise gefärbt.'],
 ['favs','Lieblingsorte','Orte, an die ihr immer wieder geht (ohne Zuhause und Arbeit). Grösse = Tage dort, Ring = Anzahl Besuche.'],
 ['co2','Unterwegs-Bilanz','Reise-Kilometer pro Jahr nach Verkehrsmittel und ein grob geschätztes CO₂ pro Person (Flug 0.25, Auto 0.17, Schiff 0.12, Zug 0.03 kg pro km).'],
 ['blank','Weisse Flecken','Pro Land: wie viele Regionen (Kantone, Bundesländer, Provinzen) ihr schon kennt – und wie viele noch fehlen.'],
];
const CO2={fly:.25,road:.17,ferry:.12,rail:.03,foot:0};
function dTilesOn(){if(DASH.tiles)return DASH.tiles;let off=[];try{off=JSON.parse(localStorage.getItem('wm-dash-off')||'[]')}catch(e){}DASH.tiles=new Set(DTILES.map(t=>t[0]).filter(k=>!off.includes(k)));return DASH.tiles}
function dSaveTiles(){try{localStorage.setItem('wm-dash-off',JSON.stringify(DTILES.map(t=>t[0]).filter(k=>!DASH.tiles.has(k))))}catch(e){}}
const dHav=(a,b,c,d)=>{const r=Math.PI/180,x=Math.sin((c-a)*r/2)**2+Math.cos(a*r)*Math.cos(c*r)*Math.sin((d-b)*r/2)**2;return 12742*Math.asin(Math.sqrt(x))};
const dHash=s=>{let h=7;for(const c of String(s))h=(h*31+c.charCodeAt(0))>>>0;return h};
const dCol=w=>WCOL[w]||'#8B3DFF';
function dTrips(){return D.trips.filter(t=>tripSel(t)).sort((a,b)=>a.a<b.a?-1:1)}
function dMain(t){let best=null,v=-1;for(const m in t.k||{})if(t.k[m]>v){v=t.k[m];best=m}return best||(t.m&&t.m[0])||'road'}
function dCountries(t){return String(t.c||'').split(/\s*[,·]\s*/).filter(Boolean)}
function dFar(t){return t.nopos?0:dHav(HOME[0],HOME[1],t.p[0],t.p[1])}
const MONTHS_DE=['','Januar','Februar','März','April','Mai','Juni','Juli','August','September','Oktober','November','Dezember'];
/* a trip known only by month or year ("Juli 2009", "2009") – the stored days are a stand-in, never shown as exact */
function tWhen(t){if(t.dp=='year')return '~ '+t.a.slice(0,4);if(t.dp!='month')return null;const ya=t.a.slice(0,4),yb=t.b.slice(0,4),ma=MONTHS_DE[+t.a.slice(5,7)],mb=MONTHS_DE[+t.b.slice(5,7)];
 return '~ '+(ya==yb?(ma==mb?ma:ma+'–'+mb)+' '+ya:ma+' '+ya+'–'+mb+' '+yb)}
function dRange(t){const v=tWhen(t);if(v)return v;return `${t.a.slice(8,10)}.${t.a.slice(5,7)}.${t.a.slice(0,4)}${t.b!=t.a?' – '+t.b.slice(8,10)+'.'+t.b.slice(5,7)+'.'+t.b.slice(0,4):''}`}

/* ---------------------------------------------------------------- tiles */
function tKpi(T){const cs=new Set(T.flatMap(dCountries)),n=T.reduce((s,t)=>s+(t.n||0),0),km=T.reduce((s,t)=>s+(t.km||0),0);
 const ys=new Set(T.map(t=>t.y));
 return `<div class="dk">${[[T.length,T.length==1?'Reise':'Reisen'],[cs.size,cs.size==1?'Land':'Länder'],[fmt(n),'Nächte unterwegs'],[fmt(km),'km gereist'],[ys.size,ys.size==1?'Jahr mit Reisen':'Jahre mit Reisen']].map(([v,l])=>`<div><b>${v}</b><span>${l}</span></div>`).join('')}</div>`}

function tEarth(T){const km=T.reduce((s,t)=>s+(t.km||0),0),E=40075,M=384400,laps=km/E,f=laps%1,full=Math.floor(laps),R=62,C=2*Math.PI*R;
 const by={};for(const t of T)for(const m in t.k||{})by[m]=(by[m]||0)+t.k[m];
 let off=0;const segs=MODES.filter(m=>by[m]>0).map(m=>{const l=Math.min(1,by[m]/Math.max(km,1))*C;const s=`<circle r="${R}" cx="80" cy="80" fill="none" stroke="${MCOL[m]}" stroke-width="14" stroke-dasharray="${l} ${C-l}" stroke-dashoffset="${-off}" transform="rotate(-90 80 80)"/>`;off+=l;return s}).join('');
 return `<div class="dearth"><svg viewBox="0 0 160 160" width="160" height="160" role="img" aria-label="${laps.toFixed(1)} mal um die Erde">
  <circle r="${R}" cx="80" cy="80" fill="none" stroke="var(--soft)" stroke-width="14"/>${segs}
  <circle r="${R-16}" cx="80" cy="80" fill="none" stroke="var(--acc)" stroke-width="4" stroke-dasharray="${f*2*Math.PI*(R-16)} 999" transform="rotate(-90 80 80)" stroke-linecap="round"/>
  <text x="80" y="78" text-anchor="middle" font-size="30" font-weight="800" fill="var(--ink)">${laps.toFixed(1)}×</text><text x="80" y="98" text-anchor="middle" font-size="11" fill="var(--mute)">um die Erde</text></svg>
  <div><p><b>${fmt(km)} km</b> auf Reisen – ${full?`${full}× ganz um die Erde und ${Math.round(f*100)} % der nächsten Runde`:`${Math.round(f*100)} % einer Erdumrundung`}.</p>
  <p class="dmute">Bis zum Mond: ${Math.min(100,km/M*100).toFixed(1)} % geschafft.</p><div class="dmoon"><i style="width:${Math.min(100,km/M*100)}%"></i></div>
  <div class="dleg">${MODES.filter(m=>by[m]>0).map(m=>`<span><i style="background:${MCOL[m]}"></i>${MNAME[m]} ${fmt(by[m])} km</span>`).join('')}</div></div></div>`}

function tRecords(T){if(!T.length)return '<div class="empty">Noch keine Reisen.</div>';
 const mx=(f)=>T.reduce((b,t)=>f(t)>f(b)?t:b,T[0]);
 const far=mx(dFar),lon=mx(t=>t.n||0),kms=mx(t=>t.km||0),car=mx(t=>(t.k||{}).road||0);
 const cy={};for(const t of T)for(const c of dCountries(t))(cy[t.y]=cy[t.y]||new Set()).add(c);const by=Object.entries(cy).sort((a,b)=>b[1].size-a[1].size)[0];
 const row=(ico,l,t,v)=>t?`<button class="drec" data-trip="${t.id}"><span class="di">${ico}</span><span><small>${l}</small><b>${esc(t.name)}</b><em>${v}</em></span></button>`:'';
 return `<div class="drecs">${row('🧭','Am weitesten weg',far,fmt(dFar(far))+' km Luftlinie · '+far.y)}${row('🌙','Am längsten',lon,(lon.n||0)+' Nächte · '+lon.y)}${row('📏','Meiste Kilometer',kms,fmt(kms.km)+' km · '+kms.y)}${(car.k||{}).road?row('🚗','Längste Autofahrt',car,fmt(car.k.road)+' km im Auto · '+car.y):''}
  ${by?`<div class="drec"><span class="di">🗺️</span><span><small>Meiste Länder in einem Jahr</small><b>${by[0]}</b><em>${by[1].size} Länder: ${esc([...by[1]].join(', '))}</em></span></div>`:''}</div>`}

function tPassport(T){const first={},cnt={};for(const t of T)for(const c of dCountries(t)){if(!first[c]||t.a<first[c])first[c]=t.a;cnt[c]=(cnt[c]||0)+1}
 const cs=Object.keys(first).sort((a,b)=>first[a]<first[b]?-1:1);if(!cs.length)return '<div class="empty">Noch keine Länder.</div>';
 const pal=['#FF3D9A','#0A7CFF','#12A84F','#8B3DFF','#FF8A00','#00BFB3','#D23DB0'],A3={};for(const k in (RG.countries||{}))A3[RG.countries[k].toLowerCase()]=k;
 return `<div class="dpass">${cs.map(c=>{const h=dHash(c),col=pal[h%pal.length],rot=(h%23)-11,op=Math.min(1,.55+cnt[c]*.12);
  return `<div class="dstamp" style="--c:${col};transform:rotate(${rot}deg);opacity:${op}" title="${esc(c)}: ${cnt[c]} ${cnt[c]==1?'Reise':'Reisen'}"><b>${esc(A3[c.toLowerCase()]||c.slice(0,3).toUpperCase())}</b><span>${esc(c)}</span><em>${first[c].slice(0,4)}</em></div>`}).join('')}</div>`}

/* ---------------------------------------------------------------- the postcard
   Front: the real map of the trip (land from the base map, the route as recorded or estimated), a stamp of the
   country and a postmark. Back: greetings, dates, km per transport, who was there, stations. Tap to turn over. */
const PCS={flip:false};
const PC_HAND="'Segoe Script','Bradley Hand','Snell Roundhand','Apple Chancery','Comic Sans MS',cursive";
function pcTrip(T){const t=T.find(x=>x.id==DASH.pc)||T[T.length-1];DASH.pc=t.id;return t}
function pcCountry(t){return dCountries(t)[0]||''}
const PC_A3={grossbritannien:'GBR','vereinigtes königreich':'GBR',england:'GBR',schottland:'GBR',wales:'GBR',usa:'USA','vereinigte staaten':'USA',holland:'NLD',niederlande:'NLD',tschechien:'CZE',russland:'RUS',südkorea:'KOR',vae:'ARE','vereinigte arabische emirate':'ARE'};
function pcA3(c){const A3={...PC_A3};for(const k in (RG.countries||{}))A3[RG.countries[k].toLowerCase()]=k;return A3[c.toLowerCase()]||PC_A3[c.toLowerCase()]||c.slice(0,3).toUpperCase()}
function pcStations(t){return t.st&&t.st.length?t.st.map(x=>({la:x[0],lo:x[1],n:x[3]?'✈ '+x[3]:x[2],ap:x[3]||''})):t.nopos?[]:[{la:t.p[0],lo:t.p[1],n:t.name}]}
function tPostcard(T){if(!T.length)return '<div class="empty">Noch keine Reisen.</div>';
 const t=pcTrip(T),i=T.indexOf(t);
 const opts=[...T].reverse().map(x=>`<option value="${x.id}" ${x.id==t.id?'selected':''}>${x.y} · ${esc(x.name)}</option>`).join('');
 return `<div class="pcw" id="pcw">
  <div class="pcard${PCS.flip?' flip':''}" id="pcard" tabindex="0" role="button" aria-label="Postkarte ${esc(t.name)} – antippen zum Umdrehen, wischen für die nächste Reise">
   <div class="pcin"><div class="pcf"><canvas id="pccv" width="1200" height="800" role="img" aria-label="Karte der Reise ${esc(t.name)}"></canvas></div><div class="pcb">${pcBack(t)}</div></div></div>
  <div class="pcnav"><button class="pcbtn" data-pc="prev" aria-label="Vorherige Reise" ${i<=0?'disabled':''}>‹</button>
   <select class="dsel" id="dpc-sel" aria-label="Reise wählen">${opts}</select>
   <button class="pcbtn" data-pc="next" aria-label="Nächste Reise" ${i>=T.length-1?'disabled':''}>›</button>
   <span class="pcsp"></span><button class="pcbtn txt" data-pc="rnd" title="Eine zufällige Reise">🎲 Zufall</button><button class="pcbtn txt" data-pc="flip">↻ Umdrehen</button><button class="pcbtn txt" data-pc="png" title="Vorderseite als Bild speichern">⬇ Bild</button></div></div>`}
function pcBack(t){const by=Object.entries(t.k||{}).filter(([,v])=>v>0).sort((a,b)=>b[1]-a[1]);const st=pcStations(t);
 const cs=dCountries(t),h=dHash(pcCountry(t)||t.name),pal=['#FF3D9A','#0A7CFF','#12A84F','#8B3DFF','#FF8A00','#00BFB3','#D23DB0'],col=pal[h%pal.length];
 return `<div class="pcmsg"><p class="pchi">Grüsse aus ${esc(t.name)}!</p>
  <p>${esc(dRange(t))} · ${t.n||0} ${t.n==1?'Nacht':'Nächte'}${cs.length?' · '+esc(cs.join(', ')):''}</p>
  ${by.length?`<p>${by.map(([m,v])=>`${ICO[m]||''} ${MNAME[m]} ${fmt(v)} km`).join(' · ')}</p>`:''}
  ${st.length>1?`<p>${st.map(x=>esc(x.n)).join(' → ')}</p>`:''}
  <p>Dabei: ${esc(t.w)}</p><p class="pcsig">${fmt(t.km||0)} km – bis bald!</p></div>
 <div class="pcadr"><div class="pcstamp" style="--c:${col}"><b>${esc(pcA3(pcCountry(t)||t.name))}</b><span>${t.y}</span></div>
  <div class="pclines"><span>An</span><span>Zuhause</span><span>${esc((D.persons||[]).join(', ').slice(0,40)||'Worldmap')}</span><span>Worldmap ✉</span></div></div>`}
function pcDraw(t){const cv=document.getElementById('pccv');if(!cv||!B)return;const g=cv.getContext('2d'),W=cv.width,H=cv.height,M=26;
 const P=(la,lo)=>[MX(lo),MY(la)],st=pcStations(t),home=P(HOME[0],HOME[1]),lines=[],tracks=[];
 for(const r of t.gr||[]){const f=r[1],a=[];for(let k=0;k+1<f.length;k+=2)a.push(P(f[k],f[k+1]));if(a.length>1)lines.push({m:r[2]||'road',a})}
 if(TR){const ds=new Set();D.days.forEach((r,k)=>{if(r[6]==t.id)ds.add(k)});TR.forEach(l=>{if(ds.has(l.d)){const a=[];const q=l.lm;for(let k=0;k+1<q.length;k+=2)a.push([q[k],q[k+1]]);if(a.length>1)tracks.push(a)}})}
 const seen=new Set(),fl=[];for(const f of t.fl||[]){const key=[f[0],f[1]].map(x=>x.join(',')).sort().join('|');if(seen.has(key))continue;seen.add(key);fl.push({a:P(f[0][0],f[0][1]),b:P(f[1][0],f[1][1]),sea:f[4]==1})}
 /* what the card shows: the stations and ways there – home only when it is close enough not to shrink everything */
 const box=[];st.forEach(x=>box.push(P(x.la,x.lo)));lines.forEach(l=>box.push(...l.a));tracks.forEach(a=>box.push(...a.filter((_,k)=>k%4==0)));
 const far=st.length?Math.max(...st.map(x=>dHav(HOME[0],HOME[1],x.la,x.lo))):0;
 if(far<1600||!box.length)box.push(home);fl.forEach(f=>{if(far<1600||(Math.hypot(f.a[0]-home[0],f.a[1]-home[1])>.004))box.push(f.a);if(far<1600||(Math.hypot(f.b[0]-home[0],f.b[1]-home[1])>.004))box.push(f.b)});
 let x0=1,y0=1,x1=0,y1=0;for(const [x,y] of box){x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y)}
 const sw=Math.max(x1-x0,.0035),sh=Math.max(y1-y0,.0035),cx=(x0+x1)/2,cy=(y0+y1)/2;
 /* the route sits in the free part of the card: not under the stamp (top right) nor the lettering (bottom) */
 const fx0=M+70,fy0=M+70,fx1=W-M-360,fy1=H-M-200,sc=Math.min((fx1-fx0)/sw,(fy1-fy0)/sh),ox=(fx0+fx1)/2-cx*sc,oy=(fy0+fy1)/2-cy*sc,X=x=>ox+x*sc,Y=y=>oy+y*sc;
 g.save();g.clearRect(0,0,W,H);
 /* paper border and the picture */
 g.fillStyle='#FFFDF7';g.fillRect(0,0,W,H);
 g.beginPath();g.roundRect(M,M,W-2*M,H-2*M,18);g.clip();
 const sea=g.createLinearGradient(0,M,0,H-M);sea.addColorStop(0,'#8FDCEB');sea.addColorStop(1,'#2E7FCB');g.fillStyle=sea;g.fillRect(0,0,W,H);
 g.save();g.setTransform(sc,0,0,sc,ox,oy);g.shadowColor='rgba(10,40,80,.35)';g.shadowBlur=18;g.shadowOffsetY=6;
 g.fillStyle='#F4E8CC';g.fill(B.land,'nonzero');g.shadowColor='transparent';
 const lake=g.createLinearGradient(0,y0,0,y1);g.fillStyle='#7CCBE6';g.fill(B.lakes,'nonzero');
 g.lineWidth=1.6/sc;g.strokeStyle='rgba(120,90,60,.35)';g.setLineDash([6/sc,5/sc]);g.stroke(B.borders);g.setLineDash([]);
 g.lineWidth=1.2/sc;g.strokeStyle='rgba(60,140,200,.45)';g.stroke(B.rivB);g.restore();
 /* graticule: a hint of latitude and longitude, also where there is only sea (atolls) */
 {const span=sw*360,step=span>60?15:span>20?5:span>6?2:span>2?1:.5,lo0=(-ox/sc)*360-180,lo1=((W-ox)/sc)*360-180;g.strokeStyle='rgba(255,255,255,.22)';g.lineWidth=1.2;g.beginPath();
  for(let lo=Math.ceil(lo0/step)*step;lo<=lo1;lo+=step){const x=X(MX(lo));g.moveTo(x,0);g.lineTo(x,H)}
  for(let la=-80;la<=80;la+=step){const y=Y(MY(la));if(y>0&&y<H){g.moveTo(0,y);g.lineTo(W,y)}}g.stroke()}
 const vig=g.createRadialGradient(W/2,H/2,H*.35,W/2,H/2,H*.95);vig.addColorStop(0,'rgba(0,0,0,0)');vig.addColorStop(1,'rgba(10,20,60,.28)');g.fillStyle=vig;g.fillRect(0,0,W,H);
 /* the ways */
 const poly=(a,col,w,dash)=>{g.beginPath();a.forEach(([x,y],k)=>k?g.lineTo(X(x),Y(y)):g.moveTo(X(x),Y(y)));g.lineJoin='round';g.lineCap='round';
  g.setLineDash([]);g.strokeStyle='rgba(255,255,255,.95)';g.lineWidth=w+6;g.stroke();g.setLineDash(dash||[]);g.strokeStyle=col;g.lineWidth=w;g.stroke();g.setLineDash([])};
 /* no way known for a leg (only some GPS points): a faint dashed line keeps the order of the stations readable */
 const covered=st.length&&tracks.length&&st.every(x=>{const [px,py]=P(x.la,x.lo);return tracks.some(a=>a.some(([qx,qy])=>Math.hypot(X(qx)-X(px),Y(qy)-Y(py))<40))});
 if(!fl.length&&!lines.length&&st.length&&!covered){const a=[home,...st.map(x=>P(x.la,x.lo))];g.beginPath();a.forEach(([x,y],k)=>k?g.lineTo(X(x),Y(y)):g.moveTo(X(x),Y(y)));g.setLineDash([3,11]);g.lineCap='round';g.strokeStyle='rgba(23,18,46,.45)';g.lineWidth=4;g.stroke();g.setLineDash([])}
 tracks.forEach(a=>poly(a,dCol(t.w),5));lines.forEach(l=>poly(l.a,MCOL[l.m]||'#0A7CFF',6,l.m=='ferry'?[2,12]:null));
 for(const f of fl){const ax=X(f.a[0]),ay=Y(f.a[1]),bx=X(f.b[0]),by=Y(f.b[1]),d=Math.hypot(bx-ax,by-ay),bend=f.sea?.12:.24,mx=(ax+bx)/2-(by-ay)*bend,my=(ay+by)/2+(bx-ax)*bend;
  const col=f.sea?'#00B8C9':MCOL.fly;g.beginPath();g.moveTo(ax,ay);g.quadraticCurveTo(mx,my,bx,by);g.lineCap='round';g.strokeStyle='rgba(255,255,255,.95)';g.lineWidth=10;g.stroke();
  g.setLineDash([2,13]);g.strokeStyle=col;g.lineWidth=5;g.stroke();g.setLineDash([]);
  if(d>60){const px=.25*ax+.5*mx+.25*bx,py=.25*ay+.5*my+.25*by,an=Math.atan2(by-ay,bx-ax);g.save();g.translate(px,py);g.rotate(an);g.font='34px system-ui,"Apple Color Emoji","Segoe UI Emoji"';g.textAlign='center';g.textBaseline='middle';
   g.shadowColor='rgba(0,0,0,.3)';g.shadowBlur=6;g.fillText(f.sea?'🛩️':'✈️',0,0);g.restore()}}
 /* places */
 const label=(x,y,txt,size)=>{g.font=`800 ${size}px Inter,system-ui,sans-serif`;g.textAlign='center';g.lineJoin='round';g.lineWidth=7;g.strokeStyle='rgba(255,255,255,.95)';g.strokeText(txt,x,y);g.fillStyle='#17122E';g.fillText(txt,x,y)};
 const hx=X(home[0]),hy=Y(home[1]);if(hx>M&&hx<W-M&&hy>M&&hy<H-M){g.beginPath();g.arc(hx,hy,9,0,7);g.fillStyle='#17122E';g.fill();g.lineWidth=4;g.strokeStyle='#fff';g.stroke();label(hx,hy-18,'Zuhause',22)}
 st.forEach((x,k)=>{const [px,py]=P(x.la,x.lo),sx=X(px),sy=Y(py);g.beginPath();g.arc(sx,sy,12,0,7);g.fillStyle='#fff';g.fill();g.lineWidth=6;g.strokeStyle=dCol(t.w);g.stroke();
  if(st.length<=8)label(sx,sy-22,String(x.n).slice(0,22),st.length>4?22:26)});
 g.restore();
 /* "Grüsse aus" lettering */
 const name=String(t.name).toUpperCase();let fs=128;g.font=`900 ${fs}px Inter,system-ui,sans-serif`;while(g.measureText(name).width>W*.62&&fs>44){fs-=4;g.font=`900 ${fs}px Inter,system-ui,sans-serif`}
 const bx=M+40,by=H-M-46;g.save();g.textAlign='left';g.textBaseline='alphabetic';
 g.font=`700 46px ${PC_HAND}`;g.lineWidth=8;g.strokeStyle='rgba(23,18,46,.85)';g.strokeText('Grüsse aus',bx+6,by-fs*.92);g.fillStyle='#FFF7E0';g.fillText('Grüsse aus',bx+6,by-fs*.92);
 g.font=`900 ${fs}px Inter,system-ui,sans-serif`;g.shadowColor='rgba(23,18,46,.55)';g.shadowOffsetX=6;g.shadowOffsetY=7;g.shadowBlur=0;g.fillStyle='#17122E';g.fillText(name,bx,by);
 g.shadowColor='transparent';const gr=g.createLinearGradient(bx,by-fs,bx+W*.6,by);gr.addColorStop(0,'#FF2DAA');gr.addColorStop(.5,'#8B3DFF');gr.addColorStop(1,'#2D7BFF');
 g.fillStyle=gr;g.fillText(name,bx-3,by-3);g.lineWidth=3;g.strokeStyle='#FFF7E0';g.strokeText(name,bx-3,by-3);g.restore();
 /* stamp with perforated edge */
 const sw2=176,sh2=212,sx0=W-M-sw2-30,sy0=M+30,c=pcCountry(t),h=dHash(c||t.name),pal=['#FF3D9A','#0A7CFF','#12A84F','#8B3DFF','#FF8A00','#00BFB3','#D23DB0'],col=pal[h%pal.length];
 const sc2=document.createElement('canvas');sc2.width=sw2;sc2.height=sh2;const q=sc2.getContext('2d');q.fillStyle='#FFFDF7';q.fillRect(0,0,sw2,sh2);
 const sgr=q.createLinearGradient(0,0,sw2,sh2);sgr.addColorStop(0,col);sgr.addColorStop(1,'#17122E');q.fillStyle=sgr;q.fillRect(14,14,sw2-28,sh2-28);
 q.fillStyle='rgba(255,255,255,.14)';for(let k=0;k<6;k++){q.beginPath();q.arc(sw2*.7,sh2*.32,18+k*16,0,7);q.lineWidth=3;q.strokeStyle='rgba(255,255,255,.16)';q.stroke()}
 q.fillStyle='#fff';q.textAlign='center';q.font='900 58px Inter,system-ui,sans-serif';q.fillText(pcA3(c||t.name),sw2/2,104);q.font='700 15px Inter,system-ui,sans-serif';q.fillText(String(c||t.name).slice(0,16),sw2/2,128);
 q.font='34px system-ui,"Apple Color Emoji","Segoe UI Emoji"';q.fillText(ICO[dMain(t)]||'🧳',sw2/2,172);q.font='800 16px Inter,system-ui,sans-serif';q.fillText(String(t.y),sw2-36,sh2-26);
 q.globalCompositeOperation='destination-out';for(let x=0;x<=sw2;x+=16){q.beginPath();q.arc(x,0,6,0,7);q.arc(x,sh2,6,0,7);q.fill()}for(let y=0;y<=sh2;y+=16){q.beginPath();q.arc(0,y,6,0,7);q.arc(sw2,y,6,0,7);q.fill()}
 g.save();g.translate(sx0+sw2/2,sy0+sh2/2);g.rotate(.05);g.shadowColor='rgba(0,0,0,.35)';g.shadowBlur=14;g.shadowOffsetY=6;g.drawImage(sc2,-sw2/2,-sh2/2);g.restore();
 /* postmark */
 const pmx=sx0+4,pmy=sy0+sh2-6,R=70,ink='rgba(23,18,46,.78)';g.save();g.translate(pmx,pmy);g.rotate(-.22);g.strokeStyle=ink;g.fillStyle=ink;g.lineWidth=4;
 g.beginPath();g.arc(0,0,R,0,7);g.stroke();g.lineWidth=2;g.beginPath();g.arc(0,0,R-12,0,7);g.stroke();
 const when=(tWhen(t)||dfmtShort(t.a)).replace('~ ','').toUpperCase();g.textAlign='center';g.textBaseline='middle';g.font='900 19px Inter,system-ui,sans-serif';g.fillText(when.slice(0,14),0,4);
 g.font='800 12px Inter,system-ui,sans-serif';const top='WORLDMAP · '+String(t.name).toUpperCase().slice(0,14);[...top].forEach((ch,k,arr)=>{const a=-Math.PI/2+(k-(arr.length-1)/2)*.15;g.save();g.rotate(a+Math.PI/2);g.fillText(ch,0,-(R-24));g.restore()});
 g.lineWidth=3.5;for(let k=0;k<4;k++){g.beginPath();for(let x=-R-70;x<=-R-6;x+=4){const y=-30+k*20+Math.sin(x/10)*6;x==-R-70?g.moveTo(x,y):g.lineTo(x,y)}g.stroke()}
 g.restore();
}
function dfmtShort(s){const MN=['JAN','FEB','MÄR','APR','MAI','JUN','JUL','AUG','SEP','OKT','NOV','DEZ'];return `${+s.slice(8,10)} ${MN[+s.slice(5,7)-1]} ${s.slice(0,4)}`}
function pcInit(T){const w=document.getElementById('pcw');if(!w)return;const t=pcTrip(T);pcDraw(t);
 if(!TR&&D.days.some(r=>r[6]==t.id))need('tracks').then(()=>{if(DASH.pc==t.id)pcDraw(t)}).catch(()=>{});
 const go=id=>{DASH.pc=id;PCS.flip=false;pcRender(T)},idx=()=>T.findIndex(x=>x.id==DASH.pc);
 const card=document.getElementById('pcard');let sx=null,sy=0;
 card.addEventListener('pointerdown',e=>{sx=e.clientX;sy=e.clientY});
 card.addEventListener('pointerup',e=>{if(sx==null)return;const dx=e.clientX-sx,dy=e.clientY-sy;sx=null;
  if(Math.abs(dx)>50&&Math.abs(dx)>Math.abs(dy)){const i=idx()+(dx<0?1:-1);if(i>=0&&i<T.length)go(T[i].id);return}
  if(Math.abs(dx)<8&&Math.abs(dy)<8){PCS.flip=!PCS.flip;card.classList.toggle('flip',PCS.flip)}});
 card.addEventListener('keydown',e=>{if(e.key=='Enter'||e.key==' '){e.preventDefault();PCS.flip=!PCS.flip;card.classList.toggle('flip',PCS.flip)}
  if(e.key=='ArrowRight'||e.key=='ArrowLeft'){const i=idx()+(e.key=='ArrowRight'?1:-1);if(i>=0&&i<T.length){go(T[i].id);document.getElementById('pcard')?.focus()}}});
 w.querySelectorAll('[data-pc]').forEach(b=>b.onclick=()=>{const a=b.dataset.pc,i=idx();
  if(a=='prev'&&i>0)go(T[i-1].id);if(a=='next'&&i<T.length-1)go(T[i+1].id);
  if(a=='rnd'&&T.length>1){let j=i;while(j==i)j=Math.floor(Math.random()*T.length);go(T[j].id)}
  if(a=='flip'){PCS.flip=!PCS.flip;card.classList.toggle('flip',PCS.flip)}
  if(a=='png'){const cv=document.getElementById('pccv');cv.toBlob(bl=>{if(!bl)return;const u=URL.createObjectURL(bl),l=document.createElement('a');l.href=u;l.download='postkarte-'+String(t.name).toLowerCase().replace(/[^a-z0-9äöü]+/g,'-').slice(0,40)+'.png';document.body.appendChild(l);l.click();l.remove();setTimeout(()=>URL.revokeObjectURL(u),2000)},'image/png')}});
 const sel=document.getElementById('dpc-sel');if(sel)sel.onchange=()=>go(+sel.value)}
function pcRender(T){const w=document.getElementById('pcw');if(!w)return;const n=document.createElement('div');n.innerHTML=tPostcard(T);w.replaceWith(n.firstElementChild);pcInit(T)}

function tCalendar(T){const ys=[...new Set(T.map(t=>t.y))].sort();if(!ys.length)return '<div class="empty">Noch keine Reisen.</div>';
 if(!ys.includes(DASH.year))DASH.year=ys[ys.length-1];const Y=DASH.year,day={};
 for(const t of T){let d=dateOf(t.a);const e=dateOf(t.b);while(d<=e){const k=d.toISOString().slice(0,10);if(k.startsWith(Y+''))day[k]=t;d=new Date(d.getTime()+864e5)}}
 const jan1=Date.UTC(Y,0,1),wd0=(new Date(jan1).getUTCDay()+6)%7,n=(Y%4==0&&(Y%100||Y%400==0))?366:365,c=11,g=2;let cells='';
 for(let i=0;i<n;i++){const d=new Date(jan1+i*864e5),k=d.toISOString().slice(0,10),col=Math.floor((i+wd0)/7),row=(d.getUTCDay()+6)%7,t=day[k];
  cells+=`<rect x="${26+col*(c+g)}" y="${14+row*(c+g)}" width="${c}" height="${c}" rx="2.5" fill="${t?dCol(t.w):'var(--soft)'}"${t?` data-trip="${t.id}"`:''}><title>${k}${t?' · '+esc(t.name):''}</title></rect>`}
 const mon=['Jan','Feb','Mär','Apr','Mai','Jun','Jul','Aug','Sep','Okt','Nov','Dez'].map((m,i)=>{const col=Math.floor((Math.round((Date.UTC(Y,i,1)-jan1)/864e5)+wd0)/7);return `<text x="${26+col*(c+g)}" y="9" font-size="9" fill="var(--mute)">${m}</text>`}).join('');
 const wl=['Mo','','Mi','','Fr','',''].map((l,i)=>l?`<text x="0" y="${23+i*(c+g)}" font-size="9" fill="var(--mute)">${l}</text>`:'').join('');
 const nd=Object.keys(day).length,who=[...new Set(Object.values(day).map(t=>t.w))];
 return `${dOpts().year?'':`<div class="dyears">${ys.map(y=>`<button class="${y==Y?'on':''}" data-y="${y}">${y}</button>`).join('')}</div>`}
  <div class="dcal"><svg viewBox="0 0 ${26+54*(c+g)} ${14+7*(c+g)}" role="img" aria-label="${nd} Reisetage ${Y}">${mon}${wl}${cells}</svg></div>
  <p class="dmute">${nd} von ${n} Tagen unterwegs (${Math.round(nd/n*100)} %)</p><div class="dleg">${who.map(w=>`<span><i style="background:${dCol(w)}"></i>${esc(w)}</span>`).join('')}</div>`}

function tLanes(T){const ps=(D.persons||[]).filter(p=>!SEL||members(SEL).includes(p));if(!T.length||!ps.length)return '<div class="empty">Keine Personen oder Reisen.</div>';
 const y0=Math.min(...T.map(t=>t.y)),y1=Math.max(...T.map(t=>t.y))+1,W=1240,L=80,lh=34,H=lh*ps.length+26,X=s=>{const d=dateOf(s);return L+((d.getUTCFullYear()+(d-Date.UTC(d.getUTCFullYear(),0,1))/31536e6)-y0)/(y1-y0)*(W-L-8)};
 let g='';ps.forEach((p,i)=>{g+=`<text x="0" y="${i*lh+22}" font-size="12" font-weight="700" fill="var(--ink)">${esc(p.slice(0,10))}</text><line x1="${L}" x2="${W-8}" y1="${i*lh+18}" y2="${i*lh+18}" stroke="var(--line)" stroke-width="2"/>`});
 for(let y=y0;y<=y1;y++){const x=L+(y-y0)/(y1-y0)*(W-L-8);g+=`<line x1="${x}" x2="${x}" y1="4" y2="${H-18}" stroke="var(--line)" stroke-dasharray="2 4"/>${(y<y1)&&(y1-y0<=14||y%2==0)?`<text x="${x+2}" y="${H-4}" font-size="10" fill="var(--mute)">${y}</text>`:''}`}
 for(const t of T){const ms=members(t.w).filter(p=>ps.includes(p));if(!ms.length)continue;const x=X(t.a),w=Math.max(4,X(t.b)-x),rows=ms.map(p=>ps.indexOf(p)).sort((a,b)=>a-b),col=dCol(t.w);
  if(rows.length>1)g+=`<line x1="${x+w/2}" x2="${x+w/2}" y1="${rows[0]*lh+18}" y2="${rows[rows.length-1]*lh+18}" stroke="${col}" stroke-width="2.5" opacity=".7"/>`;
  for(const r of rows)g+=`<rect x="${x}" y="${r*lh+11}" width="${w}" height="14" rx="4" fill="${col}" data-trip="${t.id}"><title>${esc(t.name)} · ${dRange(t)} · ${esc(t.w)}</title></rect>`}
 return `<div class="dscroll"><svg viewBox="0 0 ${W} ${H}" style="min-width:640px" role="img" aria-label="Zeitstrahl pro Person">${g}</svg></div>`}

function tWheel(T){const mon=Array.from({length:12},()=>({}));for(const t of T){const m=+t.a.slice(5,7)-1,k=dMain(t);mon[m][k]=(mon[m][k]||0)+Math.max(1,t.n||0)}
 const tot=mon.map(o=>Object.values(o).reduce((a,b)=>a+b,0)),mx=Math.max(1,...tot),cx=110,cy=110,r0=34,r1=96;let g='';
 const ML=['J','F','M','A','M','J','J','A','S','O','N','D'];
 mon.forEach((o,i)=>{const a0=(i/12)*2*Math.PI-Math.PI/2+.04,a1=((i+1)/12)*2*Math.PI-Math.PI/2-.04;let r=r0;
  const arc=(ra,rb,col,tt)=>{const p=(rr,a)=>`${(cx+rr*Math.cos(a)).toFixed(1)} ${(cy+rr*Math.sin(a)).toFixed(1)}`;return `<path d="M${p(ra,a0)} A${ra} ${ra} 0 0 1 ${p(ra,a1)} L${p(rb,a1)} A${rb} ${rb} 0 0 0 ${p(rb,a0)}Z" fill="${col}"><title>${tt}</title></path>`};
  g+=arc(r0,r1,'var(--soft)','');for(const m of MODES){if(!o[m])continue;const dr=o[m]/mx*(r1-r0);g+=arc(r,r+dr,MCOL[m],`${ML[i]}: ${o[m]} Nächte · ${MNAME[m]}`);r+=dr}
  const am=(a0+a1)/2;g+=`<text x="${(cx+(r1+10)*Math.cos(am)).toFixed(1)}" y="${(cy+(r1+10)*Math.sin(am)+4).toFixed(1)}" text-anchor="middle" font-size="10" font-weight="700" fill="var(--mute)">${ML[i]}</text>`});
 const top=tot.indexOf(Math.max(...tot)),MN=['Januar','Februar','März','April','Mai','Juni','Juli','August','September','Oktober','November','Dezember'];
 return `<div class="dwheel"><svg viewBox="0 0 220 220" width="220" height="220" role="img" aria-label="Reisenächte pro Monat">${g}<text x="${cx}" y="${cy+4}" text-anchor="middle" font-size="11" font-weight="800" fill="var(--ink)">${T.length?MN[top].slice(0,3):''}</text></svg>
 <div><p>${T.length?`Am meisten unterwegs im <b>${MN[top]}</b> (${tot[top]} Nächte über alle Jahre).`:''}</p><div class="dleg">${MODES.filter(m=>mon.some(o=>o[m])).map(m=>`<span><i style="background:${MCOL[m]}"></i>${MNAME[m]}</span>`).join('')}</div></div></div>`}

function tFavs(){const P=D.places.filter(p=>placeSel(p)&&p[7]!='Home'&&p[7]!='Work'&&p[3]>=2).sort((a,b)=>b[4]-a[4]).slice(0,14);
 if(!P.length)return '<div class="empty">Noch keine Orte mit mehreren Besuchen.</div>';const mx=Math.max(...P.map(p=>p[4]));
 return `<div class="dfavs">${P.map(p=>{const s=Math.round(34+Math.sqrt(p[4]/mx)*58),ring=Math.min(8,1+Math.log2(p[3]));const col=p[8]>=0&&tripById[p[8]]?dCol(tripById[p[8]].w):'#8B3DFF';
  return `<div class="dfav" title="${esc(p[9])}: ${p[3]} Besuche, ${p[4]} Tage"><i style="width:${s}px;height:${s}px;--c:${col};border-width:${ring.toFixed(1)}px"><b>${p[4]}</b></i><span>${esc(p[9])}</span><em>${p[3]}× besucht</em></div>`}).join('')}</div>`}

function tCo2(T){const by={};for(const t of T){const o=by[t.y]=by[t.y]||{};for(const m in t.k||{})o[m]=(o[m]||0)+t.k[m]}
 const ys=Object.keys(by).sort();if(!ys.length)return '<div class="empty">Noch keine Reisen.</div>';
 const tot=ys.map(y=>Object.values(by[y]).reduce((a,b)=>a+b,0)),mx=Math.max(1,...tot),bw=Math.max(10,Math.min(34,560/ys.length-6)),W=ys.length*(bw+6)+40,H=170;let g='';
 ys.forEach((y,i)=>{let yy=H-20;const x=36+i*(bw+6);for(const m of MODES){const v=by[y][m]||0;if(!v)continue;const h=v/mx*(H-40);yy-=h;g+=`<rect x="${x}" y="${yy.toFixed(1)}" width="${bw}" height="${Math.max(1,h-1).toFixed(1)}" rx="2" fill="${MCOL[m]}"><title>${y} · ${MNAME[m]}: ${fmt(v)} km</title></rect>`}
  g+=`<text x="${x+bw/2}" y="${H-6}" text-anchor="middle" font-size="9.5" fill="var(--mute)">${String(y).slice(2)}</text>`});
 g+=`<text x="0" y="16" font-size="9.5" fill="var(--mute)">${fmt(mx)} km</text><line x1="34" x2="${W}" y1="20" y2="20" stroke="var(--line)" stroke-dasharray="2 4"/>`;
 const kg=T.reduce((s,t)=>s+Object.entries(t.k||{}).reduce((a,[m,v])=>a+v*(CO2[m]||0),0),0),hours=T.reduce((s,t)=>s+Object.entries(t.k||{}).reduce((a,[m,v])=>a+v/({fly:750,road:75,rail:90,ferry:30,foot:4.5}[m]||60),0),0);
 return `<div class="dscroll"><svg viewBox="0 0 ${W} ${H}" style="min-width:${Math.min(W,560)}px" role="img" aria-label="Kilometer pro Jahr">${g}</svg></div>
 <div class="dk sm"><div><b>${fmt(kg/1000)} t</b><span>CO₂ geschätzt pro Person</span></div><div><b>${fmt(hours)} h</b><span>unterwegs (Fahrzeit grob)</span></div><div><b>${fmt(T.reduce((s,t)=>s+t.km,0)/Math.max(1,ys.length))} km</b><span>pro Jahr mit Reisen</span></div></div>`}

function tBlank(){if(!RG.list)return '<div class="empty">Regionen werden geladen …</div>';const A=aggReg(),tot={},seen={};
 for(const r of RG.list){tot[r.a3]=(tot[r.a3]||0)+1;if(A.has(r.id))seen[r.a3]=(seen[r.a3]||0)+1}
 const cs=Object.keys(seen).sort((a,b)=>(b==RG.cc)-(a==RG.cc)||seen[b]/tot[b]-seen[a]/tot[a]).slice(0,12);if(!cs.length)return '<div class="empty">Noch keine Regionen besucht.</div>';
 return `<div class="dblank">${cs.map(c=>{const p=seen[c]/tot[c];return `<div><span>${esc(RG.countries[c]||c)}</span><div class="dbar"><i style="width:${(p*100).toFixed(1)}%"></i></div><em>${seen[c]} / ${tot[c]}</em></div>`}).join('')}</div>
 <p class="dmute">Fehlende Regionen siehst du auf der Karte „Regionen“.</p>`}

/* ---------------------------------------------------------------- layout */
function buildDash(){const box=document.getElementById('dashb');if(!box||!D)return;const O=dOpts();let T=dTrips();const allY=[...new Set(T.map(t=>t.y))].sort();
 if(O.year){if(!allY.includes(DASH.year))DASH.year=allY[allY.length-1];T=T.filter(t=>t.y==DASH.year)}
 const order=dOrder(),on=new Set(order);document.getElementById('dash').classList.toggle('kiosk',!!O.kiosk);
 document.getElementById('dash-presets').innerHTML=DPRESETS.concat([DOWN]).map(([k,n,d,,,ico,col])=>`<button class="dpre${dPreset()==k?' on':''}" role="radio" aria-checked="${dPreset()==k}" data-p="${k}" style="--c:${col}"><span class="dpi" aria-hidden="true">${ico}</span><b>${n}</b><small>${esc(d)}</small></button>`).join('');
 document.querySelectorAll('#dash-presets button').forEach(b=>b.onclick=()=>{DASH.preset=b.dataset.p;try{localStorage.setItem('wm-dash-preset',DASH.preset)}catch(e){}buildDash()});
 const pdEl=document.getElementById('dash-pdesc');pdEl.hidden=!O.year;pdEl.innerHTML=O.year?`<span class="dlab">Jahr</span><span class="dyears">${allY.map(y=>`<button class="${y==DASH.year?'on':''}" data-y="${y}">${y}</button>`).join('')}</span>`:'';
 const fn={kpi:tKpi,earth:tEarth,records:tRecords,passport:tPassport,postcard:tPostcard,calendar:tCalendar,lanes:tLanes,wheel:tWheel,favs:tFavs,co2:tCo2,blank:tBlank};
 const wide={kpi:1,calendar:1,lanes:1};
 box.innerHTML=order.map(k=>DTILES.find(t=>t[0]==k)).map(([k,ti,info])=>{let body='';try{body=fn[k](T)}catch(e){body='<div class="empty">Diese Kachel konnte nicht gezeichnet werden.</div>';console.error(e)}
  return `<section class="dtile${wide[k]?' wide':''}" id="dt-${k}"><div class="dth"><h3>${ti}</h3><button class="info" aria-expanded="false" aria-controls="dti-${k}" aria-label="Was zeigt diese Kachel?">i</button></div><p class="dinfo" id="dti-${k}" hidden>${info}</p>${body}</section>`}).join('')||'<div class="empty">Alle Kacheln sind ausgeblendet. Mit „Anpassen“ oben wieder einblenden.</div>';
 box.querySelectorAll('.dth .info').forEach(b=>b.onclick=()=>{const p=document.getElementById(b.getAttribute('aria-controls'));p.hidden=!p.hidden;b.setAttribute('aria-expanded',String(!p.hidden))});
 pcInit(T);
 document.querySelectorAll('#dash .dyears button').forEach(b=>b.onclick=()=>{DASH.year=+b.dataset.y;buildDash()});
 box.querySelectorAll('[data-trip]').forEach(el=>el.addEventListener('click',()=>{DASH.pc=+el.dataset.trip;PCS.flip=false;const pc=document.getElementById('dt-postcard');if(!pc)return;pcRender(T);pc.scrollIntoView({behavior:'smooth',block:'nearest'})}));
 document.getElementById('dash-sub').textContent=(SEL?SEL+' · ':'')+(O.year?DASH.year+' · ':'')+T.length+' '+(T.length==1?'Reise':'Reisen');
 clearInterval(DASH.kt);if(O.kiosk&&T.length>1&&!matchMedia('(prefers-reduced-motion: reduce)').matches)DASH.kt=setInterval(()=>{if(TAB!='dash'||document.hidden)return;const i=T.findIndex(t=>t.id==DASH.pc);DASH.pc=T[(i+1)%T.length].id;PCS.flip=false;pcRender(T)},15000);
 if(!RG.list)need('reg').then(()=>{if(TAB=='dash')buildDash()}).catch(()=>{});
}
function dashTiles(){const m=document.getElementById('dash-menu');if(!m.hidden){m.hidden=true;return}if(dPreset()!='own')DASH.tiles=new Set(dOrder());const on=dTilesOn();
 m.innerHTML=DTILES.map(([k,t])=>`<label><input type="checkbox" data-k="${k}" ${on.has(k)?'checked':''}> ${t}</label>`).join('');m.hidden=false;
 m.querySelectorAll('input').forEach(i=>i.onchange=()=>{i.checked?on.add(i.dataset.k):on.delete(i.dataset.k);dSaveTiles();DASH.preset='own';try{localStorage.setItem('wm-dash-preset','own')}catch(e){}buildDash()})}
function dashEnter(){document.getElementById('dash-tiles').onclick=dashTiles;document.querySelector('.app').hidden=true;const d=document.getElementById('dash');d.hidden=false;
 const wb=document.getElementById('whobar');document.getElementById('dash-who').appendChild(wb);buildDash()}
function dashLeave(){clearInterval(DASH.kt);const d=document.getElementById('dash');if(d.hidden)return;d.hidden=true;document.querySelector('.app').hidden=false;
 const wb=document.getElementById('whobar'),side=document.querySelector('.side');side.insertBefore(wb,side.firstChild);document.getElementById('dash-menu').hidden=true}
window.__T={};
sizeCV();
setInterval(()=>{if(!document.hidden)badge()},60000);
window.__wm={AN,V,MX,MY,full,get D(){return D},get TAB(){return TAB}};
Promise.all([loadJSON('api/atlas/core'),loadJSON('base.json?v=__WMV__'),loadJSON('api/atlas/labels'),loadJSON('api/style').catch(()=>null)]).then(([c,b,l,st])=>{
 if(st){SDEF=st.default;PRE.list=st.presets||[];PRE.def=st.preset_default??-1;const dp=PRE.list[PRE.def];if(!EMBED&&dp&&!sameStyle(dp.style,st.style)){st.style=dp.style;fetch('api/style/presets/'+(PRE.def+1),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'load'})}).catch(()=>{})}applyStyle(st.style);pickTheme();themeBtn();presetsUI()}
 D=c;LAB=l;prepBase(b);initData();badge();D.trips.forEach(t=>tripById[t.id]=t);
 const d0=dateOf(D.days[0][0]);D.days.forEach((r,i)=>{const d=new Date(d0.getTime()+i*864e5);const who=r[6]>=0?tripById[r[6]].w:'Alltag';dayInfo[i]={y:d.getUTCFullYear(),dow:d.getUTCDay(),who,cat:r[6]>=0?'Reise':'Alltag'}});
 whoBar();emptyState();const h=(location.hash||'').slice(1);setTab(NEEDS[h]?h:'reisen');
}).catch(()=>{$('load').textContent='Daten konnten nicht geladen werden.'});
}
