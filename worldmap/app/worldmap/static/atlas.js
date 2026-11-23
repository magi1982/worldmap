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
function themeBtn(){const b=document.getElementById('ztheme');if(b){b.textContent=THEME=='dark'?'☀':'☾';b.title=b.ariaLabel=THEME=='dark'?'Heller Modus':'Dunkler Modus'}}
const BASEMAPS={paper:{sea:'#D7E4EA',land:'#FBF6EC',prov:'#EADFCB',rivS:'#C3D5DE',rivB:'#AFC7D4',lake:'#C9DCE4',lakeLine:'#A9C2CF',border:'#BFAE8E',text:'#5A4632',halo:'rgba(251,246,236,.92)',base:[251,246,236]},
 mono:{sea:'#E1E5EA',land:'#F8F8F8',prov:'#EBEBEB',rivS:'#D4D9DF',rivB:'#C6CDD5',lake:'#D6DBE1',lakeLine:'#BEC5CD',border:'#B4B8BF',text:'#4A4A55',halo:'rgba(248,248,248,.92)',base:[248,248,248]}};
function pickTheme(){let t='auto';try{t=localStorage.getItem('wm-theme')||(STYLE&&STYLE.map.theme)||'auto'}catch(e){}const dark=t=='dark'||(t=='auto'&&matchMedia('(prefers-color-scheme: dark)').matches);THEME=dark?'dark':'light';MC=THEMES[THEME];const bm=STYLE&&STYLE.map.basemap;if(!dark&&BASEMAPS[bm])MC={...THEMES.light,...BASEMAPS[bm]};document.documentElement.dataset.theme=THEME}
pickTheme();
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
function renderTile(z,x,y,fn){const n=2**z,St=TS*n,f=TDPR;const c=document.createElement('canvas');c.width=c.height=Math.round(TS*f);const g=c.getContext('2d');const bb=[x/n,y/n,(x+1)/n,(y+1)/n];const oc=ctx,oS=V.S;ctx=g;V.S=St;V.tf=f;g.setTransform(f*St,0,0,f*St,-x*TS*f,-y*TS*f);g.fillStyle=MC.sea;g.fillRect(bb[0],bb[1],1/n,1/n);try{fn(bb)}finally{ctx=oc;V.S=oS}return c}
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
function drawBase(opt={}){
 const S=V.S;
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
 const chip=(n,ico)=>`<button class="chip ${SEL==n?'on':''}" style="--c:${n?WCOL[n]||'#8B3DFF':MC.strong}" data-n="${esc(n||'')}" aria-pressed="${SEL==n}"><i></i>${ico}${esc(n||'Alle')}</button>`;
 box.innerHTML='<div class="wb-t">ANZEIGEN FÜR <span class="r"><label class="aswitch" title="Flugzeuge, Züge und Autos bewegen sich"><input type="checkbox" id="animT"'+(animWanted()?' checked':'')+'><span></span>ANIMATION</label><a href="app.html#people" title="Personen und Gruppen bearbeiten">bearbeiten</a></span></div><div class="chips">'+chip(null,'')+ps.map(n=>chip(n,'<span class="wi" aria-hidden="true">👤</span>')).join('')+gs.map(n=>chip(n,'<span class="wi" aria-hidden="true">👥</span>')).join('')+'</div>';
 box.querySelectorAll('.chip').forEach(b=>b.onclick=()=>setSel(b.dataset.n||null));const at=$('animT');if(at)at.onchange=()=>{try{localStorage.setItem('wm-anim',at.checked?'1':'0')}catch(e){}full();animRestart()}}
function setSel(n){SEL=SEL==n?null:n;SELV++;
 R.w=new Set(SEL?WHO.filter(w=>tripSel({w})):WHO);
 if(TR){for(let i=0;i<TR.length;i++)TR[i].on=trackSel(i);byDay={};TR.forEach((l,i)=>{if(l.on)(byDay[l.d]=byDay[l.d]||[]).push(i)})}
 O.pl=null;Z.cum=null;Z.weeks=null;Z.tr=null;Z.boxes.clear();RG.groups=null;RG.agg=null;
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
 const pairs=new Map();if(R.m.has('fly'))for(const t of on){for(const [x,y,ia,ib] of t.fl){const A=ia?'ap:'+ia:ptGroup(x,t),Bg=ib?'ap:'+ib:ptGroup(y,t);if(!A||!Bg||A==Bg)continue;const hm=q=>q=='home'||(q.startsWith('ap:')&&D.airports[q.slice(3)]&&km2(D.airports[q.slice(3)][0],D.airports[q.slice(3)][1],HOME[0],HOME[1])<150);const k=[A,Bg].sort((p,q)=>hm(q)-hm(p)||p.localeCompare(q)).join('>');let e=pairs.get(k);if(!e){e={k,ws:new Set(),g:new Set()};pairs.set(k,e)}e.ws.add(t.w);if(t.g&&!t.gps)e.g.add(t.g)}}
 RC={own:out,far,est,near,pairs:[...pairs.values()],on,onIds,st:{},ver:(RC?RC.ver:0)+1};
}
/* airports at the ends of flight arcs: a small tag with the IATA code */
function apMarks(keys){const S=V.S;if(S<1500)return;const seen=new Set();ctx.font='800 10.5px Inter,system-ui,sans-serif';ctx.textBaseline='middle';
 for(const k of keys){if(!k.startsWith('ap:')||seen.has(k))continue;seen.add(k);const code=k.slice(3),a=D.airports[code];if(!a)continue;const [x,y]=toS(MX(a[1]),MY(a[0]));if(x<-30||y<-30||x>V.W+30||y>V.H+30)continue;
  const w=ctx.measureText(code).width+20;ctx.fillStyle=MC.land;ctx.strokeStyle=MCOL.fly;ctx.lineWidth=1.4;ctx.beginPath();ctx.roundRect(x+6,y-9,w,18,9);ctx.fill();ctx.stroke();
  ctx.fillStyle=MCOL.fly;ctx.fillText('✈',x+10,y+.5);ctx.fillStyle=MC.strong;ctx.fillText(code,x+21,y+.5);ctx.beginPath();ctx.arc(x,y,3.2,0,7);ctx.fillStyle=MCOL.fly;ctx.fill();ctx.strokeStyle=MC.ring;ctx.lineWidth=1.5;ctx.stroke();placed.push([x+6,y-9,x+6+w,y+9])}
 ctx.textBaseline='alphabetic'}
function gpos(g){if(g=='home')return [MX(HOME[1]),MY(HOME[0])];if(g.startsWith('ap:')){const a=D.airports[g.slice(3)];return [MX(a[1]),MY(a[0])]}if(g.startsWith('p:')){const [a,b]=g.slice(2).split(',').map(Number);return [MX(b),MY(a)]}const G=D.groups.find(x=>x[0]==g);return [MX(G[3]),MY(G[2])]}
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
 const AR=STYLE?STYLE.areas:{show:true,opacity:1,outline:true};ctx.globalAlpha=AR.opacity;
 for(const cells of (!AR.show||S>=150000?[]:ZOOMED?RC.own.slice(0,R.color=='w'?1:0):RC.own)){const own=areaLayer(cells,S),r0=cells._r;
  if(AR.outline)for(const q in own){ctx.fillStyle=col[q];ctx.beginPath();const r=r0+1.4/S;for(const [x,y] of own[q]){ctx.moveTo(x+r,y);ctx.arc(x,y,r,0,7)}ctx.fill()}
  for(const q in own){ctx.fillStyle=tint(col[q],q=='Alltag'?.2:.3);ctx.beginPath();for(const [x,y] of own[q]){ctx.moveTo(x+r0,y);ctx.arc(x,y,r0,0,7)}ctx.fill()}
 }
 ctx.globalAlpha=1;
 // far routes
 ctx.lineJoin='round';ctx.lineCap='round';
 const lw=Math.max(1.6,Math.min(3.2,S/6000))/S;
 const vb=[V.cx-V.W/2/S,V.cy-V.H/2/S,V.cx+V.W/2/S,V.cy+V.H/2/S];
 tileDraw(RC.st,li=>{const l=TR[li],r=D.days[l.d];if(!l.on)return null;if(!r||r[6]<0)return null;const t=tripById[r[6]];if(!RC.onIds.has(t.id))return null;if(!t.g&&!ZOOMED)return null;const m=TCLS[l.c];if(!R.m.has(m))return null;return (R.color=='w'?WCOL[t.w]:MCOL[m])+'|'+m+(t.g?'|f':'|n')},k=>k.endsWith('|f')?1:0,k=>{const f=k.endsWith('|f'),m=k.slice(8,-2);ctx.strokeStyle=k.slice(0,7);ctx.lineWidth=(f?lw:lw*.75)*SM(m).width;setDash(m,V.S);ctx.globalAlpha=1},bb);ctx.setLineDash([]);ctx.globalAlpha=1;
 drawGaps(g=>{const r=D.days[g[0]];if(!r||r[6]<0||!gapSel(g))return null;const t=tripById[r[6]];if(!RC.onIds.has(t.id)||(!t.g&&!ZOOMED))return null;const m=TCLS[g[1]];if(!R.m.has(m))return null;return R.color=='w'?WCOL[t.w]:MCOL[m]},lw,bb)}
function drawR(){
 TKEY='R'+RC.ver+(V.S>=150000?'Z':V.S>=55000?'z':'');drawTiles(contentR);worldT();const S=V.S;ctx.globalAlpha=1;
 for(const [la,lo,rk,c] of RC.est){const r=rk/(40075*Math.cos(la*Math.PI/180));ctx.beginPath();ctx.arc(MX(lo),MY(la),r,0,7);ctx.fillStyle=tint(c,.82);ctx.globalAlpha=.55;ctx.fill();ctx.globalAlpha=1;ctx.setLineDash([1/S,5/S]);ctx.lineCap='round';ctx.strokeStyle=c;ctx.lineWidth=2.8/S;ctx.stroke();ctx.setLineDash([])}
 // flights
 if(!(AN.on&&STYLE&&STYLE.anim.planes))for(const e of RC.pairs){const [A,Bg]=e.k.split('>');const [x1,y1]=gpos(A),[x2,y2]=gpos(Bg);const a=arcPts(x1,y1,x2,y2,A=='home'?.2:.18);strokeArc(a,R.color=='w'?WHO.filter(w=>e.ws.has(w)).map(w=>WCOL[w]):[MCOL.fly],2.4,8,6)}
 endWorld();placed.length=0;usedNames.clear();
 homeMark();apMarks(RC.pairs.flatMap(e=>e.k.split(">")));
 // destinations
 RC.mbox=null;let off=null;
 for(const G of D.groups){const [g,name,la,lo,an,fs,major,gkm]=G;const ts=RC.on.filter(t=>t.g==g);if(!ts.length)continue;const [x,y]=toS(MX(lo),MY(la));if(x<-80||y<-40||x>V.W+80||y>V.H+40){if(gkm>1500&&(!off||gkm>off[0][7]))off=[G,ts];continue}
  const cs=R.color=='w'?WHO.filter(w=>ts.some(t=>t.w==w)).map(w=>WCOL[w]):[...new Set(ts.flatMap(t=>t.m).filter(m=>R.m.has(m)))].map(m=>MCOL[m]);const r=major?7.5:5.5;pieS(x,y,r,cs);
  lbl(name,an=='end'?x-r-6:an=='middle'?x:x+r+6,an=='middle'?y-r-6:y+5,fs,major?780:650,major?MC.strong:MC.text,an=='end'?'right':an=='middle'?'center':'left',4.5,true)}
 // near trips
 const near={};for(const t of RC.on){if(t.g||t.nopos)continue;const k=t.name;(near[k]=near[k]||{name:k,p:t.p,ts:[]}).ts.push(t)}
 const ns=Object.values(near).sort((a,b)=>b.ts.length-a.ts.length);
 for(const q of ns){const [x,y]=toS(MX(q.p[1]),MY(q.p[0]));if(x<-20||y<-20||x>V.W+20||y>V.H+20)continue;const r=Math.min(9,3+Math.sqrt(q.ts.length)*1.3)*(S>40000?1:.75);const cs=R.color=='w'?WHO.filter(w=>q.ts.some(t=>t.w==w)).map(w=>WCOL[w]):[...new Set(q.ts.flatMap(t=>t.m).filter(m=>R.m.has(m)))].map(m=>MCOL[m]);pieS(x,y,r,cs);q.sx=x;q.sy=y;q.r=r;if(S>45000)lbl(q.name,x+r+4,y+4,12,650,MC.text)}
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
 openDetail(`<h3>${esc(name)}</h3><div class="dsub">${ts.length} ${ts.length==1?'Reise':'Reisen'} · ${esc(n)} Nächte · ${fmt(km)} km · ${esc(ts[0]?ts[0].c:'')}</div>`+ts.map(t=>`<div class="trip"><div class="s" style="background:${WCOL[t.w]}"></div><div><div class="t1">${dfmt(t.a)}${t.n?' – '+dfmt(t.b):''}</div><div class="t2"><span class="pill" style="background:${tint(WCOL[t.w],.18)}">${esc(t.w)}</span>${t.m.map(m=>`<span class="pill">${MNAME[m]}</span>`).join('')}${t.n?t.n+(t.n==1?' Nacht':' Nächte'):'Tagesausflug'} · ${fmt(t.km)} km${t.name!=name?' · '+esc(t.name):''}${t.approx?' · geschätzt':''} · <a href="#" class="edit" data-id="${t.dbid}">bearbeiten</a></div></div></div>`).join(''));$('detail').querySelectorAll('a.edit').forEach(a=>a.onclick=e=>{e.preventDefault();editTrip(+a.dataset.id)})}
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
function drawGaps(colOf,lw,bb){const st=STYLE?STYLE.map.gaps:'dotted';if(st=='open'||!D.gaps)return;const S=V.S,by=new Map();
 for(const g of D.gaps){const c=colOf(g);if(!c)continue;const x1=MX(g[3]),y1=MY(g[2]),x2=MX(g[5]),y2=MY(g[4]);if(Math.max(x1,x2)<bb[0]||Math.min(x1,x2)>bb[2]||Math.max(y1,y2)<bb[1]||Math.min(y1,y2)>bb[3])continue;let p=by.get(c);if(!p){p=new Path2D();by.set(c,p)}p.moveTo(x1,y1);p.lineTo(x2,y2)}
 ctx.save();ctx.lineCap='round';ctx.setLineDash(st=='straight'?[]:[.01/S,Math.max(3.2,lw*S*2.4)/S]);ctx.lineWidth=lw*(st=='straight'?.7:1.15);ctx.globalAlpha=st=='straight'?.55:.8;for(const [c,p] of by){ctx.strokeStyle=c;ctx.stroke(p)}ctx.restore()}
function contentS(bb){
 drawBase();const S=V.S,lw=S<300000?1/(S*(V.tf||1)):Math.min(2.4,S/250000)/S;
 ctx.lineWidth=lw;ctx.lineJoin='round';ctx.lineCap='round';ctx.globalAlpha=1;
 tileDraw(SP.st,li=>{const l=TR[li];return l.on&&SP.modes.has(TCLS[l.c])&&dayOk(l.d)?keyS(l)+'|'+TCLS[l.c]:null},kk=>{const k=kk.split('|')[0];return SP.color=='m'?['foot','road','rail'].indexOf(k):SP.color=='w'?WORDER().indexOf(k):+k},kk=>{const [k,m]=kk.split('|');ctx.strokeStyle=S<300000?colS(k):tint(colS(k),.85);ctx.lineWidth=lw*SM(m).width;setDash(m,S)},bb);ctx.setLineDash([]);ctx.globalAlpha=1;
 drawGaps(g=>SP.modes.has(TCLS[g[1]])&&dayOk(g[0])&&gapSel(g)?colS(keyS({d:g[0],c:g[1]})):null,lw,bb)}
function drawS(){
 TKEY='S'+SP.ver;drawTiles(contentS);worldT();const S=V.S;
 ctx.globalAlpha=S>40000?.4:.75;if(!(AN.on&&STYLE&&STYLE.anim.planes))for(const [a,c] of SP.fl)strokeArc(a,[c],S>40000?1.3:1.8,7,5);
 ctx.globalAlpha=1;endWorld();placed.length=0;usedNames.clear();homeMark();if(SP.modes.has('fly'))apMarks((SP.flKeys=SP.flKeys||D.flights.flatMap(f=>[f[5]?'ap:'+f[5]:'',f[6]?'ap:'+f[6]:''])).filter(Boolean));drawPlaceLabels();
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
 const fade=O.day!=null?.3:1,zf=Math.max(.55,Math.min(1.7,Math.log2(S/8000)/4));
 for(const p of O.pl){const [x,y]=toS(MX(p[1]),MY(p[0]));if(x<-30||y<-30||x>V.W+30||y>V.H+30)continue;const r=Math.min(24,(1.6+Math.sqrt(p[2])*.3)*zf);const c=PCOL[p.cat];ctx.globalAlpha=fade;ctx.beginPath();ctx.arc(x,y,r,0,7);ctx.fillStyle=tint(c,.55);ctx.fill();ctx.lineWidth=1.3;ctx.strokeStyle=c;ctx.stroke();O.hit.push([x,y,Math.max(r,9),p])}
 ctx.globalAlpha=1;homeMark();
 if(O.day==null){let n=0;const seen=new Set();for(const p of O.pl){if(n>50)break;if(p[9]=='Zuhause'||seen.has(p[9]))continue;const [x,y]=toS(MX(p[1]),MY(p[0]));if(x<0||y<0||x>V.W||y>V.H)continue;const r=Math.min(24,(1.6+Math.sqrt(p[2])*.3)*zf);if(lbl(p[9],x+r+3,y+4,12,650,MC.text)){seen.add(p[9]);n++}}}
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
 ctx.fillStyle=MC.land;ctx.fill(B.land);const S=V.S,A=aggReg();
 if(!RG.groups){RG.groups=new Map();RG.lines=new Path2D();const cs=new Set([...A.keys()].map(id=>RG.byId.get(id)?.a3));if(RG.cc)cs.add(RG.cc);
  for(const r of RG.list){if(cs.has(r.a3))RG.lines.addPath(r.p);const c=regFill(r);if(!c)continue;let p=RG.groups.get(c);if(!p){p=new Path2D();RG.groups.set(c,p)}p.addPath(r.p)}}
 for(const [c,p] of RG.groups){ctx.fillStyle=c;ctx.fill(p,'evenodd')}
 ctx.fillStyle=MC.lake;ctx.fill(B.lakes);
 ctx.strokeStyle=MC.regLine;ctx.lineWidth=.8/S;ctx.stroke(RG.lines);
 ctx.strokeStyle=MC.regBorder;ctx.lineWidth=1.3/S;ctx.stroke(B.borders)}
function drawRG(){
 TKEY='G'+RG.color+'_'+SELV;drawTiles(contentRG);worldT();const S=V.S;
 if(RG.hit){ctx.strokeStyle=MC.strong;ctx.lineWidth=3/S;ctx.stroke(RG.hit.p)}
 endWorld();placed.length=0;usedNames.clear();homeMark();
 if(S>2500){const A=aggReg();const vis=RG.list.filter(r=>A.has(r.id)).map(r=>[r,toS(MX(r.lo),MY(r.la))]).filter(([,[x,y]])=>x>0&&y>0&&x<V.W&&y<V.H).sort((a,b)=>A.get(b[0].id).days-A.get(a[0].id).days);for(const [r,[x,y]] of vis.slice(0,120))lbl(r.name.replace(/^(Kanton|Département|Gespanschaft|Provinz|Provincia|Region|Regierungsbezirk|Bezirk|Comté|County of) /,''),x,y,S>20000?12:11,650,MC.text,'center',3)}
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
segBind('g-color',v=>{RG.color=v;RG.groups=null;legendG();legend();full()});

/* ================= KARTE 5: ZEITRAFFER ================= */
const Z={t:0,play:false,speed:7,cam:'follow',trail:'all',last:0,cum:null,cl:new Map(),boxes:new Map(),drag:false};
const dayIdx=ds=>Math.round((dateOf(ds)-dateOf(D.days[0][0]))/864e5);
const PLAY='M2.5 1.5H5.5V12.5H2.5ZM8.5 1.5H11.5V12.5H8.5Z',PAUSE='M3 1.5L12 7L3 12.5Z';
function prepZ(){
 Z.n=D.days.length;Z.s0=Math.max(0,Math.min(Z.n-1,dayIdx(D.since||D.days[0][0])));Z.t=Math.max(Z.s0,Math.min(Z.n-1,Z.t||0));$('z-slider').min=Z.s0*24;$('z-slider').max=Math.max(1,(Z.n-1)*24);
 Z.cum=[];let s=0;D.days.forEach((r,i)=>{if(daySel(i))s+=r[1]+r[2]+r[3]+r[4];Z.cum.push(s)});
 Z.trips=D.trips.filter(t=>tripSel(t)&&t.b>=D.days[Z.s0][0]&&t.a<=D.days[Z.n-1][0]).map(t=>({t,a:Math.max(0,dayIdx(t.a)),b:Math.min(Z.n-1,dayIdx(t.b))}));
 Z.fl=new Map();(D.flights||[]).forEach(f=>{const [ds,A,B,fr]=f;if(!flightSel(f))return;const d=dayIdx(ds);if(!Z.fl.has(d))Z.fl.set(d,[]);Z.fl.get(d).push({A,B,s:fr==null?.4:fr})});
 const G=new Map(D.groups.map(g=>[g[0],g[1]]));const seen=new Set();
 const jumps=Z.trips.filter(o=>o.t.g).sort((x,y)=>y.t.km-x.t.km).filter(o=>{const k=o.t.g+o.t.y;if(seen.has(k))return false;seen.add(k);return true}).slice(0,14).sort((x,y)=>x.a-y.a);
 $('z-jump').innerHTML=`<button class="chip on" style="--c:${MC.strong}" data-i="${Z.s0}"><i></i>Anfang</button>`+jumps.map(o=>`<button class="chip on" style="--c:${WCOL[o.t.w]||'#8B3DFF'}" data-i="${o.a}"><i></i>${esc(G.get(o.t.g)||o.t.name)} ’${String(o.t.y).slice(2)}</button>`).join('');
 $('z-jump').querySelectorAll('.chip').forEach(b=>b.onclick=()=>jumpZ(+b.dataset.i));
 const c=$('z-line');const pos=e=>{const r=c.getBoundingClientRect();return Z.s0+Math.max(0,Math.min(1,(e.clientX-r.left)/r.width))*(Z.n-1-Z.s0)};
 c.onpointerdown=e=>{Z.drag=true;c.setPointerCapture(e.pointerId);setZ(pos(e));full()};
 c.onpointermove=e=>{if(Z.drag){setZ(pos(e));redraw()}else{const di=Math.floor(pos(e));const tr=Z.trips.find(o=>di>=o.a&&di<=o.b);c.title=dfmt(D.days[di][0])+(tr?' · '+tr.t.name:'')}};
 c.onpointerup=()=>{Z.drag=false;full()};
}
function trackT(i){return D.trackT&&D.trackT[i]?D.trackT[i]:[0,1]}
function cumLen(i){let c=Z.cl.get(i);if(c)return c;const a=TR[i].p;c=new Float64Array(a.length/2);for(let j=1;j<c.length;j++)c[j]=c[j-1]+Math.hypot(a[j*2]-a[j*2-2],a[j*2+1]-a[j*2-1]);Z.cl.set(i,c);if(Z.cl.size>4000)Z.cl.clear();return c}
function partial(i,p){/* draws track i up to share p, returns the head point */const a=TR[i].p,c=cumLen(i),L=c[c.length-1]*p;ctx.moveTo(a[0],a[1]);let j=1;for(;j<c.length&&c[j]<=L;j++)ctx.lineTo(a[j*2],a[j*2+1]);if(j>=c.length)return [a[a.length-2],a[a.length-1]];const f=(L-c[j-1])/Math.max(1e-12,c[j]-c[j-1]);const x=a[j*2-2]+(a[j*2]-a[j*2-2])*f,y=a[j*2-1]+(a[j*2+1]-a[j*2-1])*f;ctx.lineTo(x,y);return [x,y]}
function ptAt(i,p){const a=TR[i].p,c=cumLen(i),L=c[c.length-1]*p;let j=1;while(j<c.length&&c[j]<L)j++;if(j>=c.length)return [a[a.length-2],a[a.length-1]];const f=(L-c[j-1])/Math.max(1e-12,c[j]-c[j-1]);return [a[j*2-2]+(a[j*2]-a[j*2-2])*f,a[j*2-1]+(a[j*2+1]-a[j*2-1])*f]}
function bez(a,t){const u=1-t;return [u*u*a[0]+2*u*t*a[2]+t*t*a[4],u*u*a[1]+2*u*t*a[3]+t*t*a[5]]}
function boxOfTrip(o){const k='t'+o.t.id;if(Z.boxes.has(k))return Z.boxes.get(k);let b=null;for(let d=o.a;d<=o.b;d++){const q=bboxOfDay(d);if(q)b=b?[Math.min(b[0],q[0]),Math.min(b[1],q[1]),Math.max(b[2],q[2]),Math.max(b[3],q[3])]:q}if(!b){const x=MX(o.t.p[1]),y=MY(o.t.p[0]);b=[x,y,x,y]}Z.boxes.set(k,b);return b}
function groundBox(d){let x0=1,y0=1,x1=0,y1=0;for(const i of byDay[d]||[]){const b=TR[i].bb;x0=Math.min(x0,b[0]);y0=Math.min(y0,b[1]);x1=Math.max(x1,b[2]);y1=Math.max(y1,b[3])}return x0<=x1?[x0,y0,x1,y1]:null}
const ub=(a,b)=>!a?b:!b?a:[Math.min(a[0],b[0]),Math.min(a[1],b[1]),Math.max(a[2],b[2]),Math.max(a[3],b[3])];
function camBox(di){
 const fl=(Z.fl.get(di)||[]).filter(f=>Z.t-di>=f.s-.05&&Z.t-di<=f.s+.2);/* a flight in progress: show both ends */
 if(fl.length){let b=null;for(const f of fl)b=ub(b,[Math.min(MX(f.A[1]),MX(f.B[1])),Math.min(MY(f.A[0]),MY(f.B[0])),Math.max(MX(f.A[1]),MX(f.B[1])),Math.max(MY(f.A[0]),MY(f.B[0]))]);return b}
 const o=Z.trips.find(o=>di>=o.a&&di<=o.b&&o.t.g);
 if(o){let b=null;for(let d=Math.max(o.a,di-1);d<=Math.min(o.b,di+1);d++)b=ub(b,groundBox(d));if(b)return b;const x=MX(o.t.p[1]),y=MY(o.t.p[0]);return [x-.0004,y-.0004,x+.0004,y+.0004]}
 /* everyday life: a calm view of the home region instead of following every commute */
 const hx=MX(HOME[1]),hy=MY(HOME[0]);return [hx-.0011,hy-.0011,hx+.0011,hy+.0011]}
function boxScale(b,pad=.62){const w=Math.max(b[2]-b[0],1e-6),h=Math.max(b[3]-b[1],1e-6);return Math.min(260000,Math.max(1800,Math.min(V.W*pad/w,V.H*pad/h)))}
function jumpZ(di){setZ(Math.max(0,di));Z.card=undefined;tripCard();const b=camBox(di)||[MX(HOME[1]),MY(HOME[0]),MX(HOME[1]),MY(HOME[0])];flyTo((b[0]+b[2])/2,(b[1]+b[3])/2,boxScale(b))}
function setZ(t){Z.t=Math.max(Z.s0||0,Math.min(Z.n-1,t));$('z-slider').value=Math.round(Z.t*24);infoZ();drawZLine()}
function infoZ(){const di=Math.floor(Z.t),r=D.days[di],o=Z.trips.find(o=>di>=o.a&&di<=o.b),t=o&&o.t;
 const hh=Math.floor((Z.t-di)*24);$('z-date').textContent=dfmt(r[0]);$('z-what').textContent=t?`${t.w} · ${t.name} · Tag ${di-o.a+1} von ${o.b-o.a+1}`:(r[1]+r[2]+r[3]+r[4]>1?'Alltag':'kaum unterwegs');
 $('hud').style.display=TAB=='zeit'?'block':'none';$('hudd').textContent=dfmt(r[0])+(Z.play?'':'');
 $('huds').innerHTML=(t?`<i class="hdot" style="background:${WCOL[t.w]||'#8B3DFF'}"></i>${esc(t.name)} · `:'')+fmt(Z.cum[di]-(Z.cum[Z.s0-1]||0))+' km seit '+dfmt(D.days[Z.s0][0]).slice(3);
 if(!$('z1'))$('z-stats').innerHTML=statHTML([['z1','km bis zu diesem Tag'],['z2','Reisetage bis hier'],['z3','Reisen bis hier'],['z4','Länder bis hier']]);
 $('z1').textContent=fmt(Z.cum[di]-(Z.cum[Z.s0-1]||0));let n=0;for(let i=Z.s0;i<=di;i++)if(D.days[i][6]>=0&&daySel(i))n++;$('z2').textContent=fmt(n);
 const done=Z.trips.filter(q=>q.a<=di&&q.b>=Z.s0);$('z3').textContent=fmt(done.length);$('z4').textContent=fmt(new Set(done.map(q=>q.t.c).filter(Boolean)).size)}
function drawZLine(){const c=$('z-line');if(!c||!Z.cum)return;const w=c.parentElement.clientWidth,h=74,dpr=Math.min(2,window.devicePixelRatio||1);if(c.width!==Math.round(w*dpr)){c.width=Math.round(w*dpr);c.height=Math.round(h*dpr);c.style.height=h+'px'}
 const g=c.getContext('2d');g.setTransform(dpr,0,0,dpr,0,0);g.clearRect(0,0,w,h);const n=Z.n,s0=Z.s0,X=d=>(d-s0)/(Math.max(1,n-1-s0))*w;
 if(!Z.weeks){Z.weeks=[];for(let d=s0;d<n;d+=7){let k=0;for(let i=d;i<Math.min(n,d+7);i++){if(!daySel(i))continue;const r=D.days[i];k+=r[1]+r[2]+r[3]+r[4]}Z.weeks.push(k)}Z.wmax=Math.max(1,...Z.weeks)}
 const bw=Math.max(1,w/Z.weeks.length);g.fillStyle='#D9D4EA';Z.weeks.forEach((k,i)=>{const bh=Math.sqrt(k/Z.wmax)*38;g.fillRect(i*bw,44-bh,Math.max(1,bw-.5),bh)});
 for(const o of Z.trips){g.fillStyle=WCOL[o.t.w]||'#8B3DFF';g.fillRect(X(Math.max(s0,o.a)),48,Math.max(2,X(o.b+1)-X(Math.max(s0,o.a))),8)}
 g.font='700 10px Inter, system-ui, sans-serif';g.fillStyle='#5B5479';let ly=-1;for(let d=s0;d<n;d++){const ds=D.days[d][0];if(ds.endsWith('-01-01')||d==s0){const x=X(d);if(x-ly>34){g.fillRect(x,58,1,4);g.fillText(ds.slice(0,4),x+2,70);ly=x}}}
 const x=X(Z.t);g.fillStyle=MC.strong;g.fillRect(x-1,0,2,58);g.beginPath();g.arc(x,3,4,0,7);g.fill()}
function drawZ(){const TLS=STYLE?STYLE.timelapse:{cinema:true,glow:true};const M0=MC;if(TLS.cinema)MC=THEMES.dark;try{drawZ0(TLS)}finally{MC=M0}}
function drawZ0(TLS){
 const ti=Math.floor(Z.t),frac=Z.t-ti,from=Z.trail=='month'?Math.max(0,ti-30):0,upto=ti-6;
 const wk=Math.max(0,Math.floor(upto/42)*42),f0=Z.trail=='all'?0:Math.floor(from/14)*14;if(!Z.tr||Z.tr.wk!==wk||Z.tr.f0!==f0)Z.tr={wk,f0};
 TKEY='Z'+wk+'_'+f0+'_'+SELV+(TLS.cinema?'c':'');drawTiles(bb=>{drawBase();const S=V.S;ctx.globalAlpha=1;ctx.strokeStyle=MC.oldT;ctx.lineJoin='round';ctx.lineCap='round';ctx.lineWidth=S<300000?1/(S*(V.tf||1)):1.4/S;tileDraw(Z.tr,li=>{const d=TR[li].d;return TR[li].on&&d<wk&&d>=f0?'o':null},()=>0,()=>{},bb);ctx.globalAlpha=1});
 worldT();const S=V.S;const lw=Math.max(1,Math.min(2.4,S/40000))/S;ctx.lineJoin='round';ctx.lineCap='round';const LK=lodKey();
 ctx.strokeStyle=MC.old;ctx.lineWidth=lw;ctx.beginPath();
 for(let d=Math.max(wk,from);d<upto;d++)for(const i of byDay[d]||[]){const a=TR[i][LK];ctx.moveTo(a[0],a[1]);for(let j=2;j<a.length;j+=2)ctx.lineTo(a[j],a[j+1])}ctx.stroke();
 /* the last days: colour by transport, fading */
 if(TLS.cinema&&TLS.glow)ctx.globalCompositeOperation='lighter';
 for(let d=Math.max(from,ti-6);d<ti;d++){const age=ti-d+frac;ctx.globalAlpha=Math.max(.15,1-age*.13)*(TLS.cinema?.85:1);for(const i of byDay[d]||[]){const a=TR[i][LK];ctx.beginPath();ctx.moveTo(a[0],a[1]);for(let j=2;j<a.length;j+=2)ctx.lineTo(a[j],a[j+1]);const mm=TCLS[TR[i].c];ctx.strokeStyle=MCOL[mm];ctx.lineWidth=2.2/S*SM(mm).width;setDash(mm,S);ctx.stroke();ctx.setLineDash([])}
  for(const f of Z.fl.get(d)||[]){strokeArc(arcPts(MX(f.A[1]),MY(f.A[0]),MX(f.B[1]),MY(f.B[0])),[MCOL.fly],1.8,8,6)}}
 ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';
 /* today: drawn as far as the clock has come, with a glowing head */
 let head=null,plane=null,headCol=MCOL.road,headM='road',headA=0;
 for(const i of byDay[ti]||[]){const [s0,s1]=trackT(i);if(frac<s0)continue;const p=Math.min(1,(frac-s0)/Math.max(.004,s1-s0));ctx.beginPath();const h=partial(i,p);ctx.strokeStyle=MC.ring;ctx.lineWidth=6/S;ctx.stroke();const mm=TCLS[TR[i].c];ctx.strokeStyle=MCOL[mm];ctx.lineWidth=3.4/S*SM(mm).width;setDash(mm,S);ctx.stroke();ctx.setLineDash([]);head=h;headM=TCLS[TR[i].c];headCol=MCOL[headM];{const q=ptAt(i,Math.max(0,p-.02));headA=Math.atan2(h[1]-q[1],h[0]-q[0])}}
 for(const f of Z.fl.get(ti)||[]){if(frac<f.s)continue;const p=Math.min(1,(frac-f.s)/.12);const arc=arcPts(MX(f.A[1]),MY(f.A[0]),MX(f.B[1]),MY(f.B[0]));ctx.beginPath();ctx.moveTo(arc[0],arc[1]);const N=40;for(let k=1;k<=N*p;k++){const q=bez(arc,k/N);ctx.lineTo(q[0],q[1])}const q=bez(arc,p);ctx.lineTo(q[0],q[1]);ctx.setLineDash([8/S,6/S]);ctx.strokeStyle=MCOL.fly;ctx.lineWidth=2.8/S;ctx.stroke();ctx.setLineDash([]);if(p<1){const q2=bez(arc,Math.min(1,p+.01));plane=[q[0],q[1],Math.atan2(q2[1]-q[1],q2[0]-q[0])]}else{head=[arc[4],arc[5]];headCol=MCOL.fly}}
 endWorld();placed.length=0;usedNames.clear();
 if(!head&&!plane){for(let d=ti;d>=0&&!head;d--){const ids=(byDay[d]||[]).filter(i=>d<ti||trackT(i)[0]<=frac);if(ids.length){const a=TR[ids[ids.length-1]].p;head=[a[a.length-2],a[a.length-1]]}}}
 Z.pos=plane?[plane[0],plane[1]]:head;homeMark();drawPlaceLabels(TLS.cinema?'few':null);
 const SZ=1.35;
 if(plane){const [x,y]=toS(plane[0],plane[1]);drawPlane(ctx,x,y,plane[2],MCOL.fly,SZ*1.2)}
 else if(head){const [x,y]=toS(head[0],head[1]);const pulse=RED?0:(performance.now()/700)%1;ctx.beginPath();ctx.arc(x,y,10+pulse*16,0,7);ctx.fillStyle=tint(headCol,.25);ctx.globalAlpha=.45*(1-pulse);ctx.fill();ctx.globalAlpha=1;
  const moving=Z.play&&(D.days[ti]||[])[1]+(D.days[ti]||[])[2]>5;if(moving&&headM=='rail')drawTrain(ctx,x,y,headA,headCol,SZ);else if(moving&&headM=='road')drawCar(ctx,x,y,headA,headCol,SZ);else{ctx.beginPath();ctx.arc(x,y,6.5,0,7);ctx.fillStyle=headCol;ctx.fill();ctx.lineWidth=2.5;ctx.strokeStyle=MC.ring;ctx.stroke()}}
}
function tickZ(ts){if(!Z.play)return;const dt=Math.min(.1,(ts-(Z.last||ts))/1000);Z.last=ts;const di0=Math.floor(Z.t),inTrip=Z.trips.some(o=>di0>=o.a&&di0<=o.b);const fast=!inTrip&&STYLE&&STYLE.timelapse.skip_everyday?Math.max(1,Math.min(6,60/Z.speed)):1;setZ(Z.t+dt*Z.speed*fast);tripCard();
 if(Z.cam=='follow'){const di=Math.floor(Z.t);const b=camBox(di);const k=1-Math.exp(-dt*(Z.speed>30?1:1.6));
  if(b){let tS=boxScale(b);tS=TS*Math.pow(2,Math.round(Math.log2(tS/TS)));/* whole tile levels: the map tiles stay cached while playing */let cx=(b[0]+b[2])/2,cy=(b[1]+b[3])/2;if(Z.pos){/* keep the head well inside the view */const mx=V.W*.32/V.S,my=V.H*.32/V.S;cx=Math.min(Math.max(cx,Z.pos[0]-mx),Z.pos[0]+mx);cy=Math.min(Math.max(cy,Z.pos[1]-my),Z.pos[1]+my)}
   V.S=V.S*Math.pow(tS/V.S,k);V.cx+=(cx-V.cx)*k;V.cy+=(cy-V.cy)*k}}
 DRAW();scaleBar();if(Z.t>=Z.n-1){Z.play=false;setPlayZ()}else requestAnimationFrame(tickZ)}
function tripCard(){const di=Math.floor(Z.t),o=Z.trips.find(o=>di>=o.a&&di<=o.b);const id=o?o.t.id:null;if(id===Z.card)return;Z.card=id;const el=$('ztitle');if(!o){el.classList.remove('show');return}
 const t=o.t,G=t.g&&D.groups.find(g=>g[0]==t.g);const ic={fly:'✈️',rail:'🚆',road:'🚗',ferry:'⛴️',foot:'🚶'};
 el.innerHTML=`<div class="zt-w"><i style="background:${WCOL[t.w]||'#8B3DFF'}"></i>${esc(t.w)}</div><div class="zt-n">${esc(G?G[1]:t.name)}</div><div class="zt-d">${dfmt(t.a)}${t.n?' – '+dfmt(t.b):''} · ${t.m.map(m=>ic[m]||'').join(' ')}${t.km?' · '+fmt(t.km)+' km':''}</div>`;
 el.classList.remove('show');void el.offsetWidth;el.classList.add('show')}
function setPlayZ(){$('z-pico').setAttribute('d',Z.play?PLAY:PAUSE);$('z-play').setAttribute('aria-label',Z.play?'Pause':'Abspielen')}
$('z-play').onclick=()=>{Z.play=!Z.play;setPlayZ();if(Z.play){if(Z.t>=Z.n-1)setZ(0);Z.last=0;requestAnimationFrame(tickZ)}else full()};
$('z-slider').addEventListener('input',e=>{setZ(+e.target.value/24);if(!zq)zq=requestAnimationFrame(()=>{zq=null;DRAW()});clearTimeout(idleT);idleT=setTimeout(full,200)});let zq=null;
segBind('z-look',v=>{if(STYLE)STYLE.timelapse.cinema=v=='cine';Z.tr=null;full()});
segBind('z-speed',v=>Z.speed=+v);segBind('z-cam',v=>Z.cam=v);segBind('z-trail',v=>{Z.trail=v;Z.tr=null;full()});
document.addEventListener('keydown',e=>{if(TAB!='zeit'||e.target.closest('input,select,textarea'))return;if(e.code=='Space'){e.preventDefault();$('z-play').click()}else if(e.key=='ArrowRight'){setZ(Math.floor(Z.t)+1);full()}else if(e.key=='ArrowLeft'){setZ(Math.floor(Z.t)-1);full()}});

/* ================= Animierte Ebene: Flugzeuge, Züge, Autos ================= */
const cva=$('cva'),actx=cva.getContext('2d');
const AN={on:false,raf:0,arcs:[],cars:[],hidden:false};
function animWanted(){const a=STYLE?STYLE.anim:{on:true};let on=a.on;try{const v=localStorage.getItem('wm-anim');if(v!=null)on=v=='1'}catch(e){}return on}
function animOn(){return animWanted()&&!RED&&(TAB=='reisen'||TAB=='spuren')}
function sizeA(){cva.width=cv.width;cva.height=cv.height;cva.style.width=V.W+'px';cva.style.height=V.H+'px'}
function polyOf(li){const a=TR[li].l1;const n=a.length/2;const cum=new Float64Array(n);for(let j=1;j<n;j++)cum[j]=cum[j-1]+Math.hypot(a[j*2]-a[j*2-2],a[j*2+1]-a[j*2-1]);return {a,cum,len:cum[n-1],bb:TR[li].bb}}
function animBuild(){
 AN.arcs=[];AN.cars=[];const A=STYLE?STYLE.anim:{planes:true,vehicles:true};let seed=1;const rnd=()=>{seed=(seed*16807)%2147483647;return seed/2147483647};
 if(TAB=='reisen'&&RC){
  if(A.planes)for(const e of RC.pairs){const [a1,b1]=e.k.split('>');const [x1,y1]=gpos(a1),[x2,y2]=gpos(b1);AN.arcs.push({a:arcPts(x1,y1,x2,y2,a1=='home'?.2:.18),cols:R.color=='w'?WHO.filter(w=>e.ws.has(w)).map(w=>WCOL[w]):[MCOL.fly],ph:rnd()*2})}
  if(A.vehicles&&TR){const hc=(D.region&&D.region.name)||'';const cand=[];
   for(const t of RC.on){if(!t.g||!t.m.some(m=>m=='road'||m=='rail'))continue;if(hc&&t.c&&t.c==hc)continue;
    let best=null,bl=0;for(let d=dayIdx(t.a);d<=dayIdx(t.b);d++)for(const li of byDay[d]||[]){const m=TCLS[TR[li].c];if(m!='road'&&m!='rail')continue;if(!R.m.has(m))continue;const b=TR[li].bb;const l=Math.hypot(b[2]-b[0],b[3]-b[1]);if(l>bl){bl=l;best=li}}
    if(best!=null&&bl>1e-3)cand.push([bl,best,t])}
   cand.sort((a,b)=>b[0]-a[0]);for(const [,li,t] of cand.slice(0,25)){const m=TCLS[TR[li].c];AN.cars.push({...polyOf(li),m,col:R.color=='w'?WCOL[t.w]:MCOL[m],ph:rnd()*2})}}}
 else if(TAB=='spuren'&&SP.fl&&A.planes){const seen=new Set();for(const [a,c] of SP.fl){const k=Math.round(a[0]*2e3)+','+Math.round(a[1]*2e3)+','+Math.round(a[4]*2e3)+','+Math.round(a[5]*2e3)+c;if(seen.has(k))continue;seen.add(k);AN.arcs.push({a,cols:[c],ph:rnd()*2});if(AN.arcs.length>=150)break}}
}
function animRestart(){const on=animOn();AN.on=on;if(on){animBuild();sizeA();cva.hidden=false;if(!AN.raf)AN.raf=requestAnimationFrame(animFrame)}else{cva.hidden=true;if(AN.raf){cancelAnimationFrame(AN.raf);AN.raf=0}}}
document.addEventListener('visibilitychange',()=>{if(!document.hidden&&AN.on&&!AN.raf)AN.raf=requestAnimationFrame(animFrame)});
const pingpong=p=>{const q=p%2;const u=q<1?q:2-q;return u<.5?2*u*u:1-Math.pow(-2*u+2,2)/2};
function dashArr(m){const d=SM(m).dash;return d=='dashed'?[8,6]:d=='dotted'?[.1,5]:d=='longdash'?[16,7]:d=='dashdot'?[10,4,.1,4]:d=='sparse'?[.1,10]:[]}
function drawPlane(g,x,y,ang,col,s){g.save();g.translate(x,y);g.rotate(ang);g.scale(s,s);g.fillStyle=col;g.strokeStyle=MC.ring;g.lineWidth=1.6;g.lineJoin='round';g.beginPath();g.moveTo(9,0);g.lineTo(2,-1.6);g.lineTo(-2,-7.5);g.lineTo(-4,-7.5);g.lineTo(-1.6,-1.6);g.lineTo(-6,-1.4);g.lineTo(-8,-4);g.lineTo(-9,-4);g.lineTo(-8,0);g.lineTo(-9,4);g.lineTo(-8,4);g.lineTo(-6,1.4);g.lineTo(-1.6,1.6);g.lineTo(-4,7.5);g.lineTo(-2,7.5);g.lineTo(2,1.6);g.closePath();g.stroke();g.fill();g.restore()}
function drawCar(g,x,y,ang,col,s){g.save();g.translate(x,y);const flip=Math.abs(ang)>Math.PI/2;g.rotate(flip?ang+Math.PI:ang);g.scale(flip?-s:s,s);g.fillStyle=col;g.strokeStyle=MC.ring;g.lineWidth=1.5;g.beginPath();g.roundRect(-7,-3.2,14,5.2,2.2);g.moveTo(-3.6,-3.2);g.lineTo(-1.8,-6.4);g.lineTo(3.4,-6.4);g.lineTo(5,-3.2);g.closePath();g.stroke();g.fill();g.fillStyle=MC.ring;g.fillRect(-1.2,-5.6,1.6,2.1);g.fillRect(1.2,-5.6,1.8,2.1);g.fillStyle=MC.strong;for(const wx of [-4,4]){g.beginPath();g.arc(wx,2.2,1.9,0,7);g.fill()}g.restore()}
function drawTrain(g,x,y,ang,col,s){g.save();g.translate(x,y);const flip=Math.abs(ang)>Math.PI/2;g.rotate(flip?ang+Math.PI:ang);g.scale(flip?-s:s,s);g.fillStyle=col;g.strokeStyle=MC.ring;g.lineWidth=1.5;g.beginPath();g.moveTo(-10,-4.5);g.lineTo(6,-4.5);g.quadraticCurveTo(10.5,-4.5,10.5,1.5);g.lineTo(10.5,3);g.lineTo(-10,3);g.closePath();g.stroke();g.fill();g.fillStyle=MC.ring;for(const wx of [-8,-4,0])g.fillRect(wx,-3,2.6,2.2);g.beginPath();g.moveTo(5,-3);g.lineTo(8,-3);g.lineTo(9.3,-.8);g.lineTo(5,-.8);g.fill();g.restore()}
function animFrame(ts){
 AN.raf=0;if(!AN.on||document.hidden)return;
 const A=STYLE?STYLE.anim:{speed:1,size:1,hide_line:true},t=ts/1000*(A.speed||1),sz=(A.size||1)*1.25*(V.W<600?.9:1);
 actx.setTransform(V.dpr,0,0,V.dpr,0,0);actx.clearRect(0,0,V.W,V.H);actx.lineCap='round';actx.lineJoin='round';
 const fw=2.4*SM('fly').width,fd=dashArr('fly'),N=56;
 for(const A2 of AN.arcs){const a=A2.a;const P=[toS(a[0],a[1]),toS(a[2],a[3]),toS(a[4],a[5])];
  const x0=Math.min(P[0][0],P[1][0],P[2][0]),x1=Math.max(P[0][0],P[1][0],P[2][0]),y0=Math.min(P[0][1],P[1][1],P[2][1]),y1=Math.max(P[0][1],P[1][1],P[2][1]);
  if(x1<-20||y1<-20||x0>V.W+20||y0>V.H+20)continue;
  const len=Math.hypot(P[2][0]-P[0][0],P[2][1]-P[0][1]);const per=Math.max(2.6,Math.min(9,len/110));const raw=t/per+A2.ph;const u=pingpong(raw),back=(raw%2)>=1;
  const at=s=>{const v=1-s;return [v*v*P[0][0]+2*v*s*P[1][0]+s*s*P[2][0],v*v*P[0][1]+2*v*s*P[1][1]+s*s*P[2][1]]};
  const gap=A.hide_line?Math.min(.12,22/Math.max(1,len)):0;
  actx.setLineDash(fd);actx.lineWidth=fw;actx.globalAlpha=len<60?.55:.9;
  A2.cols.forEach((c,ci)=>{actx.strokeStyle=c;actx.lineDashOffset=-ci*(fd.length?fd[0]+fd[1]:0);actx.beginPath();let pen=false;for(let k=0;k<=N;k++){const s=k/N;const near=gap&&Math.abs(s-u)<gap;if(near){pen=false;continue}const [px,py]=at(s);pen?actx.lineTo(px,py):actx.moveTo(px,py);pen=true}actx.stroke()});
  actx.setLineDash([]);actx.globalAlpha=1;
  if(len<40)continue;
  A2.cols.forEach((c,ci)=>{const uu=Math.max(0,Math.min(1,u-(back?-1:1)*ci*Math.min(.08,14/len)));const [px,py]=at(uu),[qx,qy]=at(Math.min(1,uu+.01)),[rx,ry]=at(Math.max(0,uu-.01));let ang=Math.atan2(qy-ry,qx-rx);if(back)ang+=Math.PI;drawPlane(actx,px,py,ang,c,sz)});
 }
 for(const v of AN.cars){const b=v.bb;const [sx0,sy0]=toS(b[0],b[1]),[sx1,sy1]=toS(b[2],b[3]);if(sx1<-20||sy1<-20||sx0>V.W+20||sy0>V.H+20)continue;
  const lenpx=v.len*V.S;if(lenpx<50)continue;const per=Math.max(3,Math.min(14,lenpx/70));const raw=t/per+v.ph,u=pingpong(raw),back=(raw%2)>=1;
  const L=u*v.len;let lo=0,hi=v.cum.length-1;while(hi-lo>1){const mid=(lo+hi)>>1;if(v.cum[mid]<L)lo=mid;else hi=mid}
  const f=(L-v.cum[lo])/Math.max(1e-12,v.cum[hi]-v.cum[lo]);const wx=v.a[lo*2]+(v.a[hi*2]-v.a[lo*2])*f,wy=v.a[lo*2+1]+(v.a[hi*2+1]-v.a[lo*2+1])*f;
  const [px,py]=toS(wx,wy);let ang=Math.atan2(v.a[hi*2+1]-v.a[lo*2+1],v.a[hi*2]-v.a[lo*2]);if(back)ang+=Math.PI;ang=Math.atan2(Math.sin(ang),Math.cos(ang));
  if(A.hide_line){actx.globalAlpha=.85;actx.fillStyle=MC.land;actx.beginPath();actx.arc(px,py,9*sz,0,7);actx.fill();actx.globalAlpha=1}
  (v.m=='rail'?drawTrain:drawCar)(actx,px,py,ang,v.col,sz)}
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
wrap.addEventListener('wheel',e=>{if(e.target.closest('.detail'))return;e.preventDefault();const r=wrap.getBoundingClientRect();zoomAt(Math.exp(-e.deltaY*.0018),e.clientX-r.left,e.clientY-r.top)},{passive:false});
wrap.addEventListener('pointerdown',e=>{if(e.target.closest('.ctrl,.detail,.legend'))return;ptrs.set(e.pointerId,{x:e.clientX,y:e.clientY});moved=false;downAt={x:e.clientX,y:e.clientY};wrap.setPointerCapture(e.pointerId);wrap.classList.add('drag');if(ptrs.size==2){const [a,b]=[...ptrs.values()];pinch={d:Math.hypot(a.x-b.x,a.y-b.y)}}});
wrap.addEventListener('pointermove',e=>{
 const r=wrap.getBoundingClientRect(),sx=e.clientX-r.left,sy=e.clientY-r.top;
 if(!ptrs.size&&e.pointerType=='mouse'){if(TAB=='orte'&&O.hit){const h=O.hit.findLast(([hx,hy,hr])=>Math.hypot(hx-sx,hy-sy)<hr);h?showTip(e,`${h[3][9]} · ${fmt(h[3][2])} h`):hideTip()}else if(TAB=='regionen'&&RG.list){const r=regAt(sx,sy);const v=r&&aggReg().get(r.id);r?showTip(e,r.name+' · '+(RG.countries[r.a3]||r.a3)+(v?` · seit ${v.first.slice(0,4)}`:' · noch nie')):hideTip()}}
 if(!ptrs.has(e.pointerId))return;const prev=ptrs.get(e.pointerId),cur={x:e.clientX,y:e.clientY};ptrs.set(e.pointerId,cur);
 if(Math.hypot(cur.x-downAt.x,cur.y-downAt.y)>5)moved=true;
 if(ptrs.size==2&&pinch){const [a,b]=[...ptrs.values()];const d=Math.hypot(a.x-b.x,a.y-b.y);zoomAt(d/pinch.d,(a.x+b.x)/2-r.left,(a.y+b.y)/2-r.top);pinch.d=d;return}
 V.cx-=(cur.x-prev.x)/V.S;V.cy-=(cur.y-prev.y)/V.S;redraw()});
function up(e){ptrs.delete(e.pointerId);if(ptrs.size<2)pinch=null;if(!ptrs.size){wrap.classList.remove('drag');clearTimeout(idleT);idleT=setTimeout(full,60)}}
wrap.addEventListener('pointerup',e=>{const wasMoved=moved;up(e);if(wasMoved||e.target.closest('.ctrl,.detail,.legend'))return;const r=wrap.getBoundingClientRect(),sx=e.clientX-r.left,sy=e.clientY-r.top;
 if(TAB=='reisen'){const f=hitR(sx,sy);f?f():closeDetail()}
 else if(TAB=='orte'){const h=O.hit.findLast(([hx,hy,hr])=>Math.hypot(hx-sx,hy-sy)<hr);if(h)placeDetail(h[3])}
 else if(TAB=='regionen'){const r=regAt(sx,sy);RG.hit=r;full();if(r){const v=aggReg().get(r.id);openDetail(`<h3>${esc(r.name)}</h3><div class="dsub">${esc(RG.countries[r.a3]||r.a3)}</div>`+(v?`<div class="trip"><div class="s" style="background:${regFill(r)}"></div><div><div class="t1">Zum ersten Mal: ${dfmt(v.first)}</div><div class="t2">an ${fmt(v.days)} ${v.days==1?'Tag':'Tagen'} dort oder durchgefahren${v.stay?' · mit Aufenthalten':''}</div></div></div>`:'<div class="empty">Hier wart ihr laut den Daten noch nie.</div>'),()=>{RG.hit=null;full()})}else closeDetail()}});
wrap.addEventListener('pointercancel',up);
$('ztheme').onclick=()=>{const next=THEME=='dark'?'light':'dark';try{localStorage.setItem('wm-theme',next)}catch(e){}pickTheme();themeBtn();TC.clear();RG.groups=null;Z.tr=null;if(PCOL)PCOL.Zuhause=MC.strong;whoBar();if(TAB=='orte')drawCal();if(TAB=='zeit')drawZLine();enter(TAB)};
matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>{let t='auto';try{t=localStorage.getItem('wm-theme')||'auto'}catch(e){}if(t=='auto'){pickTheme();TC.clear();RG.groups=null;if(D)enter(TAB)}});
themeBtn();
$('zin').onclick=()=>zoomAt(1.7,V.W/2,V.H/2);$('zout').onclick=()=>zoomAt(1/1.7,V.W/2,V.H/2);
$('zhome').onclick=()=>flyTo(MX(HOME[1]),MY(HOME[0]),260000);
$('zch').onclick=()=>{const b=D.region.box;fit(b[0],b[1],b[2],b[3])};$('zeu').onclick=()=>{const s=V.S;fitTrips();const t={cx:V.cx,cy:V.cy,S:V.S};V.S=s;flyTo(t.cx,t.cy,t.S)};

/* ================= Daten aus der App ================= */
function initData(){
 if(!D.days.length){const t=new Date().toISOString().slice(0,10);D.days=[[t,0,0,0,0,0,-1,0]]}
 HOME=D.home;WHO=D.who.slice();for(const n of [...(D.persons||[]),...GCFG().map(g=>g.name)])if(!WHO.includes(n))WHO.splice(WHO.length-1,0,n);WCOL={};let pi=0;
 const CC=D.colors||{};const used=new Set(Object.values(CC));
 for(const w of WHO){if(CC[w])WCOL[w]=CC[w];else if(w=='Alltag')WCOL[w]='#8A82AA';else if(w=='offen')WCOL[w]='#B8B0D6';else if(PALETTE==PALETTES.neon&&GROUPCOL[w]&&!D.persons.includes(w))WCOL[w]=GROUPCOL[w];else{while((used.has(PALETTE[pi%PALETTE.length])||Object.values(GROUPCOL).includes(PALETTE[pi%PALETTE.length])&&!D.persons.includes(w))&&pi<PALETTE.length*2)pi++;WCOL[w]=PALETTE[pi++%PALETTE.length]}}
 PCOL={Zuhause:MC.strong,Arbeit:'#FFB000',...WCOL};
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
const NEEDS={reisen:['tracks'],spuren:['tracks'],orte:['tracks'],regionen:['reg'],zeit:['tracks']};
function need(k){if(!window.__T.t0)__T.t0=performance.now();if(ready[k])return ready[k];if(k=='tracks')ready[k]=loadJSON('api/atlas/tracks').then(T=>{const t=performance.now();__T.fetch=t-__T.t0;prepTracks(T);__T.prep=performance.now()-t});if(k=='reg')ready[k]=Promise.all([loadJSON('regions.json'),loadJSON('api/atlas/reg')]).then(([m,g])=>prepReg(m,g));return ready[k]}
function setTab(t){
 TAB=t;closeDetail();hideTip();stopR();if(Z.play){Z.play=false;setPlayZ()}
 document.querySelectorAll('#tabs button').forEach(b=>b.classList.toggle('on',b.dataset.t==t));
 document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('on',p.id=='p-'+t));
 $('hud').style.display=t=='zeit'?'block':'none';if(t!='zeit'){$('ztitle').classList.remove('show');Z.card=undefined}
 try{history.replaceState(null,'','#'+t)}catch(e){}
 $('load').style.display='grid';
 Promise.all(NEEDS[t].map(need)).then(()=>{$('load').style.display='none';enter(t)}).catch(()=>{$('load').textContent='Daten konnten nicht geladen werden.'});
}
const fitted={};
function enter(t){
 legend();const _e=performance.now();setTimeout(()=>{__T.enter=performance.now()-_e},0);
 if(t=='reisen'){DRAW=drawR;chipsR();let _t=performance.now();buildR();__T.buildR=performance.now()-_t;sideR();if(!fitted.r){fitted.r=1;fitTrips()}}
 if(t=='spuren'){routeNote();DRAW=drawS;chipsS();let _t=performance.now();buildS();__T.buildS=performance.now()-_t;_t=performance.now();sideS();__T.sideS=performance.now()-_t;if(!fitted.s){fitted.s=1;const b=D.region.box;setFit(b[0],b[1],b[2],b[3])}}
 if(t=='orte'){DRAW=drawO;if(!O.pl)O.pl=D.places.filter(placeSel).map(p=>{p.cat=placeCat(p);return p}).sort((a,b)=>b[2]-a[2]);sideO();drawCal();if(!fitted.o){fitted.o=1;setFit(HOME[0]-.35,HOME[1]-.7,HOME[0]+.3,HOME[1]+.5)}}
 if(t=='regionen'){DRAW=drawRG;sideRG();if(!fitted.g){fitted.g=1;const A=aggReg();let b=null;for(const id of A.keys()){const r=RG.byId.get(id);if(r)b=ub(b,r.bb)}if(b){const S=Math.min((V.W-80)/(b[2]-b[0]),(V.H-80)/(b[3]-b[1]));V.cx=(b[0]+b[2])/2;V.cy=(b[1]+b[3])/2;V.S=Math.min(S,120000)}else{const q=D.region.box;setFit(q[0],q[1],q[2],q[3])}}}
 if(t=='zeit'){DRAW=drawZ;if(!Z.cum)prepZ();Z.weeks=null;infoZ();drawZLine();if(!fitted.z){fitted.z=1;const b=camBox(Math.floor(Z.t));if(b){V.cx=(b[0]+b[2])/2;V.cy=(b[1]+b[3])/2;V.S=boxScale(b)}else setFit(HOME[0]-.35,HOME[1]-.7,HOME[0]+.3,HOME[1]+.5)}}
 full();animRestart();
}
document.querySelectorAll('#tabs button').forEach(b=>b.onclick=()=>setTab(b.dataset.t));
window.addEventListener('hashchange',()=>{const h=location.hash.slice(1);if(D&&NEEDS[h]&&h!=TAB)setTab(h)});
let rsz=null;window.addEventListener('resize',()=>{clearTimeout(rsz);rsz=setTimeout(()=>{sizeCV();sizeA();full();if(TAB=='orte')drawCal();if(TAB=='zeit')drawZLine()},120)});
/* descriptions live behind a small (i) button so the panels stay calm */
document.querySelectorAll('.panel').forEach(pn=>{const h=pn.querySelector('h1');if(!h)return;const head=h.parentElement;const bits=[...pn.querySelectorAll('.sub,details.note')];if(!bits.length)return;
 const box=document.createElement('div');box.className='infobox';box.hidden=true;box.id='info-'+pn.id;
 for(const b of bits){const q=document.createElement('p');if(b.tagName=='DETAILS'){const sm=b.querySelector('summary');if(sm)sm.remove();while(b.firstChild)q.appendChild(b.firstChild)}else{q.id=b.id||'';while(b.firstChild)q.appendChild(b.firstChild)}box.appendChild(q);b.remove()}
 const wrapH=document.createElement('div');wrapH.className='ph';head.insertBefore(wrapH,h);wrapH.appendChild(h);
 const btn=document.createElement('button');btn.className='info';btn.textContent='i';btn.setAttribute('aria-label','Was zeigt diese Karte?');btn.setAttribute('aria-expanded','false');btn.setAttribute('aria-controls',box.id);
 btn.onclick=()=>{box.hidden=!box.hidden;btn.setAttribute('aria-expanded',String(!box.hidden))};wrapH.appendChild(btn);head.appendChild(box)});
window.__T={};
sizeCV();
setInterval(()=>{if(!document.hidden)badge()},60000);
window.__wm={AN,V,MX,MY,full,get D(){return D},get TAB(){return TAB}};
Promise.all([loadJSON('api/atlas/core'),loadJSON('base.json'),loadJSON('api/atlas/labels'),loadJSON('api/style').catch(()=>null)]).then(([c,b,l,st])=>{
 if(st){applyStyle(st.style);pickTheme();themeBtn()}
 D=c;LAB=l;prepBase(b);initData();badge();D.trips.forEach(t=>tripById[t.id]=t);
 const d0=dateOf(D.days[0][0]);D.days.forEach((r,i)=>{const d=new Date(d0.getTime()+i*864e5);const who=r[6]>=0?tripById[r[6]].w:'Alltag';dayInfo[i]={y:d.getUTCFullYear(),dow:d.getUTCDay(),who,cat:r[6]>=0?'Reise':'Alltag'}});
 whoBar();emptyState();const h=(location.hash||'').slice(1);setTab(NEEDS[h]?h:'reisen');
}).catch(()=>{$('load').textContent='Daten konnten nicht geladen werden.'});
}
