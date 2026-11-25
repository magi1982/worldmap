/* Render the Earth picture tiles with a headless Chrome (run on a build machine, never on Home Assistant).
     node tools/earthtiles/gen.js [maxZoom=5]
   needs: puppeteer (PUPPETEER_PATH) and Chrome (CHROME_PATH); output: tools/earthtiles/out/<z>/<x>/<y>.webp
   Copy z0–maxZoom into worldmap/app/worldmap/static/tiles/earth/ afterwards. */
const puppeteer=require(process.env.PUPPETEER_PATH||'puppeteer');const fs=require('fs');const http=require('http');const path=require('path');
const DIR=__dirname,MAXZ=Math.min(9,+(process.argv[2]||5));
/* one page with all drawing code in it */
const page=fs.readFileSync(path.join(DIR,'render.tpl.html'),'utf8').replace('/*SHARED*/',fs.readFileSync(path.join(DIR,'shared.js'),'utf8')).replace('/*CORE*/',fs.readFileSync(path.join(DIR,'core.js'),'utf8')).replace('/*DRAW*/',fs.readFileSync(path.join(DIR,'drawtile.js'),'utf8'));
fs.writeFileSync(path.join(DIR,'render.html'),page);
const ALLOWED=new Set(['/render.html','/welt.json','/full.json']);
const srv=http.createServer((q,r)=>{const u=q.url.split('?')[0];if(!ALLOWED.has(u)){r.statusCode=404;return r.end()}fs.readFile(path.join(DIR,u),(e,d)=>{if(e){r.statusCode=404;return r.end()}r.end(d)})}).listen(8777,'127.0.0.1');
(async()=>{const b=await puppeteer.launch({executablePath:process.env.CHROME_PATH||undefined,args:['--no-sandbox']});const p=await b.newPage();p.on('pageerror',e=>console.log('E',e.message));
 await p.goto('http://127.0.0.1:8777/render.html');await p.evaluate(()=>load());let cnt=0;const t0=Date.now();
 for(let z=0;z<=MAXZ;z++){const N=2**z,n=Math.min(8,N);for(let by=0;by<N;by+=n)for(let bx=0;bx<N;bx+=n){
  const out=await p.evaluate((z,bx,by,n)=>renderBlock(z,bx,by,n,48),z,bx,by,n);
  for(const [k,u] of Object.entries(out)){const [zz,xx,yy]=k.split('/').map(Number);if(xx>=N||yy>=N)continue;fs.mkdirSync(path.join(DIR,'out',''+zz,''+xx),{recursive:true});fs.writeFileSync(path.join(DIR,'out',''+zz,''+xx,yy+'.webp'),Buffer.from(u.split(',')[1],'base64'));cnt++}}
  console.log('zoom',z,'done,',cnt,'tiles,',((Date.now()-t0)/1000).toFixed(0)+'s')}
 await b.close();srv.close()})();
