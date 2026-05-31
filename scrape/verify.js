const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({headless:true});
  const c = await b.newContext({ignoreHTTPSErrors:true, viewport:{width:1280,height:850}});
  const p = await c.newPage();
  const errs=[];
  p.on('console',m=>{ if(m.type()==='error') errs.push(m.text()); });
  p.on('pageerror',e=>errs.push('PAGEERR: '+e.message));
  await p.goto('file://'+process.cwd()+'/index.html',{waitUntil:'networkidle',timeout:45000});
  await p.waitForTimeout(2500);
  const stats = await p.evaluate(()=>({
    markers: document.querySelectorAll('.leaflet-marker-icon').length,
    rings: document.querySelectorAll('path.ring-skm, path.ring-studio').length,
    ringSkm: document.querySelectorAll('path.ring-skm').length,
    ringStudio: document.querySelectorAll('path.ring-studio').length,
    tiles: document.querySelectorAll('.leaflet-tile-loaded').length,
    sub: document.getElementById('sub').textContent,
    fillComputed: (()=>{const el=document.querySelector('path.ring-skm');return el?getComputedStyle(el).fill:null;})()
  }));
  console.log(JSON.stringify(stats,null,2));
  console.log('ERRORS:', errs.length? errs.join('\n'):'none');
  await p.screenshot({path:'scrape/preview.png'});
  // open a studio popup to check link
  await p.click('.marker-num >> nth=10').catch(()=>{});
  await p.waitForTimeout(800);
  await p.screenshot({path:'scrape/preview_popup.png'});
  await b.close();
})();
