// Render scene.html to video frames via Playwright, piping JPEGs into ffmpeg.
// Usage: node render_frames.js out.mp4 [fps]   |   node render_frames.js --preview t1,t2,...
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto('file://' + path.join(__dirname, 'scene.html'));
  await page.waitForTimeout(300);
  if (process.argv[2] === '--preview') {
    for (const t of process.argv[3].split(',')) {
      await page.evaluate(x => render(x), parseFloat(t));
      await page.screenshot({ path: path.join(process.argv[4] || '.', `prev_${t}.jpg`), type: 'jpeg', quality: 70 });
    }
  } else {
    const out = process.argv[2], fps = parseInt(process.argv[3] || '30');
    const total = await page.evaluate(() => TOTAL);
    const ff = spawn('ffmpeg', ['-y', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium', out], { stdio: ['pipe', 'ignore', 'inherit'] });
    const n = Math.round(total * fps);
    for (let i = 0; i < n; i++) {
      await page.evaluate(x => render(x), i / fps);
      const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 150 === 0) console.log(`frame ${i}/${n}`);
    }
    ff.stdin.end();
    await new Promise(r => ff.on('close', r));
  }
  await browser.close();
})();
