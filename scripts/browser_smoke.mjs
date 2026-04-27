#!/usr/bin/env node
let chromium;
try {
  const playwrightModule = await import(process.env.WSIS_PLAYWRIGHT_PACKAGE || "playwright");
  chromium = playwrightModule.chromium || playwrightModule.default?.chromium;
} catch (error) {
  console.error("Install Playwright or set WSIS_PLAYWRIGHT_PACKAGE to a local Playwright package path.");
  console.error(error.message);
  process.exit(1);
}
if (!chromium) {
  console.error("Playwright was found, but chromium was not exported.");
  process.exit(1);
}

const baseUrl = process.env.WSIS_SMOKE_BASE_URL || "http://localhost:8501";
const pages = ["/", "/Decision", "/City_Profile", "/Comparison"];
const viewports = [
  { name: "desktop", width: 1280, height: 900 },
  { name: "mobile", width: 390, height: 844 },
];

function fail(message) {
  console.error(message);
  process.exitCode = 1;
}

const browser = await chromium.launch({ headless: true });

for (const viewport of viewports) {
  const page = await browser.newPage({ viewport });
  for (const path of pages) {
    const url = `${baseUrl}${path}`;
    await page.goto(url, { waitUntil: "networkidle", timeout: 30000 });
    const result = await page.evaluate(() => {
      const rawHtmlBlocks = [...document.querySelectorAll("pre")].filter((node) =>
        (node.textContent || "").includes("<div")
      ).length;
      const doc = document.documentElement;
      const horizontalOverflow = doc.scrollWidth - doc.clientWidth;
      const unreadableLabels = [...document.querySelectorAll("label, label p")].filter((node) => {
        const rect = node.getBoundingClientRect();
        if (rect.width <= 0 || rect.height <= 0) return false;
        const style = getComputedStyle(node);
        return style.opacity === "0" || style.color === "rgb(255, 255, 255)";
      }).length;
      return { rawHtmlBlocks, horizontalOverflow, unreadableLabels };
    });

    if (result.rawHtmlBlocks > 0) {
      fail(`${viewport.name} ${path}: raw HTML is visible in code blocks.`);
    }
    if (result.horizontalOverflow > 2) {
      fail(`${viewport.name} ${path}: horizontal overflow is ${result.horizontalOverflow}px.`);
    }
    if (result.unreadableLabels > 0) {
      fail(`${viewport.name} ${path}: ${result.unreadableLabels} labels look unreadable.`);
    }
    console.log(`${viewport.name} ${path}: ok`);
  }
  await page.close();
}

await browser.close();
if (process.exitCode) process.exit(process.exitCode);
