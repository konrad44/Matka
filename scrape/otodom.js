const { chromium } = require('playwright');
const fs = require('fs');

const BASE = 'https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/pomorskie/gdynia/gdynia/gdynia';
(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({
    locale: 'pl-PL',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    viewport: { width: 1366, height: 900 },
    ignoreHTTPSErrors: true,
  });
  const page = await ctx.newPage();
  let all = [];
  for (let p = 1; p <= 6; p++) {
    const url = `${BASE}?powierzchniaMin=80&limit=72&page=${p}&by=DEFAULT&direction=DESC`;
    console.error('GET', url);
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
    } catch (e) { console.error('goto fail', e.message); break; }
    // accept cookies if present
    try { await page.click('#onetrust-accept-btn-handler', { timeout: 4000 }); } catch {}
    await page.waitForTimeout(1500);
    const data = await page.evaluate(() => {
      const el = document.getElementById('__NEXT_DATA__');
      return el ? el.textContent : null;
    });
    if (!data) { console.error('no __NEXT_DATA__ on page', p); 
      console.error('title=', await page.title());
      break; }
    let json;
    try { json = JSON.parse(data); } catch(e){ console.error('parse fail'); break; }
    const items = json?.props?.pageProps?.data?.searchAds?.items
               || json?.props?.pageProps?.data?.searchAdsRandom?.items
               || [];
    console.error('page', p, 'items', items.length);
    if (!items.length) break;
    all = all.concat(items);
    const tot = json?.props?.pageProps?.data?.searchAds?.pagination?.totalResults;
    console.error('totalResults', tot);
  }
  fs.writeFileSync('data/_otodom_raw.json', JSON.stringify(all, null, 2));
  console.error('SAVED', all.length);
  await browser.close();
})();
