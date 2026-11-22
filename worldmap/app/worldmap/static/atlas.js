{
/* ================= Grundlagen ================= */
let WHO=['Alltag'];const MODES=['fly','rail','road','ferry','foot'];
let WCOL={Alltag:'#8A82AA'};
const PALETTE=['#0A7CFF','#FF3D9A','#8B3DFF','#00BFB3','#FF8A00','#12A84F','#E03131','#5C7CFA','#C2255C','#2B8A3E'];
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
function tint(c,a){const r=parseInt(c.slice(1,3),16),g=parseInt(c.slice(3,5),16),b=parseInt(c.slice(5,7),16);const m=(x,y)=>Math.round(y+(x-y)*a).toString(16).padStart(2,'0');return '#'+m(r,252)+m(g,251)+m(b,255)}
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
function sizeCV(){const r=$('wrap').getBoundingClientRect();V.W=r.width;V.H=r.height;V.dpr=Math.min(V.W*V.H>900000?1.5:2,window.devicePixelRatio||1);cv.width=Math.round(r.width*V.dpr);cv.height=Math.round(r.height*V.dpr)}
const toS=(x,y)=>[(x-V.cx)*V.S+V.W/2,(y-V.cy)*V.S+V.H/2];
const toW=(sx,sy)=>[(sx-V.W/2)/V.S+V.cx,(sy-V.H/2)/V.S+V.cy];
const TS=256,TDPR=Math.min(2,window.devicePixelRatio||1),TC=new Map();let TKEY='',tileT=null;
function renderTile(z,x,y,fn){const n=2**z,St=TS*n,f=TDPR;const c=document.createElement('canvas');c.width=c.height=Math.round(TS*f);const g=c.getContext('2d');const bb=[x/n,y/n,(x+1)/n,(y+1)/n];const oc=ctx,oS=V.S;ctx=g;V.S=St;V.tf=f;g.setTransform(f*St,0,0,f*St,-x*TS*f,-y*TS*f);g.fillStyle='#DCE4F6';g.fillRect(bb[0],bb[1],1/n,1/n);try{fn(bb)}finally{ctx=oc;V.S=oS}return c}
function drawTiles(fn){
 ctx.setTransform(V.dpr,0,0,V.dpr,0,0);ctx.fillStyle='#E7E4F2';ctx.fillRect(0,0,V.W,V.H);
 const z=Math.max(1,Math.min(25,Math.round(Math.log2(V.S/TS)))),n=2**z,k=V.S/(TS*n),ts=TS*k;
 const x0=Math.floor((V.cx-V.W/2/V.S)*n),x1=Math.floor((V.cx+V.W/2/V.S)*n),y0=Math.floor((V.cy-V.H/2/V.S)*n),y1=Math.floor((V.cy+V.H/2/V.S)*n);
 const list=[];for(let x=x0;x<=x1;x++)for(let y=y0;y<=y1;y++)list.push([x,y]);const cx=V.cx*n,cy=V.cy*n;list.sort((a,b)=>Math.hypot(a[0]+.5-cx,a[1]+.5-cy)-Math.hypot(b[0]+.5-cx,b[1]+.5-cy));
 const t0=performance.now();let miss=0;
 for(const [x,y] of list){const key=TKEY+'|'+z+'|'+x+'|'+y;let t=TC.get(key);const sx=Math.floor((x/n-V.cx)*V.S+V.W/2),sy=Math.floor((y/n-V.cy)*V.S+V.H/2),sz=Math.ceil(ts)+1;
  if(!t&&performance.now()-t0<28){t=renderTile(z,x,y,fn);TC.set(key,t)}
  if(t){TC.delete(key);TC.set(key,t);ctx.drawImage(t,sx,sy,sz,sz);continue}
  miss++;let drew=false;for(let up=1;up<=5&&!drew;up++){const m=2**up,pk=TKEY+'|'+(z-up)+'|'+Math.floor(x/m)+'|'+Math.floor(y/m);const pt=TC.get(pk);if(pt){const sub=pt.width/m;ctx.drawImage(pt,(x-Math.floor(x/m)*m)*sub,(y-Math.floor(y/m)*m)*sub,sub,sub,sx,sy,sz,sz);drew=true}}
  if(!drew){for(const dn of [1,2]){const m=2**dn;const cz=z+dn;let any=false;for(let i=0;i<m;i++)for(let j=0;j<m;j++){const ck=TKEY+'|'+cz+'|'+(x*m+i)+'|'+(y*m+j);const ct=TC.get(ck);if(ct){ctx.drawImage(ct,sx+i*sz/m,sy+j*sz/m,sz/m+1,sz/m+1);any=true}}if(any)break}}}
 while(TC.size>260)TC.delete(TC.keys().next().value);
 window.__miss=miss;if(miss){clearTimeout(tileT);tileT=setTimeout(()=>redraw(),16)}
}
function worldT(){ctx.save();ctx.translate(V.W/2,V.H/2);ctx.scale(V.S,V.S);ctx.translate(-V.cx,-V.cy)}
function begin(){ctx.setTransform(V.dpr,0,0,V.dpr,0,0);ctx.fillStyle='#DCE4F6';ctx.fillRect(0,0,V.W,V.H);ctx.save();ctx.translate(V.W/2,V.H/2);ctx.scale(V.S,V.S);ctx.translate(-V.cx,-V.cy)}
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
 B={land:decRingsClosed(j.land),lakes:decRingsClosed(j.lakes),borders:decRings(j.borders),prov:decRings(j.prov),rivB:decRings(rivB),rivS:decRings(rivS),cant:decRings(j.ch_cant),mun:decRings(j.ch_mun),chb:decRings(j.ch_border),ne:j.labels};
}
function drawBase(opt={}){
 const S=V.S;
 ctx.fillStyle='#FCFBFF';ctx.fill(B.land,'nonzero');
 if(S>14000){ctx.strokeStyle='#ECE8F5';ctx.lineWidth=.8/S;ctx.stroke(B.prov)}
 if(opt.mun||S>260000){ctx.strokeStyle=opt.mun?'#D8D2EC':'#EEEAF7';ctx.lineWidth=(opt.mun?.7:.8)/S;ctx.stroke(B.mun)}
 if(S>30000){ctx.strokeStyle='#C4D4F2';ctx.lineWidth=Math.min(2,S/60000)/S;ctx.stroke(B.rivS)}
 ctx.strokeStyle='#B6CAEF';ctx.lineWidth=Math.min(2.4,.6+S/50000)/S;ctx.stroke(B.rivB);
 ctx.fillStyle='#C9D8F3';ctx.fill(B.lakes);ctx.strokeStyle='#AFC3EA';ctx.lineWidth=.7/S;ctx.stroke(B.lakes);
 if(S>35000||opt.mun){ctx.strokeStyle=opt.mun?'#B5ABD6':'#DCD6EE';ctx.lineWidth=(opt.mun?1.3:1)/S;ctx.stroke(B.cant)}
 ctx.strokeStyle='#C2B8E0';ctx.lineWidth=1.2/S;ctx.stroke(B.borders);
 ctx.setLineDash([5/S,4/S]);ctx.strokeStyle='#A79CD0';ctx.lineWidth=1.3/S;ctx.stroke(B.chb);ctx.setLineDash([]);
}
const placed=[];const usedNames=new Set();
function lbl(t,x,y,fs,fw,c,anchor='left',halo=4,force=false){if(!force&&usedNames.has(t))return false;ctx.font=`${fw} ${fs}px Inter, sans-serif`;const w=ctx.measureText(t).width;let x0=anchor=='left'?x:anchor=='right'?x-w:x-w/2;const box=[x0-2,y-fs+1,x0+w+2,y+4];if(!force&&placed.some(b=>!(box[2]<b[0]||box[0]>b[2]||box[3]<b[1]||box[1]>b[3])))return false;placed.push(box);usedNames.add(t);ctx.textAlign='left';ctx.lineJoin='round';ctx.lineWidth=halo;ctx.strokeStyle='rgba(252,251,255,.92)';ctx.strokeText(t,x0,y);ctx.fillStyle=c;ctx.fillText(t,x0,y);return true}
let LALL=null;
function drawPlaceLabels(){
 const S=V.S;
 if(!LALL){LALL=[];for(const [n,sr,la,lo,cap] of B.ne)LALL.push([sr*10-(cap?5:0),n,MX(lo),MY(la),sr<=2?13:12,sr<=2?700:600,sr<=1?0:sr<=3?6000:sr<=5?12000:sr<=7?30000:80000]);for(const [n,c,la,lo] of LAB)LALL.push([30+c*10,n,MX(lo),MY(la),[12.5,12,11.5,11,10.5][c],[650,600,550,500,500][c],[15000,55000,180000,600000,600000][c]]);LALL.sort((a,b)=>a[0]-b[0])}
 const x0=V.cx-V.W/2/S-20/S,x1=V.cx+V.W/2/S+20/S,y0=V.cy-V.H/2/S,y1=V.cy+V.H/2/S;let n=0;
 for(const [r,t,wx,wy,fs,fw,need] of LALL){if(S<need||wx<x0||wx>x1||wy<y0||wy>y1)continue;const x=(wx-V.cx)*S+V.W/2,y=(wy-V.cy)*S+V.H/2;if(x<-50||y<-20||x>V.W+50||y>V.H+20)continue;if(lbl(t,x+4,y+4,fs,fw,'#6F6890',
 'left',3.5)){ctx.fillStyle='#8E86AE';ctx.beginPath();ctx.arc(x,y,1.8,0,7);ctx.fill();if(++n>140)break}}
}
function homeMark(){const [x,y]=toS(MX(HOME[1]),MY(HOME[0]));ctx.beginPath();ctx.arc(x,y,6,0,7);ctx.fillStyle='#17122E';ctx.fill();ctx.lineWidth=2;ctx.strokeStyle='#fff';ctx.stroke();ctx.beginPath();ctx.arc(x,y,11,0,7);ctx.strokeStyle='#17122E';ctx.lineWidth=1.8;ctx.stroke();lbl('Zuhause',x+15,y-8,14,800,'#17122E','left',4.5,true)}
function pieS(x,y,r,cs){if(!cs.length)cs=['#B8B0D6'];if(cs.length==1){ctx.beginPath();ctx.arc(x,y,r,0,7);ctx.fillStyle=cs[0];ctx.fill()}else cs.forEach((c,i)=>{ctx.beginPath();ctx.moveTo(x,y);ctx.arc(x,y,r,2*Math.PI*i/cs.length-Math.PI/2,2*Math.PI*(i+1)/cs.length-Math.PI/2);ctx.closePath();ctx.fillStyle=c;ctx.fill()});ctx.beginPath();ctx.arc(x,y,r,0,7);ctx.lineWidth=2;ctx.strokeStyle='#fff';ctx.stroke()}

/* ---- Daten ---- */
let D=null,tripById={},dayInfo=[],TR=null,byDay={},GEM=null;
const ready={};
function loadJSON(u){return fetch(u).then(r=>{if(!r.ok)throw new Error(u);return r.json()})}
function prepTracks(T){
 const thin=(a,d)=>{const o=[a[0],a[1]];let px=a[0],py=a[1];const n=a.length;for(let i=2;i<n-2;i+=2){const dx=a[i]-px,dy=a[i+1]-py;if(dx*dx+dy*dy>d*d){o.push(a[i],a[i+1]);px=a[i];py=a[i+1]}}o.push(a[n-2],a[n-1]);return Float32Array.from(o)};
 TR=T.map(r=>{const n=(r.length-2)/2;const a=new Float64Array(n*2);let la=r[2],lo=r[3];a[0]=MX(lo/1e5);a[1]=MY(la/1e5);for(let i=1;i<n;i++){la+=r[2+i*2];lo+=r[3+i*2];a[i*2]=MX(lo/1e5);a[i*2+1]=MY(la/1e5)}let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;for(let i=0;i<a.length;i+=2){if(a[i]<x0)x0=a[i];if(a[i]>x1)x1=a[i];if(a[i+1]<y0)y0=a[i+1];if(a[i+1]>y1)y1=a[i+1]}const l3=thin(a,3e-7),lm=thin(l3,1.2e-6),l1=thin(lm,5e-6),lc=thin(l1,2.4e-5);return {d:r[0],c:r[1],p:a,l3,lm,l1,lc,bb:[x0,y0,x1,y1]}});
 TR.forEach((l,i)=>{(byDay[l.d]=byDay[l.d]||[]).push(i)});
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
function strokeArc(a,cols,w,dl,gap){const S=V.S;if(S>150000){ctx.beginPath();ctx.moveTo(a[0],a[1]);ctx.quadraticCurveTo(a[2],a[3],a[4],a[5]);ctx.strokeStyle=cols[0];ctx.lineWidth=w/S;ctx.globalAlpha=Math.min(ctx.globalAlpha,.5);ctx.stroke();return}const per=(dl+gap)/S,P=per*cols.length;cols.forEach((c,i)=>{ctx.beginPath();ctx.moveTo(a[0],a[1]);ctx.quadraticCurveTo(a[2],a[3],a[4],a[5]);ctx.setLineDash([dl/S,P-dl/S]);ctx.lineDashOffset=-per*i;ctx.strokeStyle=c;ctx.lineWidth=w/S;ctx.lineCap='round';ctx.stroke()});ctx.setLineDash([]);ctx.lineDashOffset=0}

/* ================= KARTE 1: REISEN ================= */
const R={w:new Set(WHO),m:new Set(MODES),y:null,color:'w'};
let RC=null;
function yearOn(y){return R.y==null||(Array.isArray(R.y)?y<=R.y[1]:y==R.y)}
function tripOn(t){return R.w.has(t.w)&&t.m.some(m=>R.m.has(m))&&yearOn(t.y)}
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
 const pairs=new Map();if(R.m.has('fly'))for(const t of on){for(const [x,y] of t.fl){const A=ptGroup(x,t),Bg=ptGroup(y,t);if(!A||!Bg||A==Bg)continue;const k=[A,Bg].sort((p,q)=>(p!='home')-(q!='home')||p.localeCompare(q)).join('>');let e=pairs.get(k);if(!e){e={k,ws:new Set()};pairs.set(k,e)}e.ws.add(t.w)}}
 RC={own:out,far,est,near,pairs:[...pairs.values()],on,onIds,st:{},ver:(RC?RC.ver:0)+1};
}
function gpos(g){if(g=='home')return [MX(HOME[1]),MY(HOME[0])];if(g.startsWith('p:')){const [a,b]=g.slice(2).split(',').map(Number);return [MX(b),MY(a)]}const G=D.groups.find(x=>x[0]==g);return [MX(G[3]),MY(G[2])]}
function areaLayer(cells,S){
 const G=.02,cellpx=G*1.4/360*S,k=Math.max(1,Math.round(7/cellpx));const key=k;if(cells._k===key)return cells._own;
 const agg=new Map();for(const [kk,c] of cells){const [a,b]=kk.split(',').map(Number);const A=Math.floor(a/k),Bb=Math.floor(b/k),K=A+','+Bb;let o=agg.get(K);if(!o){o={};agg.set(K,o)}for(const q in c)o[q]=(o[q]||0)+c[q]}
 const own={};for(const [kk,c] of agg){const [a,b]=kk.split(',').map(Number);let nb=0;for(const da of[-1,0,1])for(const db of[-1,0,1])if(agg.has((a+da)+','+(b+db)))nb++;if(nb<(k>1?2:3))continue;let best=null,bv=-1;for(const q in c)if(c[q]>bv){bv=c[q];best=q}(own[best]=own[best]||[]).push([MX((b+.5)*k*G*1.4),MY((a+.5)*k*G)])}
 cells._k=key;cells._own=own;cells._r=k*G*1.4/360*.8;return own}
function contentR(bb){
 drawBase();
 const S=V.S,col=R.color=='w'?WCOL:MCOL;
 const ZOOMED=S>=55000;

 // areas
 for(const cells of (S>=150000?[]:ZOOMED?RC.own.slice(0,R.color=='w'?1:0):RC.own)){const own=areaLayer(cells,S),r0=cells._r;
  for(const q in own){ctx.fillStyle=col[q];ctx.beginPath();const r=r0+1.4/S;for(const [x,y] of own[q]){ctx.moveTo(x+r,y);ctx.arc(x,y,r,0,7)}ctx.fill()}
  for(const q in own){ctx.fillStyle=tint(col[q],q=='Alltag'?.2:.3);ctx.beginPath();for(const [x,y] of own[q]){ctx.moveTo(x+r0,y);ctx.arc(x,y,r0,0,7)}ctx.fill()}
 }
 // far routes
 ctx.lineJoin='round';ctx.lineCap='round';
 const lw=Math.max(1.6,Math.min(3.2,S/6000))/S;
 const vb=[V.cx-V.W/2/S,V.cy-V.H/2/S,V.cx+V.W/2/S,V.cy+V.H/2/S];
 tileDraw(RC.st,li=>{const l=TR[li],r=D.days[l.d];if(!r||r[6]<0)return null;const t=tripById[r[6]];if(!RC.onIds.has(t.id))return null;if(!t.g&&!ZOOMED)return null;const m=TCLS[l.c];if(!R.m.has(m))return null;return (R.color=='w'?WCOL[t.w]:MCOL[m])+(t.g?'|f':'|n')},k=>k.endsWith('|f')?1:0,k=>{const f=k.endsWith('|f');ctx.strokeStyle=k.slice(0,7);ctx.lineWidth=f?lw:lw*.75;ctx.globalAlpha=1},bb);ctx.globalAlpha=1}
function drawR(){
 TKEY='R'+RC.ver+(V.S>=150000?'Z':V.S>=55000?'z':'');drawTiles(contentR);worldT();const S=V.S;ctx.globalAlpha=1;
 for(const [la,lo,rk,c] of RC.est){const r=rk/(40075*Math.cos(la*Math.PI/180));ctx.beginPath();ctx.arc(MX(lo),MY(la),r,0,7);ctx.fillStyle=tint(c,.82);ctx.globalAlpha=.55;ctx.fill();ctx.globalAlpha=1;ctx.setLineDash([1/S,5/S]);ctx.lineCap='round';ctx.strokeStyle=c;ctx.lineWidth=2.8/S;ctx.stroke();ctx.setLineDash([])}
 // flights
 for(const e of RC.pairs){const [A,Bg]=e.k.split('>');const [x1,y1]=gpos(A),[x2,y2]=gpos(Bg);const a=arcPts(x1,y1,x2,y2,A=='home'?.2:.18);strokeArc(a,R.color=='w'?WHO.filter(w=>e.ws.has(w)).map(w=>WCOL[w]):[MCOL.fly],2.4,8,6)}
 endWorld();placed.length=0;usedNames.clear();
 homeMark();
 // destinations
 RC.mbox=null;let off=null;
 for(const G of D.groups){const [g,name,la,lo,an,fs,major,gkm]=G;const ts=RC.on.filter(t=>t.g==g);if(!ts.length)continue;const [x,y]=toS(MX(lo),MY(la));if(x<-80||y<-40||x>V.W+80||y>V.H+40){if(gkm>1500&&(!off||gkm>off[0][7]))off=[G,ts];continue}
  const cs=R.color=='w'?WHO.filter(w=>ts.some(t=>t.w==w)).map(w=>WCOL[w]):[...new Set(ts.flatMap(t=>t.m).filter(m=>R.m.has(m)))].map(m=>MCOL[m]);const r=major?7.5:5.5;pieS(x,y,r,cs);
  lbl(name,an=='end'?x-r-6:an=='middle'?x:x+r+6,an=='middle'?y-r-6:y+5,fs,major?780:650,major?'#17122E':'#3C3560',an=='end'?'right':an=='middle'?'center':'left',4.5,true)}
 // near trips
 const near={};for(const t of RC.on){if(t.g)continue;const k=t.name;(near[k]=near[k]||{name:k,p:t.p,ts:[]}).ts.push(t)}
 const ns=Object.values(near).sort((a,b)=>b.ts.length-a.ts.length);
 for(const q of ns){const [x,y]=toS(MX(q.p[1]),MY(q.p[0]));if(x<-20||y<-20||x>V.W+20||y>V.H+20)continue;const r=Math.min(9,3+Math.sqrt(q.ts.length)*1.3)*(S>40000?1:.75);const cs=R.color=='w'?WHO.filter(w=>q.ts.some(t=>t.w==w)).map(w=>WCOL[w]):[...new Set(q.ts.flatMap(t=>t.m).filter(m=>R.m.has(m)))].map(m=>MCOL[m]);pieS(x,y,r,cs);q.sx=x;q.sy=y;q.r=r;if(S>45000)lbl(q.name,x+r+4,y+4,12,650,'#3C3560')}
 RC.ndots=ns;
 if(off)edgeBadge(off[0],off[1]);
 drawPlaceLabels();
}
function edgeBadge(G,ts){if(V.S>40000)return;const x=V.W-70,y=V.H-58;const c=R.color=='w'?WCOL[ts[0].w]:MCOL.fly;ctx.font='800 13px Inter, sans-serif';const [gx,gy]=toS(MX(G[3]),MY(G[2]));const ar=(gy>V.H?'↓':gy<0?'↑':'')+(gx>V.W?'→':gx<0?'←':'');const txt=G[1]+' '+ar+' '+fmt(G[7])+' km';RC.mg=[G[1],ts];const w=ctx.measureText(txt).width+20;ctx.fillStyle='#fff';ctx.strokeStyle=c;ctx.lineWidth=1.5;ctx.beginPath();ctx.roundRect(x-w,y-14,w,28,10);ctx.fill();ctx.stroke();ctx.fillStyle='#17122E';ctx.fillText(txt,x-w+10,y+5);RC.mbox=[x-w,y-14,x,y+14]}
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
function chipsR(){const cnt=w=>w=='Alltag'?'':D.trips.filter(t=>t.w==w).length;
 $('r-who').innerHTML=WHO.map(w=>`<button class="chip ${R.w.has(w)?'on':''}" style="--c:${WCOL[w]}" data-w="${esc(w)}"><i></i>${esc(w)} <b>${cnt(w)}</b></button>`).join('');
 $('r-mode').innerHTML=MODES.map(m=>`<button class="chip ${R.m.has(m)?'on':''}" style="--c:${MCOL[m]}" data-m="${m}"><i></i>${MNAME[m]}</button>`).join('');
 $('r-who').querySelectorAll('.chip').forEach(b=>b.onclick=()=>toggle(R.w,b.dataset.w,WHO,updR));
 $('r-mode').querySelectorAll('.chip').forEach(b=>b.onclick=()=>toggle(R.m,b.dataset.m,MODES,updR))}
function updR(){chipsR();buildR();sideR();legend();full()}
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
function dayOk(di){const I=dayInfo[di];if(!I)return false;if(SP.years&&!SP.years.has(I.y))return false;if(SP.wd=='wk'&&(I.dow==0||I.dow==6))return false;if(SP.wd=='we'&&I.dow>0&&I.dow<6)return false;return SP.cat.has(I.cat)}
function keyS(l){const I=dayInfo[l.d];return SP.color=='m'?TCLS[l.c]:SP.color=='y'?String(I.y):I.who}
function colS(k){return SP.color=='m'?MCOL[k]:SP.color=='y'?ycol(k):WCOL[k]}
function buildS(){
 SP.st={};SP.ver=(SP.ver||0)+1;const ch=new Map();
 if(0)TR.forEach((l,i)=>{if(!SP.modes.has(TCLS[l.c])||!dayOk(l.d))return;const k=keyS(l);const ck=k+'|'+(l.d>>3);let c=ch.get(ck);if(!c){c={k,ids:idList([]),bb:[1,1,0,0]};ch.set(ck,c)}c.ids.push(i);c.bb=[Math.min(c.bb[0],l.bb[0]),Math.min(c.bb[1],l.bb[1]),Math.max(c.bb[2],l.bb[2]),Math.max(c.bb[3],l.bb[3])]});
 const order=SP.color=='m'?['foot','road','rail']:SP.color=='w'?WORDER():null;
 SP.chunks=[...ch.values()].sort((a,b)=>order?order.indexOf(a.k)-order.indexOf(b.k):(+a.k)-(+b.k));
 SP.fl=[];if(SP.modes.has('fly')){const d0=dateOf(D.days[0][0]);for(const [ds,A,Bp] of D.flights){const di=Math.round((dateOf(ds)-d0)/864e5);if(!dayOk(di))continue;SP.fl.push([arcPts(MX(A[1]),MY(A[0]),MX(Bp[1]),MY(Bp[0])),SP.color=='m'?MCOL.fly:SP.color=='y'?ycol(dayInfo[di].y):WCOL[dayInfo[di].who]])}}
}
function contentS(bb){
 drawBase();const S=V.S,lw=S<300000?1/(S*(V.tf||1)):Math.min(2.4,S/250000)/S;
 ctx.lineWidth=lw;ctx.lineJoin='round';ctx.lineCap='round';ctx.globalAlpha=1;
 tileDraw(SP.st,li=>{const l=TR[li];return SP.modes.has(TCLS[l.c])&&dayOk(l.d)?keyS(l):null},k=>SP.color=='m'?['foot','road','rail'].indexOf(k):SP.color=='w'?WORDER().indexOf(k):+k,k=>{ctx.strokeStyle=S<300000?colS(k):tint(colS(k),.85)},bb);ctx.globalAlpha=1}
function drawS(){
 TKEY='S'+SP.ver;drawTiles(contentS);worldT();const S=V.S;
 ctx.globalAlpha=S>40000?.4:.75;for(const [a,c] of SP.fl)strokeArc(a,[c],S>40000?1.3:1.8,7,5);
 ctx.globalAlpha=1;endWorld();placed.length=0;usedNames.clear();homeMark();drawPlaceLabels();
}
function sideS(){
 const km={road:0,rail:0,foot:0,fly:0},I=[['road',1],['rail',2],['foot',3],['fly',4]];let nd=0;
 D.days.forEach((r,di)=>{if(!dayOk(di))return;let any=0;for(const [m,i] of I){if(!SP.modes.has(m))continue;km[m]+=r[i];if(r[i]>0)any=1}nd+=any});
 const tot=km.road+km.rail+km.foot+km.fly;
 if(!$('sp1'))$('s-stats').innerHTML=statHTML([['sp1','km in der Auswahl'],['sp2','Tage mit Bewegung'],['sp3','km pro Tag (Ø)'],['sp4','Erdumrundungen']]);
 count('sp1',tot);count('sp2',nd);count('sp3',nd?tot/nd:0);$('sp4').textContent=(tot/40075).toFixed(1).replace('.',',');
 $('s-split').innerHTML=mbars(km,MCOL,MNAME);
 const ys=DYEARS,all={};
 D.days.forEach((r,di)=>{const J=dayInfo[di];if(!SP.cat.has(J.cat))return;if(SP.wd=='wk'&&(J.dow==0||J.dow==6))return;if(SP.wd=='we'&&J.dow>0&&J.dow<6)return;const o=all[J.y]=all[J.y]||{road:0,rail:0,foot:0,fly:0};for(const [m,i] of I)if(SP.modes.has(m))o[m]+=r[i]});
 const mx=Math.max(1,...ys.map(y=>{const o=all[y]||{};return (o.road||0)+(o.rail||0)+(o.foot||0)+(o.fly||0)}));
 $('s-years').innerHTML=ys.map(y=>{const o=all[y]||{road:0,rail:0,foot:0,fly:0};const t=o.road+o.rail+o.foot+o.fly;const segs=['road','rail','foot','fly'].map(m=>o[m]?`<div style="height:${o[m]/mx*76}px;background:${SP.color=='y'?ycol(y):MCOL[m]}"></div>`:'').join('');return `<div class="yb${SP.years&&!SP.years.has(y)?' off':''}" data-y="${y}" title="${y}: ${fmt(t)} km"><span>${t?Math.round(t/1000)+'k':''}</span><div class="bar">${segs}</div><span>${String(y).slice(2)}</span></div>`}).join('');
 $('s-years').querySelectorAll('.yb').forEach(b=>b.onclick=()=>{const y=+b.dataset.y;SP.years=SP.years&&SP.years.size==1&&SP.years.has(y)?null:new Set([y]);updS()});
}
function chipsS(){const ms=['road','rail','foot','fly'];
 $('s-modes').innerHTML=ms.map(m=>`<button class="chip ${SP.modes.has(m)?'on':''}" style="--c:${MCOL[m]}" data-v="${m}"><i></i>${MNAME[m]}</button>`).join('');
 $('s-modes').querySelectorAll('.chip').forEach(b=>b.onclick=()=>toggle(SP.modes,b.dataset.v,ms,updS));
 $('s-cat').innerHTML=[['Alltag',WCOL.Alltag,'Alltag'],['Reise','#8B3DFF','Reisen']].map(([v,c,n])=>`<button class="chip ${SP.cat.has(v)?'on':''}" style="--c:${c}" data-v="${v}"><i></i>${esc(n)}</button>`).join('');
 $('s-cat').querySelectorAll('.chip').forEach(b=>b.onclick=()=>toggle(SP.cat,b.dataset.v,['Alltag','Reise'],updS))}
function updS(){chipsS();buildS();sideS();legend();full()}
segBind('s-color',v=>{SP.color=v;updS()});segBind('s-wd',v=>{SP.wd=v;updS()});

/* ================= KARTE 3: ORTE & TAGE ================= */
const O={day:null,pl:null,hit:[],q:''};
let PCOL={Zuhause:'#17122E',Arbeit:'#FFB000'};
function placeCat(p){if(p[9]=='Zuhause')return 'Zuhause';if(p[7]=='Work'||p[7]=='Inferred Work')return 'Arbeit';if(p[8]>=0&&tripById[p[8]])return tripById[p[8]].w;return 'Alltag'}
function catOfDay(di){const r=D.days[di];return r[6]>=0?tripById[r[6]].w:'Alltag'}
function drawO(){
 TKEY='O';drawTiles(()=>drawBase());worldT();const S=V.S;
 if(O.day!=null){ctx.lineJoin='round';ctx.lineCap='round';for(const i of byDay[O.day]||[]){const l=TR[i],a=l.p;ctx.beginPath();ctx.moveTo(a[0],a[1]);for(let j=2;j<a.length;j+=2)ctx.lineTo(a[j],a[j+1]);ctx.strokeStyle='#fff';ctx.lineWidth=7/S;ctx.stroke();ctx.strokeStyle=MCOL[TCLS[l.c]];ctx.lineWidth=3.6/S;ctx.stroke()}
  const ds=D.days[O.day][0];for(const [fd,A,Bp] of D.flights){if(fd!=ds)continue;strokeArc(arcPts(MX(A[1]),MY(A[0]),MX(Bp[1]),MY(Bp[0])),[MCOL.fly],2.4,8,6)}}
 endWorld();placed.length=0;usedNames.clear();O.hit=[];
 const fade=O.day!=null?.3:1,zf=Math.max(.55,Math.min(1.7,Math.log2(S/8000)/4));
 for(const p of O.pl){const [x,y]=toS(MX(p[1]),MY(p[0]));if(x<-30||y<-30||x>V.W+30||y>V.H+30)continue;const r=Math.min(24,(1.6+Math.sqrt(p[2])*.3)*zf);const c=PCOL[p.cat];ctx.globalAlpha=fade;ctx.beginPath();ctx.arc(x,y,r,0,7);ctx.fillStyle=tint(c,.55);ctx.fill();ctx.lineWidth=1.3;ctx.strokeStyle=c;ctx.stroke();O.hit.push([x,y,Math.max(r,9),p])}
 ctx.globalAlpha=1;homeMark();
 if(O.day==null){let n=0;const seen=new Set();for(const p of O.pl){if(n>50)break;if(p[9]=='Zuhause'||seen.has(p[9]))continue;const [x,y]=toS(MX(p[1]),MY(p[0]));if(x<0||y<0||x>V.W||y>V.H)continue;const r=Math.min(24,(1.6+Math.sqrt(p[2])*.3)*zf);if(lbl(p[9],x+r+3,y+4,12,650,'#3C3560')){seen.add(p[9]);n++}}}
 drawPlaceLabels();
}
function calLayout(){const c=$('calc'),w=c.parentElement.clientWidth;const yrs=DYEARS;const lab=28,cell=Math.max(4,Math.floor((w-lab)/53)),rowH=cell*7+10;return {c,w,yrs,lab,cell,rowH,h:rowH*yrs.length}}
function drawCal(){
 const L=calLayout(),c=L.c,dpr=Math.min(2,window.devicePixelRatio||1);c.style.height=L.h+'px';c.width=Math.round(L.w*dpr);c.height=Math.round(L.h*dpr);const g=c.getContext('2d');g.setTransform(dpr,0,0,dpr,0,0);g.clearRect(0,0,L.w,L.h);
 g.font='700 11px Inter, sans-serif';g.fillStyle='#5B5479';L.yrs.forEach((y,i)=>g.fillText(i==0?String(y):"'"+String(y).slice(2),0,i*L.rowH+L.cell*4+2));
 O.calHit=[];const d0=dateOf(D.days[0][0]);
 D.days.forEach((r,di)=>{const d=new Date(d0.getTime()+di*864e5),y=d.getUTCFullYear(),yi=y-DYEARS[0];const jan1=Date.UTC(y,0,1),doy=Math.round((d-jan1)/864e5),wd0=(new Date(jan1).getUTCDay()+6)%7,wd=(d.getUTCDay()+6)%7,col=Math.floor((doy+wd0)/7);
  const x=L.lab+col*L.cell,yy=yi*L.rowH+wd*L.cell;const cat=catOfDay(di),km=r[1]+r[2]+r[3]+r[4];let fill;
  if(cat!='Alltag')fill=WCOL[cat];else if(!r[7])fill='#F6F4FB';else if(km<1)fill='#E4E0F0';else{const t=Math.min(1,Math.log10(km)/2.6);fill=tint('#5B5479',.12+t*.6)}
  g.fillStyle=fill;g.fillRect(x,yy,L.cell-1,L.cell-1);if(O.day===di){g.lineWidth=2;g.strokeStyle='#17122E';g.strokeRect(x-1,yy-1,L.cell+1,L.cell+1)}O.calHit.push([x,yy,L.cell,di])});
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
 const tripDays=D.days.filter(r=>r[6]>=0).length,big=D.days.reduce((b,r)=>{const k=r[1]+r[2]+r[3]+r[4];return k>b?k:b},0);
 if(!$('o1'))$('o-stats').innerHTML=statHTML([['o1','Tage auf Reisen'],['o2','Tage nie weiter als 30 km'],['o3','Orte mit Aufenthalt'],['o4','km am längsten Tag']]);
 count('o1',tripDays);count('o2',D.days.filter(r=>r[7]&&r[6]<0&&r[5]<30).length);count('o3',O.pl.length);count('o4',big);
 $('o-legend').innerHTML=[...WHO.filter(w=>w!='Alltag').map(w=>[w,WCOL[w]]),['Alltag wenig','#D9D5E8'],['Alltag viel','#837CA0'],['keine Daten','#F6F4FB']].map(([n,c])=>`<span style="display:inline-flex;align-items:center;gap:6px"><i style="width:11px;height:11px;border-radius:2px;background:${c};box-shadow:inset 0 0 0 1px #E4DFF3"></i>${esc(n)}</span>`).join('');
 topO();
}
function topO(){const q=O.q.trim().toLowerCase();const list=O.pl.filter(p=>p[9]!='Zuhause'&&(!q||p[9].toLowerCase().includes(q))).slice(0,q?20:10);
 $('o-top').innerHTML=list.length?list.map((p,i)=>`<div class="trow" data-i="${i}"><span class="n">${i+1}</span><span class="nm">${esc(p[9])}</span><span class="d"><i style="background:${PCOL[p.cat]}"></i><em style="margin-left:6px">${fmt(p[2])} h</em></span></div>`).join(''):'<div class="empty">Kein Ort gefunden.</div>';
 $('o-top').querySelectorAll('.trow').forEach(r=>r.onclick=()=>{const p=list[+r.dataset.i];flyTo(MX(p[1]),MY(p[0]),Math.max(V.S,300000));placeDetail(p)})}
$('o-search').addEventListener('input',e=>{O.q=e.target.value;topO()});
function placeDetail(p){openDetail(`<h3>${esc(p[9])}</h3><div class="dsub"><span class="pill" style="background:${tint(PCOL[p.cat],.2)}">${p.cat}</span>${fmt(p[2])} Stunden · ${fmt(p[3])} Aufenthalte</div><div class="trip"><div class="s" style="background:${PCOL[p.cat]}"></div><div><div class="t1">Zum ersten Mal: ${dfmt(p[5])}</div><div class="t2">Zuletzt: ${dfmt(p[6])}${p[8]>=0&&tripById[p[8]]?' · Reise: '+esc(tripById[p[8]].name):''}</div></div></div>`)}
$('o-rand').onclick=()=>{const c=D.days.map((r,i)=>[r,i]).filter(([r])=>r[6]>=0&&(r[1]+r[2]+r[4])>40);const [r,i]=c[Math.floor(Math.random()*c.length)];selectDay(i)};
$('o-clear').onclick=()=>{O.day=null;closeDetail();drawCal();fit(45.75,5.9,47.85,10.6)};

/* ================= KARTE 4: GEMEINDEN ================= */
const GM={color:'y',hit:null};
const DCOL=['#EAE6F7','#CFC6F2','#AE9CEB','#8B70E0','#6A47D2','#4A28B8'];
function prepGem(G){GEM=G.map(m=>{const p=new Path2D();for(const r of m[8]){let x=0,y=0;for(let i=0;i<r.length;i+=2){x+=r[i];y+=r[i+1];const X=MX(x/1e4),Y=MY(y/1e4);i?p.lineTo(X,Y):p.moveTo(X,Y)}p.closePath()}return {id:m[0],name:m[1],kt:m[2],first:m[3],days:m[4],visit:m[5],la:m[6],lo:m[7],p,r:m[8]}})}
function gemFill(m){if(!m.first)return null;if(GM.color=='y')return ycol(+m.first.slice(0,4));if(GM.color=='d'){const i=m.days>=200?5:m.days>=50?4:m.days>=15?3:m.days>=5?2:m.days>=2?1:0;return DCOL[i]}return m.visit>0?'#00BFB3':'#B3ECE8'}
function contentG(){
 ctx.fillStyle='#FCFBFF';ctx.fill(B.land);
 const S=V.S;if(!GM.groups){GM.groups=new Map();for(const m of GEM){const c=gemFill(m);if(!c)continue;let p=GM.groups.get(c);if(!p){p=new Path2D();GM.groups.set(c,p)}p.addPath(m.p)}}
 for(const [c,p] of GM.groups){ctx.fillStyle=c;ctx.fill(p,'evenodd')}
 ctx.fillStyle='#C9D8F3';ctx.fill(B.lakes);ctx.strokeStyle='#AFC3EA';ctx.lineWidth=.7/S;ctx.stroke(B.lakes);
 ctx.strokeStyle='rgba(255,255,255,.9)';ctx.lineWidth=(S>150000?1:.6)/S;ctx.stroke(B.mun);
 ctx.strokeStyle='#6F6890';ctx.lineWidth=1.3/S;ctx.stroke(B.cant);ctx.strokeStyle='#17122E';ctx.lineWidth=1.8/S;ctx.stroke(B.chb)}
function drawG(){
 TKEY='G'+GM.color;drawTiles(contentG);worldT();const S=V.S;
 if(GM.hit){ctx.strokeStyle='#17122E';ctx.lineWidth=3/S;ctx.stroke(GM.hit.p)}
 endWorld();placed.length=0;usedNames.clear();homeMark();
 if(S>120000){const vis=GEM.filter(m=>{const [x,y]=toS(MX(m.lo),MY(m.la));return x>0&&y>0&&x<V.W&&y<V.H}).sort((a,b)=>b.days-a.days);for(const m of vis.slice(0,160)){const [x,y]=toS(MX(m.lo),MY(m.la));lbl(m.name,x,y,S>400000?12:11,600,'#3C3560','center',3)}}
 else drawPlaceLabels();
}
function gemAt(sx,sy){const [wx,wy]=toW(sx,sy);const lo=IX(wx),la=IY(wy);for(const m of GEM){if(Math.abs(m.la-la)>.25||Math.abs(m.lo-lo)>.35)continue;if(ctx.isPointInPath(m.p,wx,wy,'evenodd'))return m}return null}
function sideG(){
 const vis=GEM.filter(m=>m.first),stay=GEM.filter(m=>m.visit>0);
 if(!$('g1'))$('g-stats').innerHTML=statHTML([['g1','Gemeinden besucht'],['g2','Prozent der Schweiz'],['g3','mit Aufenthalt'],['g4','Kantone (von 26)']]);
 count('g1',vis.length);count('g2',vis.length/GEM.length*100,' %');count('g3',stay.length);count('g4',new Set(vis.map(m=>m.kt)).size);
 const ny={};vis.forEach(m=>{const y=+m.first.slice(0,4);ny[y]=(ny[y]||0)+1});const ys=DYEARS,mx=Math.max(1,...ys.map(y=>ny[y]||0));
 $('g-years').innerHTML=ys.map(y=>`<div class="yb" style="cursor:default"><span>${ny[y]||''}</span><div class="bar"><div style="height:${(ny[y]||0)/mx*76}px;background:${ycol(y)}"></div></div><span>${String(y).slice(2)}</span></div>`).join('');
 const kt={};GEM.forEach(m=>{const k=kt[m.kt]=kt[m.kt]||{n:0,v:0};k.n++;if(m.first)k.v++});
 const rows=Object.entries(kt).map(([k,o])=>[D.cantons[k]||k,o.v/o.n*100,o.v,o.n]).sort((a,b)=>b[1]-a[1]);
 $('g-cant').innerHTML=rows.map(([n,p,v,t])=>`<div class="mbar"><span title="${esc(n)}">${esc(n.split(' / ')[0])}</span><span class="tr"><div style="width:${p}%;background:#8B3DFF"></div></span><b>${v}/${t}</b></div>`).join('');
 legendG();
}
function legendG(){const L=$('g-legend');if(GM.color=='y')L.innerHTML='<div class="row" style="gap:4px">'+YCOL.map((c,i)=>`<span style="flex:1;height:10px;border-radius:3px;background:${c}"></span>`).join('')+'</div><div class="row" style="justify-content:space-between;font-size:12px;font-weight:600;color:#5B5479;margin-top:4px"><span>'+Y0+'</span><span>'+Y1+'</span></div>';else if(GM.color=='d')L.innerHTML='<div class="row" style="gap:4px">'+DCOL.map(c=>`<span style="flex:1;height:10px;border-radius:3px;background:${c}"></span>`).join('')+'</div><div class="row" style="justify-content:space-between;font-size:12px;font-weight:600;color:#5B5479;margin-top:4px"><span>1 Tag</span><span>200+ Tage</span></div>';else L.innerHTML='<div class="row" style="font-size:12px;font-weight:600;gap:14px"><span style="display:inline-flex;gap:6px;align-items:center"><i style="width:12px;height:12px;border-radius:3px;background:#00BFB3"></i>mit Aufenthalt</span><span style="display:inline-flex;gap:6px;align-items:center"><i style="width:12px;height:12px;border-radius:3px;background:#B3ECE8"></i>nur durchgefahren</span></div>'}
segBind('g-color',v=>{GM.color=v;GM.groups=null;legendG();legend();full()});

/* ================= KARTE 5: ZEITRAFFER ================= */
const Z={t:0,play:false,speed:7,cam:'follow',trail:'all',last:0,acc:0,cache:null,cacheT:-1,cum:null};
function prepZ(){Z.n=D.days.length;$('z-slider').max=Z.n-1;Z.cum=[];let s=0;for(const r of D.days){s+=r[1]+r[2]+r[3]+r[4];Z.cum.push(s)}
 const jumps=[['Start',D.days[0][0]],...D.trips.filter(t=>t.km>1500&&t.a>D.days[0][0]&&t.a<=D.days[D.days.length-1][0]).slice(0,10).map(t=>[t.name+' '+t.y,t.a])];
 $('z-jump').innerHTML=jumps.map(([n,d])=>`<button class="chip on" style="--c:#8B3DFF" data-d="${esc(d)}"><i></i>${esc(n)}</button>`).join('');
 $('z-jump').querySelectorAll('.chip').forEach(b=>b.onclick=()=>{const di=Math.round((dateOf(b.dataset.d)-dateOf(D.days[0][0]))/864e5);setZ(Math.max(0,di-1));Z.tr=null;full()})}
function setZ(t){Z.t=Math.max(0,Math.min(Z.n-1,t));$('z-slider').value=Math.floor(Z.t);infoZ()}
function infoZ(){const di=Math.floor(Z.t),r=D.days[di],cat=catOfDay(di),t=r[6]>=0?tripById[r[6]]:null;$('z-date').textContent=dfmt(r[0]);$('z-what').textContent=t?`${esc(t.w)} · ${esc(t.name)}`:(r[1]+r[2]+r[3]+r[4]>1?'Alltag':'kaum unterwegs');
 $('hud').style.display=TAB=='zeit'?'block':'none';$('hudd').textContent=dfmt(r[0]);$('huds').textContent=(t?t.name+' · ':'')+fmt(Z.cum[di])+' km seit '+Y0;
 if(!$('z1'))$('z-stats').innerHTML=statHTML([['z1','km bis zu diesem Tag'],['z2','Reisetage bis hier']]);$('z1').textContent=fmt(Z.cum[di]);let n=0;for(let i=0;i<=di;i++)if(D.days[i][6]>=0)n++;$('z2').textContent=fmt(n)}
function drawZ(){
 const ti=Math.floor(Z.t),from=Z.trail=='month'?Math.max(0,ti-30):0,upto=ti-6;
 const wk=Math.max(0,Math.floor(upto/14)*14),f0=Z.trail=='all'?0:Math.floor(from/14)*14;if(!Z.tr||Z.tr.wk!==wk||Z.tr.f0!==f0)Z.tr={wk,f0};
 TKEY='Z'+wk+'_'+f0;drawTiles(bb=>{drawBase();const S=V.S;ctx.globalAlpha=1;ctx.strokeStyle='#B5AECD';ctx.lineJoin='round';ctx.lineCap='round';ctx.lineWidth=S<300000?1/(S*(V.tf||1)):1.4/S;tileDraw(Z.tr,li=>{const d=TR[li].d;return d<wk&&d>=f0?'o':null},()=>0,()=>{},bb);ctx.globalAlpha=1});
 worldT();const S=V.S;const lw=Math.max(1,Math.min(2.4,S/40000))/S;ctx.lineJoin='round';ctx.lineCap='round';const LK=lodKey();
 ctx.globalAlpha=1;ctx.strokeStyle='#C3BDD8';ctx.lineWidth=lw;
 for(let d=Math.max(wk,from);d<upto;d++)for(const i of byDay[d]||[]){const a=TR[i][LK];ctx.beginPath();ctx.moveTo(a[0],a[1]);for(let j=2;j<a.length;j+=2)ctx.lineTo(a[j],a[j+1]);ctx.stroke()}
 ctx.globalAlpha=1;
 let lastPt=null;
 for(let d=Math.max(from,ti-6);d<=ti;d++){const age=ti-d;const ids=byDay[d]||[];for(const i of ids){const l=TR[i],a=l.p;ctx.beginPath();ctx.moveTo(a[0],a[1]);for(let j=2;j<a.length;j+=2)ctx.lineTo(a[j],a[j+1]);ctx.strokeStyle=MCOL[TCLS[l.c]];ctx.globalAlpha=1-age*.12;ctx.lineWidth=(age==0?3.4:2.2)/S;ctx.stroke();if(d==ti)lastPt=[a[a.length-2],a[a.length-1]]}
  const ds=D.days[d][0];for(const [fd,A,Bp] of D.flights){if(fd!=ds)continue;ctx.globalAlpha=1-age*.12;strokeArc(arcPts(MX(A[1]),MY(A[0]),MX(Bp[1]),MY(Bp[0])),[MCOL.fly],age==0?2.8:2,8,6);if(d==ti)lastPt=[MX(Bp[1]),MY(Bp[0])]}}
 ctx.globalAlpha=1;endWorld();placed.length=0;usedNames.clear();
 if(!lastPt){for(let d=ti;d>=0&&!lastPt;d--){const ids=byDay[d]||[];if(ids.length){const a=TR[ids[ids.length-1]].p;lastPt=[a[a.length-2],a[a.length-1]]}}}
 Z.pos=lastPt;homeMark();drawPlaceLabels();
 if(lastPt){const [x,y]=toS(lastPt[0],lastPt[1]);ctx.beginPath();ctx.arc(x,y,9,0,7);ctx.fillStyle='rgba(139,61,255,.18)';ctx.fill();ctx.beginPath();ctx.arc(x,y,5.5,0,7);ctx.fillStyle='#8B3DFF';ctx.fill();ctx.lineWidth=2;ctx.strokeStyle='#fff';ctx.stroke()}
}
function tickZ(ts){if(!Z.play)return;const dt=Math.min(.1,(ts-(Z.last||ts))/1000);Z.last=ts;const before=Math.floor(Z.t);setZ(Z.t+dt*Z.speed);
 if(Z.cam=='follow'&&Z.pos){const di=Math.floor(Z.t);const b=bboxOfDay(di);if(b){const w=Math.max(b[2]-b[0],b[3]-b[1]);const target=Math.min(400000,Math.max(9000,Math.min(V.W,V.H)*.6/Math.max(w,1e-6)));V.S=V.S+(target-V.S)*Math.min(1,dt*1.2);V.cx+=((b[0]+b[2])/2-V.cx)*Math.min(1,dt*1.5);V.cy+=((b[1]+b[3])/2-V.cy)*Math.min(1,dt*1.5)}}
 DRAW();scaleBar();if(Z.t>=Z.n-1){Z.play=false;setPlayZ()}else requestAnimationFrame(tickZ)}
function setPlayZ(){$('z-pico').setAttribute('d',Z.play?'M2.5 1.5H5.5V12.5H2.5ZM8.5 1.5H11.5V12.5H8.5Z':'M3 1.5L12 7L3 12.5Z')}
$('z-play').onclick=()=>{Z.play=!Z.play;setPlayZ();if(Z.play){if(Z.t>=Z.n-1)setZ(0);Z.last=0;requestAnimationFrame(tickZ)}};
$('z-slider').addEventListener('input',e=>{setZ(+e.target.value);if(!zq)zq=requestAnimationFrame(()=>{zq=null;DRAW()});clearTimeout(idleT);idleT=setTimeout(full,200)});let zq=null;
segBind('z-speed',v=>Z.speed=+v);segBind('z-cam',v=>Z.cam=v);segBind('z-trail',v=>{Z.trail=v;Z.tr=null;full()});

/* ================= Legende ================= */
function legend(){const L=$('legend');const ln=(c,n,dash)=>`<div><svg width="26" height="10" aria-hidden="true"><path d="M2 5H24" stroke="${c}" stroke-width="3.2" stroke-linecap="round" ${dash?'stroke-dasharray="5 4"':''}/></svg>${esc(n)}</div>`;let it=[];
 if(TAB=='reisen'){it=R.color=='w'?WHO.map(w=>ln(WCOL[w],w)):MODES.map(m=>ln(MCOL[m],MNAME[m],m=='fly'));it.push('<div><svg width="26" height="12" aria-hidden="true"><rect x="2" y="1" width="22" height="10" rx="5" fill="#E6E1F5" stroke="#8E86AE" stroke-width="1.2"/></svg>viele kurze Wege</div>')}
 else if(TAB=='spuren'){it=SP.color=='m'?['road','rail','foot','fly'].map(m=>ln(MCOL[m],MNAME[m],m=='fly')):SP.color=='w'?WORDER().map(w=>ln(WCOL[w],w)):[`<div><svg width="130" height="10" aria-hidden="true"><defs><linearGradient id="yg">${YCOL.map((c,i)=>`<stop offset="${i/10}" stop-color="${c}"/>`).join('')}</linearGradient></defs><rect x="0" y="2" width="130" height="6" rx="3" fill="url(#yg)"/></svg></div><div style="justify-content:space-between;width:130px"><span>${Y0}</span><span>${Y1}</span></div>`]}
 else if(TAB=='orte')it=[['Zuhause','#17122E'],['Arbeit','#FFB000'],['Alltag',WCOL.Alltag],...WHO.filter(w=>w!='Alltag').map(w=>['Reise '+w,WCOL[w]])].map(([n,c])=>`<div><svg width="14" height="14" aria-hidden="true"><circle cx="7" cy="7" r="5.5" fill="${tint(c,.55)}" stroke="${c}" stroke-width="1.3"/></svg>${esc(n)}</div>`);
 else if(TAB=='gemeinden')it=['<div>Gemeinde antippen für Details</div>'];
 else it=['road','rail','foot','fly'].map(m=>ln(MCOL[m],MNAME[m],m=='fly')).concat(['<div><svg width="26" height="10" aria-hidden="true"><path d="M2 5H24" stroke="#8A82AA" stroke-width="2" opacity=".6"/></svg>früher</div>']);
 L.innerHTML=it.join('')}

/* ================= Interaktion ================= */
const wrap=$('wrap');const ptrs=new Map();let pinch=null,moved=false,downAt=null;
wrap.addEventListener('wheel',e=>{if(e.target.closest('.detail'))return;e.preventDefault();const r=wrap.getBoundingClientRect();zoomAt(Math.exp(-e.deltaY*.0018),e.clientX-r.left,e.clientY-r.top)},{passive:false});
wrap.addEventListener('pointerdown',e=>{if(e.target.closest('.ctrl,.detail,.legend'))return;ptrs.set(e.pointerId,{x:e.clientX,y:e.clientY});moved=false;downAt={x:e.clientX,y:e.clientY};wrap.setPointerCapture(e.pointerId);wrap.classList.add('drag');if(ptrs.size==2){const [a,b]=[...ptrs.values()];pinch={d:Math.hypot(a.x-b.x,a.y-b.y)}}});
wrap.addEventListener('pointermove',e=>{
 const r=wrap.getBoundingClientRect(),sx=e.clientX-r.left,sy=e.clientY-r.top;
 if(!ptrs.size&&e.pointerType=='mouse'){if(TAB=='orte'&&O.hit){const h=O.hit.findLast(([hx,hy,hr])=>Math.hypot(hx-sx,hy-sy)<hr);h?showTip(e,`${h[3][9]} · ${fmt(h[3][2])} h`):hideTip()}else if(TAB=='gemeinden'&&GEM){const m=gemAt(sx,sy);m?showTip(e,m.name+(m.first?` · seit ${m.first.slice(0,4)}`:' · noch nie')):hideTip()}}
 if(!ptrs.has(e.pointerId))return;const prev=ptrs.get(e.pointerId),cur={x:e.clientX,y:e.clientY};ptrs.set(e.pointerId,cur);
 if(Math.hypot(cur.x-downAt.x,cur.y-downAt.y)>5)moved=true;
 if(ptrs.size==2&&pinch){const [a,b]=[...ptrs.values()];const d=Math.hypot(a.x-b.x,a.y-b.y);zoomAt(d/pinch.d,(a.x+b.x)/2-r.left,(a.y+b.y)/2-r.top);pinch.d=d;return}
 V.cx-=(cur.x-prev.x)/V.S;V.cy-=(cur.y-prev.y)/V.S;redraw()});
function up(e){ptrs.delete(e.pointerId);if(ptrs.size<2)pinch=null;if(!ptrs.size){wrap.classList.remove('drag');clearTimeout(idleT);idleT=setTimeout(full,60)}}
wrap.addEventListener('pointerup',e=>{const wasMoved=moved;up(e);if(wasMoved||e.target.closest('.ctrl,.detail,.legend'))return;const r=wrap.getBoundingClientRect(),sx=e.clientX-r.left,sy=e.clientY-r.top;
 if(TAB=='reisen'){const f=hitR(sx,sy);f?f():closeDetail()}
 else if(TAB=='orte'){const h=O.hit.findLast(([hx,hy,hr])=>Math.hypot(hx-sx,hy-sy)<hr);if(h)placeDetail(h[3])}
 else if(TAB=='gemeinden'){const m=gemAt(sx,sy);GM.hit=m;full();if(m)openDetail(`<h3>${esc(m.name)}</h3><div class="dsub">Kanton ${esc((D.cantons[m.kt]||'').split(' / ')[0])}</div>`+(m.first?`<div class="trip"><div class="s" style="background:${gemFill(m)}"></div><div><div class="t1">Zum ersten Mal: ${dfmt(m.first)}</div><div class="t2">an ${fmt(m.days)} ${m.days==1?'Tag':'Tagen'} dort oder durchgefahren${m.visit?' · mit Aufenthalten':''}</div></div></div>`:'<div class="empty">Hier wart ihr laut Zeitachse noch nie.</div>'),()=>{GM.hit=null;full()});else closeDetail()}});
wrap.addEventListener('pointercancel',up);
$('zin').onclick=()=>zoomAt(1.7,V.W/2,V.H/2);$('zout').onclick=()=>zoomAt(1/1.7,V.W/2,V.H/2);
$('zhome').onclick=()=>flyTo(MX(HOME[1]),MY(HOME[0]),260000);
$('zch').onclick=()=>fit(45.75,5.9,47.85,10.6);$('zeu').onclick=()=>fit(35,-6,60,28);

/* ================= Daten aus der App ================= */
function initData(){
 if(!D.days.length){const t=new Date().toISOString().slice(0,10);D.days=[[t,0,0,0,0,0,-1,0]]}
 HOME=D.home;WHO=D.who.slice();WCOL={};let pi=0;
 for(const w of WHO){if(w=='Alltag')WCOL[w]='#8A82AA';else if(w=='offen')WCOL[w]='#B8B0D6';else if(GROUPCOL[w]&&!D.persons.includes(w))WCOL[w]=GROUPCOL[w];else{while(Object.values(GROUPCOL).includes(PALETTE[pi%PALETTE.length])&&pi<PALETTE.length*2&&!D.persons.includes(w))pi++;WCOL[w]=PALETTE[pi++%PALETTE.length]}}
 PCOL={Zuhause:'#17122E',Arbeit:'#FFB000',...WCOL};
 R.w=new Set(WHO);
 TYEARS=[...new Set(D.trips.map(t=>t.y))].sort((a,b)=>a-b);
 const dy0=+D.days[0][0].slice(0,4),dy1=+D.days[D.days.length-1][0].slice(0,4);DYEARS=[];for(let y=dy0;y<=dy1;y++)DYEARS.push(y);
 Y0=dy0;Y1=Math.max(dy1,dy0+1);
 const ay=[...TYEARS,...DYEARS];$('brandyears').textContent=ay.length?Math.min(...ay)+'–'+Math.max(...ay):'';
 $('r-sub').textContent=`Alle ${fmt(D.trips.length)} Reisen${TYEARS.length?' seit '+TYEARS[0]:''} plus der Alltag. Lücken zwischen GPS-Punkten folgen echten Strassen, Flüge als Bögen.`;
 $('s-since').textContent=D.days[0][0].slice(0,4);
 $('s-note').textContent=`Zahlen aus den GPS-Daten ab ${dfmt(D.days[0][0])}. ${fmt(D.routed)} Lücken über das Strassennetz ergänzt; wo es nicht eindeutig ging, bleibt eine Lücke statt einer geraden Linie. Karte 1 zählt zusätzlich geschätzte Reisen ohne GPS.`;
}
function fitTrips(){const ps=(D.groups.length?D.groups.map(g=>[g[2],g[3]]).filter(p=>Math.hypot(p[0]-HOME[0],p[1]-HOME[1])<25):D.trips.filter(t=>t.p).map(t=>t.p));if(!ps.length){setFit(HOME[0]-2,HOME[1]-3,HOME[0]+2,HOME[1]+3);return}
 const la=ps.map(p=>p[0]).sort((a,b)=>a-b),lo=ps.map(p=>p[1]).sort((a,b)=>a-b);const q=a=>[a[Math.floor(a.length*.05)],a[Math.ceil(a.length*.95)-1]];const [a0,a1]=q(la),[o0,o1]=q(lo);
 setFit(Math.min(a0,HOME[0])-1,Math.min(o0,HOME[1])-1.5,Math.max(a1,HOME[0])+1,Math.max(o1,HOME[1])+1.5)}
function editTrip(dbid){try{if(window.parent!==window)window.parent.postMessage({type:'worldmap-edit',id:dbid},location.origin)}catch(e){}}

/* ================= Tabs ================= */
let TAB='reisen';
const NEEDS={reisen:['tracks'],spuren:['tracks'],orte:['tracks'],gemeinden:['gem'],zeit:['tracks']};
function need(k){if(!window.__T.t0)__T.t0=performance.now();if(ready[k])return ready[k];if(k=='tracks')ready[k]=loadJSON('api/atlas/tracks').then(T=>{const t=performance.now();__T.fetch=t-__T.t0;prepTracks(T);__T.prep=performance.now()-t});if(k=='gem')ready[k]=Promise.all([loadJSON('ch.json'),loadJSON('api/atlas/gem')]).then(([c,g])=>{const v=new Map(g.map(r=>[r[0],r]));prepGem(c.mun.map(([id,n,kt,la,lo,rings])=>{const r=v.get(id);return [id,n,kt,r?r[1]:null,r?r[2]:0,r?r[3]:0,la,lo,rings]}))});return ready[k]}
function setTab(t){
 TAB=t;closeDetail();hideTip();stopR();if(Z.play){Z.play=false;setPlayZ()}
 document.querySelectorAll('#tabs button').forEach(b=>b.classList.toggle('on',b.dataset.t==t));
 document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('on',p.id=='p-'+t));
 $('hud').style.display=t=='zeit'?'block':'none';
 try{history.replaceState(null,'','#'+t)}catch(e){}
 $('load').style.display='grid';
 Promise.all(NEEDS[t].map(need)).then(()=>{$('load').style.display='none';enter(t)}).catch(()=>{$('load').textContent='Daten konnten nicht geladen werden.'});
}
const fitted={};
function enter(t){
 legend();const _e=performance.now();setTimeout(()=>{__T.enter=performance.now()-_e},0);
 if(t=='reisen'){DRAW=drawR;chipsR();let _t=performance.now();buildR();__T.buildR=performance.now()-_t;sideR();if(!fitted.r){fitted.r=1;fitTrips()}}
 if(t=='spuren'){DRAW=drawS;chipsS();let _t=performance.now();buildS();__T.buildS=performance.now()-_t;_t=performance.now();sideS();__T.sideS=performance.now()-_t;if(!fitted.s){fitted.s=1;setFit(HOME[0]-.7,HOME[1]-1.4,HOME[0]+.6,HOME[1]+1.4)}}
 if(t=='orte'){DRAW=drawO;if(!O.pl)O.pl=D.places.map(p=>{p.cat=placeCat(p);return p}).sort((a,b)=>b[2]-a[2]);sideO();drawCal();if(!fitted.o){fitted.o=1;setFit(HOME[0]-.35,HOME[1]-.7,HOME[0]+.3,HOME[1]+.5)}}
 if(t=='gemeinden'){DRAW=drawG;sideG();if(!fitted.g){fitted.g=1;setFit(45.8,5.95,47.82,10.5,20)}}
 if(t=='zeit'){DRAW=drawZ;if(!Z.cum)prepZ();infoZ();if(!fitted.z){fitted.z=1;setFit(HOME[0]-.35,HOME[1]-.7,HOME[0]+.3,HOME[1]+.5)}}
 full();
}
document.querySelectorAll('#tabs button').forEach(b=>b.onclick=()=>setTab(b.dataset.t));
window.addEventListener('hashchange',()=>{const h=location.hash.slice(1);if(D&&NEEDS[h]&&h!=TAB)setTab(h)});
let rsz=null;window.addEventListener('resize',()=>{clearTimeout(rsz);rsz=setTimeout(()=>{sizeCV();full();if(TAB=='orte')drawCal()},120)});
window.__T={};
sizeCV();
Promise.all([loadJSON('api/atlas/core'),loadJSON('base.json'),loadJSON('api/atlas/labels')]).then(([c,b,l])=>{
 D=c;LAB=l;prepBase(b);initData();D.trips.forEach(t=>tripById[t.id]=t);
 const d0=dateOf(D.days[0][0]);D.days.forEach((r,i)=>{const d=new Date(d0.getTime()+i*864e5);const who=r[6]>=0?tripById[r[6]].w:'Alltag';dayInfo[i]={y:d.getUTCFullYear(),dow:d.getUTCDay(),who,cat:r[6]>=0?'Reise':'Alltag'}});
 const h=(location.hash||'').slice(1);setTab(NEEDS[h]?h:'reisen');
}).catch(()=>{$('load').textContent='Daten konnten nicht geladen werden.'});
}
