const { chromium } = require('playwright');
const fs = require('fs');
const sleep = ms => new Promise(r=>setTimeout(r,ms));
const det = JSON.parse(fs.readFileSync('data/_otodom_detail.json','utf8'));
const todo = det.filter(d=>!d.lat);
console.error('retry', todo.length);
(async () => {
  const b = await chromium.launch({headless:true});
  let done=0;
  for (const d of todo) {
    const c = await b.newContext({locale:'pl-PL', ignoreHTTPSErrors:true,
      userAgent:'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15'});
    const p = await c.newPage();
    let coords=null;
    try {
      await p.goto(d.url,{waitUntil:'networkidle',timeout:50000});
      try{await p.click('#onetrust-accept-btn-handler',{timeout:2500});}catch{}
      await sleep(1500);
      coords = await p.evaluate(()=>{
        for(const s of document.scripts){ const m=s.textContent.match(/"latitude":\s*(5[0-9.]+).{0,40}?"longitude":\s*(1[0-9.]+)/); if(m) return [parseFloat(m[1]),parseFloat(m[2])]; }
        return null;
      });
    } catch(e){ console.error('fail',d.id,e.message); }
    if(coords){ d.lat=coords[0]; d.lon=coords[1]; d.coordSource='otodom'; }
    console.error(++done+'/'+todo.length, d.district, coords?coords.join(','):'STILL-NO');
    await c.close();
    await sleep(1000);
  }
  fs.writeFileSync('data/_otodom_detail.json', JSON.stringify(det,null,2));
  console.error('withCoords now', det.filter(x=>x.lat).length,'/',det.length);
  await b.close();
})();
