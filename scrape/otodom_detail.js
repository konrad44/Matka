const { chromium } = require('playwright');
const fs = require('fs');
const raw = JSON.parse(fs.readFileSync('data/_otodom_raw.json','utf8'));
const seen = new Map();
for (const it of raw) {
  const a = it.areaInSquareMeters || 0;
  if (a >= 80 && !seen.has(it.id)) seen.set(it.id, it);
}
const list = [...seen.values()];
console.error('to fetch', list.length);

(async () => {
  const b = await chromium.launch({headless:true});
  const c = await b.newContext({locale:'pl-PL', ignoreHTTPSErrors:true,
    userAgent:'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'});
  const p = await c.newPage();
  let accepted=false;
  const out=[];
  for (const it of list) {
    const url='https://www.otodom.pl/pl/oferta/'+it.slug;
    let coords=null;
    try {
      await p.goto(url,{waitUntil:'domcontentloaded',timeout:45000});
      if(!accepted){ try{await p.click('#onetrust-accept-btn-handler',{timeout:3000}); accepted=true;}catch{} }
      coords = await p.evaluate(()=>{
        const el=document.getElementById('__NEXT_DATA__');
        if(el){ const m=el.textContent.match(/"latitude":\s*(5[0-9.]+)\s*,\s*"longitude":\s*(1[0-9.]+)/); if(m) return [parseFloat(m[1]),parseFloat(m[2])]; }
        for(const s of document.scripts){ const m=s.textContent.match(/"latitude":\s*(5[0-9.]+).{0,40}?"longitude":\s*(1[0-9.]+)/); if(m) return [parseFloat(m[1]),parseFloat(m[2])]; }
        return null;
      });
    } catch(e){ console.error('fail',it.slug,e.message); }
    const st=it.location?.address?.street;
    const district=(it.location?.reverseGeocoding?.locations||[]).filter(x=>x.locationLevel==='district').map(x=>x.name)[0]||'';
    out.push({
      id: it.id,
      title: it.title,
      url: 'https://www.otodom.pl/pl/oferta/'+it.slug,
      area: it.areaInSquareMeters,
      rooms: it.roomsNumber,
      price: it.totalPrice?.value || null,
      pricePerM2: it.pricePerSquareMeter?.value || null,
      street: st ? (st.name + (st.number? ' '+st.number:'')) : '',
      district,
      isPrivate: it.isPrivateOwner,
      lat: coords?coords[0]:null,
      lon: coords?coords[1]:null,
    });
    console.error(out.length, it.areaInSquareMeters+'m2', district, coords?coords.join(','):'NO-COORDS');
    await p.waitForTimeout(400);
  }
  fs.writeFileSync('data/_otodom_detail.json', JSON.stringify(out,null,2));
  console.error('SAVED', out.length, 'withCoords', out.filter(x=>x.lat).length);
  await b.close();
})();
