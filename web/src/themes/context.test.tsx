// @vitest-environment jsdom
import { act, useEffect } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const getThemes = vi.fn();

vi.mock("@/lib/api", () => ({
  api: {
    getFontPref: () => Promise.resolve({ font: "theme" }),
    getThemes: () => getThemes(),
    setFontPref: () => Promise.resolve({ ok: true }),
    setTheme: () => Promise.resolve({ ok: true }),
  },
}));

import { ThemeProvider, useTheme } from "./context";

let root: Root | null = null;
let setTheme: (name: string) => void = () => {};

// Node's own (flag-gated) Web Storage shadows jsdom's, so give the page a
// working in-memory one.
function memoryStorage(): Storage {
  const items = new Map<string, string>();
  return {
    clear: () => items.clear(),
    getItem: (key) => items.get(key) ?? null,
    key: (index) => [...items.keys()][index] ?? null,
    get length() {
      return items.size;
    },
    removeItem: (key) => void items.delete(key),
    setItem: (key, value) => void items.set(key, String(value)),
  };
}

beforeEach(() => {
  Object.defineProperty(window, "localStorage", { configurable: true, value: memoryStorage() });
});

function Probe({ onTheme }: ProbeProps) {
  const { setTheme: next } = useTheme();
  useEffect(() => onTheme(next), [onTheme, next]);
  return null;
}

interface ProbeProps {
  onTheme: (setTheme: (name: string) => void) => void;
}

async function mount() {
  const container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
  await act(async () => {
    root!.render(
      <ThemeProvider>
        <Probe onTheme={(next) => (setTheme = next)} />
      </ThemeProvider>,
    );
  });
}

const html = () => document.documentElement;

afterEach(() => {
  act(() => root?.unmount());
  root = null;
  html().removeAttribute("style");
  delete html().dataset.themeFamily;
});

describe("dashboard theme provider", () => {
  it("renders the Clarity chrome when nothing has been chosen", async () => {
    getThemes.mockResolvedValue({ active: "", themes: [] });
    await mount();

    expect(html().dataset.themeFamily).toBe("clarity");
    expect(html().style.getPropertyValue("--color-primary")).toBe("#006a91");
    expect(html().style.getPropertyValue("--component-header-background")).toBe("#00364d");
  });

  it("drops the Clarity chrome and its overrides for a theme without one", async () => {
    getThemes.mockResolvedValue({ active: "clarity-dark", themes: [] });
    await mount();
    expect(html().dataset.themeFamily).toBe("clarity");
    expect(html().style.getPropertyValue("--color-primary")).toBe("#70c7ec");

    await act(async () => setTheme("default"));

    expect(html().dataset.themeFamily).toBeUndefined();
    expect(html().style.getPropertyValue("--color-primary")).toBe("");
    expect(html().style.getPropertyValue("--component-header-background")).toBe("");
  });

  it("falls back to Clarity for an unknown stored theme", async () => {
    window.localStorage.setItem("hermes-dashboard-theme", "removed-theme");
    getThemes.mockResolvedValue({ active: "", themes: [] });
    await mount();

    expect(html().dataset.themeFamily).toBe("clarity");
  });
});
