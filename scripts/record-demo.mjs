import { createRequire } from "node:module";
import { mkdir, rm } from "node:fs/promises";
import path from "node:path";

const require = createRequire("/tmp/intellibank-video/package.json");
const { chromium } = require("playwright-core");

const outputDir = path.resolve(process.argv[2] || "artifacts/demo-frames");
await rm(outputDir, { recursive: true, force: true });
await mkdir(outputDir, { recursive: true });

const browser = await chromium.launch({
  executablePath: "/opt/google/chrome/google-chrome",
  headless: true,
  args: ["--no-sandbox", "--disable-dev-shm-usage"],
});
const context = await browser.newContext({
  viewport: { width: 430, height: 900 },
  deviceScaleFactor: 1,
  locale: "es-MX",
  colorScheme: "light",
});
const page = await context.newPage();
page.setDefaultTimeout(20_000);

let frame = 0;
let recording = true;
const capture = (async () => {
  while (recording) {
    const filename = `${String(frame).padStart(6, "0")}.jpg`;
    await page.screenshot({
      path: path.join(outputDir, filename),
      type: "jpeg",
      quality: 88,
      animations: "allow",
    }).catch(() => {});
    frame += 1;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
})();

const pause = (ms = 1400) => page.waitForTimeout(ms);
const clickSlowly = async (locator, waitAfter = 1200) => {
  await locator.scrollIntoViewIfNeeded();
  const box = await locator.boundingBox();
  if (box) {
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 10 });
    await pause(300);
  }
  await locator.click();
  await pause(waitAfter);
};

try {
  await page.goto("http://127.0.0.1:5173", { waitUntil: "networkidle" });
  await page.evaluate(() => {
    localStorage.clear();
    localStorage.setItem("intellibank_has_account", "1");
  });
  await page.reload({ waitUntil: "networkidle" });
  await pause(1800);

  await page.getByPlaceholder("Correo, teléfono, CLABE o tarjeta").fill("4152");
  await pause(500);
  await page.getByPlaceholder("••••••••").fill("demo1234");
  await pause(700);
  await clickSlowly(page.getByRole("button", { name: "Entrar", exact: true }), 2200);
  const topicSkip = page.getByRole("button", { name: "Ahora no", exact: true });
  if (await topicSkip.isVisible().catch(() => false)) {
    await pause(1400);
    await clickSlowly(topicSkip, 1800);
  }
  await page.getByText(/Bienvenido,/).waitFor();
  await pause(2300);

  await clickSlowly(page.getByRole("button", { name: "Historial" }), 1700);
  await clickSlowly(page.getByRole("button", { name: "Más" }), 1700);
  await clickSlowly(page.getByRole("button", { name: /Temas del asistente/ }), 1700);
  await clickSlowly(page.getByRole("button", { name: "Inicio" }), 1800);
  await clickSlowly(page.getByRole("button", { name: "Asistente" }), 2200);

  const prompt = "Genera una interfaz visual con el resumen de mis gastos por categoría del último mes y una recomendación para ahorrar.";
  const composer = page.getByPlaceholder("Cuéntame lo que necesitas…");
  await composer.fill(prompt);
  await pause(1500);
  await clickSlowly(page.getByRole("button", { name: "Enviar" }), 500);

  await page.locator(".assistant-loader").waitFor({ state: "visible", timeout: 10_000 }).catch(() => {});
  await page.locator(".assistant-loader").waitFor({ state: "hidden", timeout: 60_000 });
  await page.locator(".generated-interface-entry").last().waitFor({ state: "visible", timeout: 15_000 });
  await pause(6500);
} finally {
  recording = false;
  await capture;
  await context.close();
  await browser.close();
  process.stdout.write(`${frame}\n`);
}
