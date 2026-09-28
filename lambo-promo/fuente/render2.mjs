import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import fs from 'fs';
const [,, mode, W, H, out, fps='30'] = process.argv;
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: +W, height: +H } });
await page.goto('file://' + process.cwd() + '/' + (process.env.PAGE||'promo.html') + '');
await page.waitForFunction(() => window.READY === true, null, { timeout: 30000 });
await page.waitForTimeout(500);
if (mode === 'stills') {
  fs.mkdirSync(out, { recursive: true });
  for (const t of (process.env.TS||'2').split(',').map(Number)) {
    await page.evaluate(t => render(t), t);
    await page.screenshot({ path: `${out}/t${String(t).replace('.', '_')}.png` });
  }
} else {
  fs.mkdirSync(out, { recursive: true });
  const dur = await page.evaluate(() => DUR), n = Math.round(dur * +fps);
  for (let i = 0; i < n; i++) {
    await page.evaluate(t => render(t), i / +fps);
    await page.screenshot({ path: `${out}/f${String(i).padStart(5, '0')}.jpg`, type: 'jpeg', quality: 95 });
  }
}
await browser.close();
