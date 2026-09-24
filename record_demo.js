const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  console.log("Starting Playwright demo recording script...");
  const artifactDir = "/config/.gemini/antigravity/brain/2f4261a8-5685-4bfd-afce-b34b9f4e2bbd";
  const videoDir = path.join(artifactDir, "video_recordings");
  if (!fs.existsSync(videoDir)) {
    fs.mkdirSync(videoDir, { recursive: true });
  }

  const browser = await chromium.launch({
    executablePath: '/usr/bin/google-chrome',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    recordVideo: {
      dir: videoDir,
      size: { width: 1280, height: 800 }
    }
  });

  const page = await context.newPage();
  console.log("Navigating to live Cloud Run app URL...");
  await page.goto('https://proposalcraft-frontend-1015245283915.us-east1.run.app', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);

  // 1. Primary Prompt: Effort estimation & project co-pilot capability
  console.log("Filling Prompt 1: Effort Estimation...");
  const prompt1 = "Estimate effort for a GKE modernization project with 12 microservices";
  await page.waitForSelector('#input', { state: 'visible', timeout: 15000 });
  await page.fill('#input', prompt1);
  await page.waitForTimeout(1000);
  await page.click('button[type="submit"]');

  console.log("Waiting for response to Prompt 1...");
  await page.waitForSelector('.typing-indicator', { state: 'attached', timeout: 10000 }).catch(() => {});
  await page.waitForSelector('.typing-indicator', { state: 'detached', timeout: 90000 }).catch(() => {});
  console.log("Prompt 1 completed. Pausing for viewer readability...");
  await page.waitForTimeout(5000);

  // 2. Second Richer Prompt: Firestore DB Lookup + Architecture Diagram Tool Call
  console.log("Filling Prompt 2: Firestore Proposal Lookup & Architecture Diagram Generation...");
  const prompt2 = "Look up proposal PROP-101 in Firestore, then generate an architecture diagram for its Cloud Modernization & GKE Migration.";
  await page.waitForSelector('#input', { state: 'visible', timeout: 15000 });
  await page.fill('#input', prompt2);
  await page.waitForTimeout(1000);
  await page.click('button[type="submit"]');

  console.log("Waiting for response to Prompt 2...");
  await page.waitForSelector('.typing-indicator', { state: 'attached', timeout: 10000 }).catch(() => {});
  await page.waitForSelector('.typing-indicator', { state: 'detached', timeout: 120000 }).catch(() => {});
  console.log("Prompt 2 completed. Pausing for viewer readability...");
  await page.waitForTimeout(5000);

  // Scroll log container down to reveal generated architecture diagram
  console.log("Scrolling chat log...");
  await page.evaluate(() => {
    const log = document.getElementById('log');
    if (log) log.scrollTop = log.scrollHeight;
  });
  await page.waitForTimeout(2000);

  // Trigger Lightbox Zoom Modal if architecture diagram image is rendered
  const archImg = await page.$('.a2img, #log img');
  if (archImg) {
    console.log("Clicking generated architecture image to launch Lightbox Zoom Modal...");
    await archImg.click();
    await page.waitForTimeout(4000);
    // Close Lightbox
    await page.click('#lightbox');
    await page.waitForTimeout(2000);
  }

  console.log("Closing browser context and saving demo video...");
  await context.close();
  await browser.close();

  // Find recorded video file and copy to artifact path
  const videoFiles = fs.readdirSync(videoDir).filter(f => f.endsWith('.webm'));
  if (videoFiles.length > 0) {
    const origVideoPath = path.join(videoDir, videoFiles[0]);
    const finalVideoPath = path.join(artifactDir, "proposalcraft_demo.webm");
    fs.copyFileSync(origVideoPath, finalVideoPath);
    console.log(`Demo video successfully created and saved to: ${finalVideoPath}`);
  } else {
    console.log("Error: No video file was generated.");
  }
})();
