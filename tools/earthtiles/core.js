let DATA=null;
let RGN=null,AL=null,TRK=null;const dist=(a,b,c,d)=>{const x=Math.sin((c-a)*R/2)**2+Math.cos(a*R)*Math.cos(c*R)*Math.sin((d-b)*R/2)**2;return 12742*Math.asin(Math.sqrt(x))};

/*SHARED*/
const PERM2=PERM;
/* ---- extra Alpine groups after real positions, plus one wide massif line that ties them together ---- */
const ALPX=[[3,70,-22,70.5,-24,68.5,-29,67.8,-34,66.3,-39,64.5,-42,62,-44,60.5],[2,45,-49,61.5,-51,64.5,-52.5,67.5,-53.5,70.5,-55,73],[3,70,-81,73.3,-75,71.5,-70,70,-67,67.5,-64.5,65.5],[3,80,-92,79.8,-85,80.8,-76,81.6,-70,82.2],[2,45,-64.5,59.5,-63.2,57.3],[2,90,-134,65,-129,63,-125,61,-123,59.5],[3,40,13.5,77.5,16,78.6,17.5,79.4],[2,40,52,71,55.5,73.5,60,75.5],[2,70,92,74,98,74.8,105,75.6],[2,160,91,68,95,69.2,99,68.5],[2,100,136,66.5,143,64.5,150,62.5],[2,80,160,64,166,66,172,66.5],[3,48,7.05,44.15,6.95,44.75,6.9,45.4,7.25,45.85,7.85,46.05,8.5,46.4,9.2,46.45,9.9,46.4,10.6,46.75,11.4,46.95,12.3,47.08,13.3,47.1,14.2,47.25],[2,80,6.2,44.2,6.7,45.2,7.4,45.95,8.4,46.4,9.6,46.55,11.0,46.85,12.5,47.0,13.8,47.15,15.4,47.45],
[2,18,6.9,46.55,7.4,46.75,8.0,46.85,8.6,47.0,9.2,47.15],[2,20,5.5,44.8,5.75,45.3,6.1,45.7,6.5,46.1],[3,25,8.0,46.45,8.5,46.4,9.0,46.35],[2,18,9.4,46.0,10.0,46.05],
[3,20,10.3,46.2,10.6,46.45,10.8,46.55],[3,25,12.0,47.08,12.7,47.08,13.3,47.05],[3,22,11.5,46.45,12.0,46.5,12.4,46.45],[3,18,6.75,45.8,7.05,45.95],[3,22,6.2,44.85,6.45,44.95],
[3,20,6.7,45.35,6.95,45.45],[3,18,9.6,47.0,10.2,46.85],[2,16,10.0,47.4,10.6,47.4],[2,16,11.0,47.42,11.6,47.45],[3,16,13.6,46.35,14.0,46.4],[2,14,14.0,46.45,14.8,46.45],
[3,16,7.6,46.0,7.9,45.95],[3,14,7.85,46.5,8.15,46.55],[2,14,8.3,46.7,8.7,46.75],[3,16,9.75,46.35,10.05,46.4],[2,18,7.0,44.15,7.6,44.25],[2,16,15.0,47.5,15.8,47.7]];
const RG2=RG.concat(ALPX.map(a=>{const p=a.slice(2);let x0=1e9,x1=-1e9,y0=1e9,y1=-1e9;for(let i=0;i<p.length;i+=2){x0=Math.min(x0,p[i]);x1=Math.max(x1,p[i]);y0=Math.min(y0,p[i+1]);y1=Math.max(y1,p[i+1])}const pd=a[1]/40+.4;return {c:a[0],w:a[1],p,bb:[x0-pd*1.5,x1+pd*1.5,y0-pd,y1+pd]}}));
function env(lo,la){let m=0;const k=Math.cos(la*R)*111.3;for(const r of RG2){if(lo<r.bb[0]||lo>r.bb[1]||la<r.bb[2]||la>r.bb[3])continue;const p=r.p;let dm=1e18;
 for(let i=0;i<p.length-2;i+=2){const ax=(p[i]-lo)*k,ay=(p[i+1]-la)*111.3,vx=(p[i+2]-p[i])*k,vy=(p[i+3]-p[i+1])*111.3,L=vx*vx+vy*vy||1;let t=-(ax*vx+ay*vy)/L;t=t<0?0:t>1?1:t;const ex=ax+vx*t,ey=ay+vy*t,d=ex*ex+ey*ey;if(d<dm)dm=d}
 const f=1-Math.sqrt(dm)/(r.w*1.9);if(f>0){const s=f*f*(3-2*f)*CW[r.c];if(s>m)m=s}}return m}
const vh=(x,y)=>PERM2[(PERM2[x&255]+y)&511]/127.5-1;
function noised(x,y){const ix=Math.floor(x),iy=Math.floor(y),fx=x-ix,fy=y-iy,ux=fx*fx*(3-2*fx),uy=fy*fy*(3-2*fy),dux=6*fx*(1-fx),duy=6*fy*(1-fy);
 const a=vh(ix,iy),b=vh(ix+1,iy),c=vh(ix,iy+1),d=vh(ix+1,iy+1),k1=b-a,k2=c-a,k4=a-b-c+d;return [a+k1*ux+k2*uy+k4*ux*uy,dux*(k1+k4*uy),duy*(k2+k4*ux)]}
function terrain(x,y,oct){let a=0,b=1,dx=0,dy=0,px=x,py=y;for(let o=0;o<oct;o++){const n=noised(px,py);dx+=n[1];dy+=n[2];a+=b*n[0]/(1+.6*(dx*dx+dy*dy));b*=.6;const qx=1.6*(.8*px-.6*py),qy=1.6*(.6*px+.8*py);px=qx;py=qy}return Math.max(0,Math.min(1,(a+.7)/1.6))}
const sleep=()=>Promise.resolve();

/* ---- view ---- */

const WX=lo=>(lo+180)/360,WY=la=>.5-Math.log(Math.tan(Math.PI/4+la*R/2))/(2*Math.PI);
function view(W,H,BOX){const sx=W/(WX(BOX[1])-WX(BOX[0])),sy=H/(WY(BOX[2])-WY(BOX[3])),s=Math.max(sx,sy),cx=(WX(BOX[0])+WX(BOX[1]))/2,cy=(WY(BOX[2])+WY(BOX[3]))/2;
 return {W,H,s,span:BOX[1]-BOX[0],P:(lo,la)=>[(WX(lo)-cx)*s+W/2,(WY(la)-cy)*s+H/2],kmpx:40075*Math.cos((BOX[2]+BOX[3])/2*R)/s,inv:(x,y)=>{const wx=(x-W/2)/s+cx,wy=(y-H/2)/s+cy;return [wx*360-180,Math.atan(Math.sinh((.5-wy)*2*Math.PI))/R]}}}
function ringPath(rings,v,closed=true,from=0){const p=new Path2D();for(const r of rings){for(let i=from;i<r.length;i+=2){const [x,y]=v.P(r[i],r[i+1]);i===from?p.moveTo(x,y):p.lineTo(x,y)}if(closed)p.closePath()}return p}
/* smooth curve through points (midpoint quadratic) */
function smoothPath(pts){const p=new Path2D();if(pts.length<2)return p;p.moveTo(pts[0][0],pts[0][1]);for(let i=1;i<pts.length-1;i++){const mx=(pts[i][0]+pts[i+1][0])/2,my=(pts[i][1]+pts[i+1][1])/2;p.quadraticCurveTo(pts[i][0],pts[i][1],mx,my)}const l=pts[pts.length-1];p.lineTo(l[0],l[1]);return p}

/* ---- the five looks ---- */
const LOOK={valley:[112,132,70],meadow:[124,140,76],forest:[60,88,48],alpine:[132,132,104],rock:[156,150,142],snow:[250,251,253],snowS:[176,190,214],amb:[6,10,28],light:[-.55,-.6,.6],
 sand:[218,172,110],sandD:[200,154,96],red:[196,118,70],redD:[176,100,60],dryrock:[168,128,92],steppe:[164,152,100],savanna:[150,140,82],jungle:[44,88,42],tundra:[140,136,100],lichen:[160,150,112],moss:[112,118,84],ice:[240,246,252],iceS:[188,206,230],floor:[62,90,48],
 water:'#173a75',waterL:'#2e5f9c',lab:'#17122E',steps:6,exag:2.2,snowOff:.3};
const LOOKS=[
 {key:'welt',n:'Die ganze Welt',d:'Alle Kontinente im selben Stil, deine Reiseziele leuchten, Flugbögen von zuhause zu den fernen Zielen.'},
 {key:'europa',n:'Europa mit deinen Spuren',d:'Deine GPS-Spuren als leuchtende pinke Linien über Wäldern, Bergen und Küsten.'},
 {key:'alpen',n:'Alpen mit deinen Spuren',d:'Nah dran: jede Fahrt durch die Täler und über die Pässe, dazu deine Ziele mit Namen.'}];

/* ---- relief for the whole view: lowland hills too, so nothing looks pasted on ---- */
const RELCACHE={};
async function heights(v,rk){const key=rk+v.W+'x'+v.H;if(RELCACHE[key])return RELCACHE[key];
 const rs=rk==='welt'?1:Math.min(1.5,devicePixelRatio||1),W=Math.round(v.W*rs),H=Math.round(v.H*rs),kmpx=v.kmpx/rs,oct=Math.max(3,Math.min(6,Math.ceil(Math.log(24/(1.3*kmpx))/Math.log(1.6))));
 const st=6,gw=Math.ceil(W/st)+2,gh=Math.ceil(H/st)+2,E=new Float32Array(gw*gh);for(let j=0;j<gh;j++)for(let i=0;i<gw;i++){const [lo,la]=v.inv(i*st/rs,j*st/rs);E[j*gw+i]=env(lo,la)}
 const Hh=new Float32Array(W*H),M=new Float32Array(W*H),N1=new Float32Array(W*H),N2=new Float32Array(W*H),LA=new Float32Array(H),BM=new Uint8Array(W*H),LO=new Float32Array(W*H);
 const bg=new Uint8Array(gw*gh);for(let j=0;j<gh;j++)for(let i=0;i<gw;i++){const [lo,la]=v.inv(i*st/rs,j*st/rs);bg[j*gw+i]=biome(lo,la)}
 for(let y=0;y<H;y++){const gy=y/st,j0=Math.floor(gy),fy=gy-j0;LA[y]=v.inv(0,y/rs)[1];
  for(let x=0;x<W;x++){const gx=x/st,i0=Math.floor(gx),fx=gx-i0,k=j0*gw+i0,m=(E[k]*(1-fx)+E[k+1]*fx)*(1-fy)+(E[k+gw]*(1-fx)+E[k+gw+1]*fx)*fy,i=y*W+x;M[i]=m;
   const [lo,lat]=v.inv(x/rs,y/rs),cl=Math.cos(lat*R),X=lo*cl/.22,Y=lat/.22;
   const t=terrain(X,Y,m>.03?oct:3),r1=1-Math.abs(sn(X*.35,Y*.35)),amp=.7+.5*(sn(X*.07+3,Y*.07)+1)/2*(1-Math.min(1,m*1.6))+ .35*Math.min(1,m*1.6);
   const mt=Math.pow(m,.55)*amp*(.14+.8*t+.22*r1*r1);{const a=bg[k],b2=bg[k+1],c2=bg[k+gw],d2=bg[k+gw+1];BM[i]=(a===b2&&a===c2&&a===d2)?a:biome(lo,lat)}LO[i]=lo;
   Hh[i]=mt+.012*t;/* gentle hills everywhere */const q=10.6/v.span;N1[i]=sn(lo*3.2*q,lat*3.2*q);N2[i]=sn(lo*7*q+4,lat*7*q)+.3*sn(lo*16*q,lat*16*q+3)}
  if(y%30===0)await sleep()}
 return RELCACHE[key]={W,H,rs,kmpx,Hh,M,N1,N2,LA,BM,LO}}
async function relief(v,look,rk){const D=await heights(v,rk),{W,H,kmpx,Hh,M,N1,N2,LA,BM,LO}=D,c=document.createElement('canvas');c.width=W;c.height=H;const img=c.getContext('2d').createImageData(W,H),o=img.data;
 const OBJ=new Uint8Array(W*H),ex=4.2/kmpx*1.9*look.exag,[lx,ly,lz]=look.light;const hb=new Uint8Array(W*H);const mixc=(a,b,t)=>[a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,a[2]+(b[2]-a[2])*t];
 for(let y=1;y<H-1;y++){const al=Math.abs(LA[y]),snowKm=Math.max(1.6,3.35-Math.max(0,al-42)*.055+Math.max(0,36-al)*.06+look.snowOff);
  for(let x=1;x<W-1;x++){const i=y*W+x,h=Hh[i],hk=h*4.2,dx=(Hh[i+1]-Hh[i-1])*.5*ex,dy=(Hh[i+W]-Hh[i-W])*.5*ex,nl=Math.hypot(dx,dy,1);
   const L=Math.max(0,(-dx*lx-dy*ly+lz)/nl/Math.hypot(lx,ly,lz)),slope=Math.hypot(dx,dy),n1=N1[i],n2=N2[i];let col;
   /* land cover: meadows and forests as crisp patches from noise, rising into alpine and rock */
   const bm=BM[i],dry=bm===BI.desert,outback=dry&&LO[i]>100,stp=bm===BI.steppe||bm===BI.savanna,cold=bm===BI.tundra||bm===BI.boreal;
   const woody=bm===BI.forest||bm===BI.boreal||bm===BI.jungle||bm===BI.temp||bm===BI.farm||bm===BI.med;
   const forest=woody&&(n1*.9+n2*.25>(bm===BI.forest||bm===BI.boreal||bm===BI.jungle?(hk<1.3?.2:-.1):(hk<.4?.55:hk<1.3?.15:-.15)))&&hk<2.0;
   const ice=bm===BI.ice;const tun=n1>.35?look.lichen:n2>.55?look.moss:look.tundra;
   const lowc=dry?(outback?look.red:look.sand):stp?(bm===BI.savanna?look.savanna:look.steppe):bm===BI.tundra?tun:look.valley;
   const fc=look.floor;
   if(forest&&hk<2)OBJ[i]=bm===BI.boreal||(hk>1.2&&bm!==BI.jungle)?2:bm===BI.jungle?3:1;else if(hk<1.1){if(bm===BI.tundra||(bm===BI.boreal&&!forest))OBJ[i]=9;else if(dry)OBJ[i]=outback?6:5;else if(bm===BI.savanna)OBJ[i]=4;else if(stp)OBJ[i]=7}
   if(hk<1.2)col=forest?fc:lowc;
   else if(hk<2.1)col=forest?fc:dry?look.dryrock:(hk<1.7?(stp||cold?lowc:look.meadow):look.alpine);
   else if(hk<2.6)col=dry||stp?look.dryrock:look.alpine;else col=dry?look.dryrock:look.rock;
   if(slope>1.6&&hk>1.5)col=dry?look.dryrock:look.rock;
   const snowAt=snowKm+n1*.15+Math.max(0,slope-1.3)*.5;let snow=hk>snowAt;
   if(ice){snow=true;col=mixc(look.iceS,look.ice,Math.min(1,L*1.2));if(n2>.7)col=mixc(col,look.iceS,.35)}
   if(snow&&!ice)col=mixc(look.snowS,look.snow,Math.min(1,L*1.25));
   let Lq=look.steps?Math.round(L*look.steps)/look.steps:L;const mw=Math.min(1,M[i]/.05);Lq=.78+(Lq-.78)*mw;hb[i]=Math.min(6,Math.floor(hk/.55));const sh=snow?.62+.42*Lq:.32+.9*Lq;if(snow&&dry&&hk<snowAt+.5)snow=false;let r=col[0]*sh+look.amb[0]*(1-Lq),g=col[1]*sh+look.amb[1]*(1-Lq),b=col[2]*sh+look.amb[2]*(1-Lq);
   o[i*4]=r;o[i*4+1]=g;o[i*4+2]=b;o[i*4+3]=255}
  if(y%60===0)await sleep()}
 if(false){for(let y=1;y<H-1;y++)for(let x=1;x<W-1;x++){const i=y*W+x;if(hb[i]>0&&(hb[i]!==hb[i+1]||hb[i]!==hb[i+W])){const k=i*4;o[k]*=.55;o[k+1]*=.55;o[k+2]*=.6}}}
 c.getContext('2d').putImageData(img,0,0);c.obj=OBJ;c.ow=W;c.oh=H;c.ors=D.rs;return c}

function sprite(g,t){const {x,y,o,h}=t;
 if(o===9){/* every lake its own shape: 7 corners with random radius, rounded */const w=1.4+h*3.2,n=7,pts=[];for(let k=0;k<n;k++){const a=k/n*6.283+h*5,r=w*(.5+.9*hash(k*13+7,h*99991|0));pts.push([x+Math.cos(a)*r*1.25,y+Math.sin(a)*r*.85])}
  g.fillStyle='#1d4880';g.beginPath();for(let k=0;k<n;k++){const p=pts[k],q=pts[(k+1)%n],mx=(p[0]+q[0])/2,my=(p[1]+q[1])/2;k?g.quadraticCurveTo(p[0],p[1],mx,my):g.moveTo(mx,my)}const p0=pts[0],q0=pts[1];g.quadraticCurveTo(p0[0],p0[1],(p0[0]+q0[0])/2,(p0[1]+q0[1])/2);g.fill();return}
 if(o===1){const r=4.2+h*1.6;g.fillStyle='rgba(20,60,30,.35)';g.beginPath();g.ellipse(x+2,y+2.5,r,r*.7,0,0,7);g.fill();
  g.fillStyle=h<.5?'#3c5a2c':'#47663a';g.beginPath();g.arc(x,y,r,0,7);g.fill();g.fillStyle='rgba(15,30,15,.45)';g.beginPath();g.arc(x+r*.25,y+r*.25,r*.8,-.3,2.1);g.fill();
  g.fillStyle='rgba(170,190,120,.35)';g.beginPath();g.arc(x-r*.35,y-r*.35,r*.38,0,7);g.fill()}
 else if(o===2){const s=7+h*3;g.fillStyle='rgba(20,50,30,.35)';g.beginPath();g.ellipse(x+2.5,y+1,s*.35,s*.15,0,0,7);g.fill();
  g.fillStyle='#34553a';g.beginPath();g.moveTo(x,y-s);g.lineTo(x+s*.36,y);g.lineTo(x-s*.36,y);g.closePath();g.fill();g.fillStyle='#24402a';g.beginPath();g.moveTo(x,y-s);g.lineTo(x+s*.36,y);g.lineTo(x+s*.05,y);g.closePath();g.fill()}
 else if(o===3){const r=5.5+h*2;g.fillStyle='rgba(10,50,25,.35)';g.beginPath();g.ellipse(x+2,y+3,r,r*.7,0,0,7);g.fill();g.fillStyle='#2f5a2c';g.beginPath();g.arc(x,y,r,0,7);g.fill();g.fillStyle='rgba(10,50,25,.4)';g.beginPath();g.arc(x+r*.3,y+r*.3,r*.75,-.3,2.1);g.fill();g.fillStyle='rgba(150,190,110,.35)';g.beginPath();g.arc(x-r*.35,y-r*.4,r*.35,0,7);g.fill()}
 else if(o===4){g.fillStyle='rgba(80,60,20,.3)';g.beginPath();g.ellipse(x+3,y+2,6,2.2,0,0,7);g.fill();g.strokeStyle='#7a5a32';g.lineWidth=1.4;g.beginPath();g.moveTo(x,y+1);g.lineTo(x,y-4);g.stroke();
  g.fillStyle='#5f6e34';g.beginPath();g.ellipse(x,y-5,6,2.4,0,0,7);g.fill();g.fillStyle='#78884a';g.beginPath();g.ellipse(x-1.2,y-5.8,4,1.3,0,0,7);g.fill()}
 else if(o===7){g.fillStyle='#7d7f4a';g.beginPath();g.arc(x,y,2.2,0,7);g.arc(x+2.4,y+.6,1.8,0,7);g.fill()}
 else if(o===5){/* crescent dune: lit windward slope, shaded slip face */const w=16+h*9,a=-.3+h*.25;g.save();g.translate(x,y);g.rotate(a);
  g.fillStyle='#e6bf82';g.beginPath();g.moveTo(-w,2);g.quadraticCurveTo(0,-w*.75,w,2);g.quadraticCurveTo(0,-w*.15,-w,2);g.fill();
  g.fillStyle='#b98a52';g.beginPath();g.moveTo(-w,2);g.quadraticCurveTo(0,-w*.15,w,2);g.quadraticCurveTo(0,w*.25,-w,2);g.fill();g.restore()}
 else if(o===6){const w=5+h*6;g.fillStyle='rgba(120,50,20,.35)';g.beginPath();g.ellipse(x+3,y+2,w,w*.35,0,0,7);g.fill();g.fillStyle='#8a9050';g.beginPath();g.arc(x-w,y,2,0,7);g.arc(x+w*.8,y+3,1.8,0,7);g.fill()}
 else if(o===8){/* red rock mesa */const w=7+h*20;g.fillStyle='rgba(110,45,20,.35)';g.beginPath();g.ellipse(x+4,y+3,w,w*.4,0,0,7);g.fill();g.fillStyle='#9a4a28';g.beginPath();g.ellipse(x,y,w,w*.38,0,0,7);g.fill();
  g.fillStyle='#c26a3c';g.beginPath();g.ellipse(x-w*.12,y-w*.12,w*.8,w*.26,0,0,7);g.fill()}}
function pinTop(g,x,y,col){g.fillStyle='rgba(0,0,0,.3)';g.beginPath();g.ellipse(x+2,y+1,5,2,0,0,7);g.fill();g.fillStyle=col;g.strokeStyle='#17122E';g.lineWidth=1.6;g.beginPath();g.moveTo(x,y);g.bezierCurveTo(x-3,y-6,x-7,y-8,x-7,y-13);g.arc(x,y-13,7,Math.PI,0);g.bezierCurveTo(x+7,y-8,x+3,y-6,x,y);g.fill();g.stroke();g.fillStyle='#fff';g.beginPath();g.arc(x,y-13,2.6,0,7);g.fill()}
function homeTop(g,x,y){g.fillStyle='#FF2DAA';g.strokeStyle='#17122E';g.lineWidth=2;g.beginPath();g.moveTo(x-9,y+5);g.lineTo(x-9,y-3);g.lineTo(x,y-12);g.lineTo(x+9,y-3);g.lineTo(x+9,y+5);g.closePath();g.fill();g.stroke();g.fillStyle='#17122E';g.fillRect(x-2,y-1,4,6)}