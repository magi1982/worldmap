async function drawTile(g){const look=LOOK,LAND=ringPath(AL.land,v);
 /* sea: deep blue, lighter and icier toward the poles */
 const LANDF=LAND;const mk=document.createElement('canvas');mk.width=Math.ceil(W);mk.height=Math.ceil(H);const mg=mk.getContext('2d');mg.fill(LANDF);const MD=mg.getImageData(0,0,mk.width,mk.height).data,MW=mk.width;const onLand=(x,y)=>{x|=0;y|=0;return x>=0&&y>=0&&x<MW&&y<mk.height&&MD[(y*MW+x)*4+3]>100};const ya=v.P(0,85)[1],yb=v.P(0,-85)[1],sg=g.createLinearGradient(0,ya,0,yb);const yN=(v.P(0,68)[1]-ya)/(yb-ya),yS=(v.P(0,-60)[1]-ya)/(yb-ya);sg.addColorStop(0,'#3a5f93');sg.addColorStop(yN,'#1a3f7a');sg.addColorStop(yS,'#173a75');sg.addColorStop(1,'#33598c');g.fillStyle=sg;g.fillRect(0,0,W,H);
 /* pack ice: plates, denser further north */
 const floe=(x,y,r,h)=>{g.beginPath();const n=6;for(let k=0;k<n;k++){const a=k/n*7+h*3,rr=r*(.6+.5*hash(k+9,h*999|0));const px=x+Math.cos(a)*rr*1.3,py=y+Math.sin(a)*rr*.8;k?g.lineTo(px,py):g.moveTo(px,py)}g.closePath()};
 const fst=Math.max(5,9*v.fz),[fx0,fy0]=v.P(-180,85);for(let j=Math.floor(-fy0/(fst*.78))-1;j<=Math.ceil((H-fy0)/(fst*.78))+1;j++)for(let i=Math.floor(-fx0/fst)-1;i<=Math.ceil((W-fx0)/fst)+1;i++){const x=fx0+i*fst,y=fy0+j*fst*.78,la=v.inv(x,y)[1],n=la>0?(la-73.5)/7:(-la-63)/5;if(n<=0)continue;const h=hash(i,j);if(h>Math.min(.95,n*.8))continue;if(onLand(x,y))continue;const jx=x+(hash(j,i)-.5)*8*v.fz,jy=y+(h-.5)*6*v.fz,r=(2.5+h*4.5)*v.fz;
  g.fillStyle='rgba(20,40,80,.35)';floe(jx+1.5,jy+1.5,r,h);g.fill();g.fillStyle=h<.5?'#eef5fb':'#d7e6f3';floe(jx,jy,r,h);g.fill()}
 g.lineJoin='round';g.lineCap='round';g.strokeStyle='#1f4a86';g.lineWidth=14;g.stroke(LAND);g.strokeStyle='#2a5f99';g.lineWidth=5;g.stroke(LAND);
 const rel=await relief(v,look,'welt');g.save();g.clip(LAND);g.drawImage(rel,0,0,W,H);
 const O=rel.obj,ow=rel.ow,ors=rel.ors,list=[];
 const at=(x,y)=>{const X=Math.round(x*ors),Y=Math.round(y*ors);return X<0||Y<0||X>=ow||Y>=rel.oh?0:O[Y*ow+X]};
 const [ox0,oy0]=v.P(0,0);const cell=(st,fn)=>{const sy=st*.86,j0=Math.floor(-oy0/sy)-1,j1=Math.ceil((H-oy0)/sy)+1;for(let j=j0;j<=j1;j++){const y=oy0+j*sy,off=(j&1)*st/2,i0=Math.floor((-ox0-off)/st)-1,i1=Math.ceil((W-ox0-off)/st)+1;for(let i=i0;i<=i1;i++){const x=ox0+off+i*st,h=hash(i*3+st*7|0,j*7-st|0),jx=x+(h-.5)*st*.6,jy=y+(hash(j+11,i-5)-.5)*st*.5;fn(jx,jy,h,at(jx,jy))}}};
 cell(5.5,(x,y,h,o)=>{if(o>=1&&o<=3)list.push({x,y,o,h})});
 cell(6,(x,y,h,o)=>{if(o!==9)return;const [lo,la]=v.inv(x,y),d=sn(lo*.9+3,la*1.6)+.5*sn(lo*3.1,la*4.2);if(h<.12+.32*Math.max(0,d))list.push({x,y,o,h:h*7.13%1})});
 cell(9,(x,y,h,o)=>{if(o===4&&h<.22)list.push({x,y,o,h});if(o===7&&h<.12)list.push({x,y,o,h})});
 cell(30,(x,y,h,o)=>{if(o===5&&h<.6)list.push({x,y,o,h});if(o===6&&h<.35)list.push({x,y,o:h<.12?8:6,h})});
 list.sort((a,b)=>(a.o===9?-1:0)-(b.o===9?-1:0)||a.y-b.y);for(const t of list)sprite(g,t);
 const LK=ringPath(AL.lakes,v);g.fillStyle=look.water;g.fill(LK);
 g.strokeStyle=look.water;for(const r of AL.rivers){const a=[];for(let i=1;i<r.length;i+=2)a.push(v.P(r[i],r[i+1]));g.lineWidth=Math.max(1,2.6-r[0]*.5);g.stroke(smoothPath(a))}
 g.restore();
 /* drifting ice floes around Greenland and Baffin: flat, no peaks */
 for(let k=0;k<70;k++){const lo=-70+hash(k,1)*50,la=59+hash(k,2)*16,[x,y]=v.P(lo,la);if(x<-5||y<-5||x>W+5||y>H+5||onLand(x,y))continue;const s=(1.4+hash(k,3)*2)*Math.min(3,Math.sqrt(Z));
  g.fillStyle='rgba(10,30,70,.35)';g.beginPath();g.ellipse(x+1,y+1,s*1.3,s*.8,hash(k,4)*3,0,7);g.fill();g.fillStyle='#e8f1f9';g.beginPath();g.ellipse(x,y,s*1.3,s*.8,hash(k,4)*3,0,7);g.fill()}
}
