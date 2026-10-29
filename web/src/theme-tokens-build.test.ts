import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, expect, test } from "vitest";
import { build, type Rollup } from "vite";
import dashboardConfig from "../vite.config";

const indexCss = fileURLToPath(new URL("./index.css", import.meta.url));
const fixtures: string[] = [];

afterEach(() => {
  for (const fixture of fixtures.splice(0)) {
    rmSync(fixture, { recursive: true, force: true });
  }
});

// ThemeProvider writes a theme's `colorOverrides` as `--color-*` on <html>.
// They only take effect if the compiled shadcn-compat utilities read those
// variables at runtime instead of a palette mix baked in at build time.
test("theme colour overrides reach the shadcn-compat utilities", async () => {
  const root = mkdtempSync(path.join(tmpdir(), "envoy-web-tokens-"));
  fixtures.push(root);
  writeFileSync(path.join(root, "index.html"), '<script type="module" src="/main.js"></script>');
  writeFileSync(
    path.join(root, "main.js"),
    `import ${JSON.stringify(indexCss)};\n` +
      'export const used = "bg-card text-primary border-border text-destructive bg-muted";\n',
  );

  const result = (await build({
    ...dashboardConfig,
    root,
    configFile: false,
    publicDir: false,
    logLevel: "silent",
    build: { ...dashboardConfig.build, write: false, minify: false },
  })) as Rollup.RollupOutput;

  const css = result.output
    .filter((chunk): chunk is Rollup.OutputAsset => chunk.type === "asset" && chunk.fileName.endsWith(".css"))
    .map((chunk) => String(chunk.source))
    .join("\n");

  for (const [utility, token] of [
    ["bg-card", "--color-card"],
    ["text-primary", "--color-primary"],
    ["border-border", "--color-border"],
    ["text-destructive", "--color-destructive"],
    ["bg-muted", "--color-muted"],
  ]) {
    expect(css).toMatch(new RegExp(`\\.${utility}\\s*\\{[^}]*var\\(${token}\\)`));
  }
}, 60_000);
