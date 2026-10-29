import { parseColor, THEME_PRESET_PALETTES, type ThemePresetPalette } from "@hermes/shared";
import type { DashboardTheme, ThemePalette, ThemeTypography, ThemeLayout } from "./types";

/**
 * Built-in dashboard themes.
 *
 * Each theme defines its own palette, typography, and layout so switching
 * themes produces visible changes beyond just color — fonts, density, and
 * corner-radius all shift to match the theme's personality.
 *
 * Theme names must stay in sync with the backend's
 * `_BUILTIN_DASHBOARD_THEMES` list in `hermes_cli/web_server_dashboard.py`.
 * `clarity` is the default everywhere a default is hard-coded (`context.tsx`,
 * the `index.css` first-paint tokens, and the backend config default).
 *
 * Presets that also ship on the desktop (midnight, ember, mono, cyberpunk)
 * take their colours from `@hermes/shared` `THEME_PRESET_PALETTES` so both
 * surfaces render one palette; only typography/layout/overrides live here.
 */

// ---------------------------------------------------------------------------
// Shared typography / layout presets
// ---------------------------------------------------------------------------

/** Default system stack — neutral, safe fallback for every platform. */
const SYSTEM_SANS =
  'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';
const SYSTEM_MONO =
  'ui-monospace, "SF Mono", "Cascadia Mono", Menlo, Consolas, monospace';

/** Metropolis — Clarity's typeface, self-hosted from @clr/ui 18.4.0 (see
 *  `index.css`), the same face the main Envoy app renders. */
const CLARITY_SANS = `Metropolis, "Avenir Next", "Helvetica Neue", Arial, sans-serif`;

const DEFAULT_TYPOGRAPHY: ThemeTypography = {
  fontSans: SYSTEM_SANS,
  fontMono: SYSTEM_MONO,
  baseSize: "15px",
  lineHeight: "1.55",
  letterSpacing: "0",
};

const DEFAULT_LAYOUT: ThemeLayout = {
  radius: "0.5rem",
  density: "comfortable",
};

/**
 * Project a shared (desktop-shaped) preset palette onto the dashboard's
 * 3-slot model. The dashboard's `midground` is its text + primary-fill
 * colour, which is the desktop's `primary`; its `warmGlow` is the brand
 * accent stroke, which is the desktop's `midground` (falling back to `ring`).
 * `foreground` stays the dashboard's invisible white overlay. Dark palettes
 * are the dashboard's home turf, so a preset shipping `darkColors` is read
 * from that side.
 */
export function webPresetFromShared(
  preset: ThemePresetPalette,
): Omit<ThemePalette, "noiseOpacity"> {
  const colors = preset.darkColors ?? preset.colors;
  const [r, g, b] = parseColor(colors.midground ?? colors.ring) ?? [255, 255, 255];
  return {
    background: { hex: colors.background, alpha: 1 },
    midground: { hex: colors.primary, alpha: 1 },
    foreground: { hex: "#ffffff", alpha: 0 },
    warmGlow: `rgba(${r}, ${g}, ${b}, 0.3)`,
  };
}

// ---------------------------------------------------------------------------
// Clarity — the default. Colours mirror the main Envoy app's Clarity palette
// (envoy/frontend/src/design/clarity-theme.css) so both read as one product;
// `family: "clarity"` switches on the Clarity header, vertical nav and control
// styling in `clarity.css`, which reads everything below through CSS vars.
// ---------------------------------------------------------------------------

const CLARITY_TYPOGRAPHY: ThemeTypography = {
  fontSans: CLARITY_SANS,
  fontMono: `"JetBrains Mono", ${SYSTEM_MONO}`,
  baseSize: "15px",
  lineHeight: "1.5",
  letterSpacing: "0",
};

const CLARITY_LAYOUT: ThemeLayout = {
  radius: "0.1875rem",
  density: "comfortable",
};

/** Clarity's header is the navy product bar in both appearances. */
const CLARITY_HEADER = {
  background: "#00364d",
  foreground: "#ffffff",
  accent: "#8cd6f0",
  muted: "#bcd5e1",
  divider: "#496b7b",
  hover: "#17516a",
};

/** The embedded TUI keeps a dark console in both appearances. */
const CLARITY_TERMINAL = { background: "#17242d", foreground: "#edf3f7" };

interface ClaritySurfaces {
  bg: string;
  surface: string;
  raised: string;
  line: string;
  input: string;
  text: string;
  muted: string;
  accent: string;
  onAccent: string;
  selected: string;
  ok: string;
  warn: string;
  bad: string;
  onBad: string;
  shadow: string;
  scheme: "light" | "dark";
}

function clarityTheme(
  name: string,
  label: string,
  description: string,
  c: ClaritySurfaces,
  outputTokenAccent: string,
): DashboardTheme {
  return {
    name,
    label,
    description,
    family: "clarity",
    palette: {
      background: { hex: c.bg, alpha: 1 },
      midground: { hex: c.text, alpha: 1 },
      // Invisible overlay layer; its hex still colours `text-foreground-base`
      // (dialog bodies), so it carries the text colour like Classic Blue's.
      foreground: { hex: c.text, alpha: 0 },
      warmGlow: c.accent,
      noiseOpacity: 0,
    },
    typography: CLARITY_TYPOGRAPHY,
    layout: CLARITY_LAYOUT,
    colorOverrides: {
      card: c.surface,
      cardForeground: c.text,
      popover: c.surface,
      popoverForeground: c.text,
      primary: c.accent,
      primaryForeground: c.onAccent,
      secondary: c.raised,
      secondaryForeground: c.text,
      muted: c.raised,
      mutedForeground: c.muted,
      accent: c.selected,
      accentForeground: c.accent,
      destructive: c.bad,
      destructiveForeground: c.onBad,
      success: c.ok,
      warning: c.warn,
      border: c.line,
      input: c.input,
      ring: c.accent,
    },
    componentStyles: {
      header: CLARITY_HEADER,
      sidebar: { background: c.surface, borderColor: c.line },
      tab: {
        foreground: c.text,
        hoverBackground: c.raised,
        activeBackground: c.selected,
        activeForeground: c.accent,
      },
      card: { background: c.surface, borderColor: c.line, boxShadow: c.shadow },
      page: { colorScheme: c.scheme },
    },
    seriesColors: { inputTokenAccent: c.accent, outputTokenAccent },
    swatchColors: [c.bg, c.accent, CLARITY_HEADER.background],
    terminalBackground: CLARITY_TERMINAL.background,
    terminalForeground: CLARITY_TERMINAL.foreground,
  };
}

/** Clarity light — the dashboard default. */
export const clarityLightTheme: DashboardTheme = clarityTheme(
  "clarity",
  "Clarity",
  "Clarity light — navy header, blue actions, neutral greys",
  {
    bg: "#f4f6f8",
    surface: "#ffffff",
    raised: "#edf1f4",
    line: "#d5dce2",
    input: "#a9b7c0",
    text: "#25333d",
    muted: "#596873",
    accent: "#006a91",
    onAccent: "#ffffff",
    selected: "#e4f3fa",
    ok: "#21682d",
    warn: "#8a5700",
    bad: "#bd2525",
    onBad: "#ffffff",
    shadow: "0 1px 2px #00000008",
    scheme: "light",
  },
  "#21682d",
);

export const clarityDarkTheme: DashboardTheme = clarityTheme(
  "clarity-dark",
  "Clarity Dark",
  "Clarity dark — slate surfaces with light-blue actions",
  {
    bg: "#17242d",
    surface: "#20333f",
    raised: "#293f4d",
    line: "#435967",
    input: "#5d7686",
    text: "#edf3f7",
    muted: "#b8c7d0",
    accent: "#70c7ec",
    onAccent: "#17242d",
    selected: "#284d61",
    ok: "#80ce8b",
    warn: "#ffd279",
    bad: "#ffaaa0",
    onBad: "#17242d",
    shadow: "0 1px 2px #00000033",
    scheme: "dark",
  },
  "#80ce8b",
);

/** The theme the dashboard falls back to when none is chosen or the stored
 *  name is unknown. */
export const defaultTheme: DashboardTheme = clarityLightTheme;

// ---------------------------------------------------------------------------
// Original dashboard themes
// ---------------------------------------------------------------------------

export const envoyTealTheme: DashboardTheme = {
  name: "default",
  label: "Envoy Teal",
  description: "Dark teal with cream accents — the original dashboard look",
  palette: {
    background: { hex: "#041c1c", alpha: 1 },
    midground: { hex: "#ffe6cb", alpha: 1 },
    foreground: { hex: "#ffffff", alpha: 0 },
    warmGlow: "rgba(255, 189, 56, 0.35)",
    noiseOpacity: 1,
  },
  typography: DEFAULT_TYPOGRAPHY,
  layout: DEFAULT_LAYOUT,
  terminalBackground: "#000000",
};

export const midnightTheme: DashboardTheme = {
  name: "midnight",
  label: "Midnight",
  description: "Deep blue-violet with cool accents",
  palette: {
    ...webPresetFromShared(THEME_PRESET_PALETTES.midnight),
    noiseOpacity: 0.8,
  },
  typography: {
    ...DEFAULT_TYPOGRAPHY,
    fontSans: `"Inter", ${SYSTEM_SANS}`,
    fontMono: `"JetBrains Mono", ${SYSTEM_MONO}`,
    fontUrl:
      "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap",
    letterSpacing: "-0.005em",
  },
  layout: {
    ...DEFAULT_LAYOUT,
    radius: "0.75rem",
  },
};

export const emberTheme: DashboardTheme = {
  name: "ember",
  label: "Ember",
  description: "Warm crimson and bronze — forge vibes",
  palette: {
    ...webPresetFromShared(THEME_PRESET_PALETTES.ember),
    noiseOpacity: 1,
  },
  typography: {
    ...DEFAULT_TYPOGRAPHY,
    fontSans: `"Spectral", Georgia, "Times New Roman", serif`,
    fontMono: `"IBM Plex Mono", ${SYSTEM_MONO}`,
    fontUrl:
      "https://fonts.googleapis.com/css2?family=Spectral:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;700&display=swap",
  },
  layout: {
    ...DEFAULT_LAYOUT,
    radius: "0.25rem",
  },
  colorOverrides: {
    destructive: "#c92d0f",
    warning: "#f97316",
  },
};

export const monoTheme: DashboardTheme = {
  name: "mono",
  label: "Mono",
  description: "Clean grayscale — minimal and focused",
  palette: {
    ...webPresetFromShared(THEME_PRESET_PALETTES.mono),
    noiseOpacity: 0.6,
  },
  typography: {
    ...DEFAULT_TYPOGRAPHY,
    fontSans: `"IBM Plex Sans", ${SYSTEM_SANS}`,
    fontMono: `"IBM Plex Mono", ${SYSTEM_MONO}`,
    fontUrl:
      "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap",
  },
  layout: {
    ...DEFAULT_LAYOUT,
    radius: "0",
  },
};

export const cyberpunkTheme: DashboardTheme = {
  name: "cyberpunk",
  label: "Cyberpunk",
  description: "Neon green on black — matrix terminal",
  palette: {
    ...webPresetFromShared(THEME_PRESET_PALETTES.cyberpunk),
    noiseOpacity: 1.2,
  },
  typography: {
    ...DEFAULT_TYPOGRAPHY,
    fontSans: `"Share Tech Mono", "JetBrains Mono", ${SYSTEM_MONO}`,
    fontMono: `"Share Tech Mono", "JetBrains Mono", ${SYSTEM_MONO}`,
    fontUrl:
      "https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=JetBrains+Mono:wght@400;700&display=swap",
  },
  layout: {
    ...DEFAULT_LAYOUT,
    radius: "0",
  },
  colorOverrides: {
    success: "#00ff88",
    warning: "#ffd700",
    destructive: "#ff0055",
  },
};

export const roseTheme: DashboardTheme = {
  name: "rose",
  label: "Rosé",
  description: "Soft pink and warm ivory — easy on the eyes",
  palette: {
    background: { hex: "#1a0f15", alpha: 1 },
    midground: { hex: "#ffd4e1", alpha: 1 },
    foreground: { hex: "#ffffff", alpha: 0 },
    warmGlow: "rgba(249, 168, 212, 0.3)",
    noiseOpacity: 0.9,
  },
  typography: {
    ...DEFAULT_TYPOGRAPHY,
    fontSans: `"Fraunces", Georgia, serif`,
    fontMono: `"DM Mono", ${SYSTEM_MONO}`,
    fontUrl:
      "https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=DM+Mono:wght@400;500&display=swap",
  },
  layout: {
    ...DEFAULT_LAYOUT,
    radius: "1rem",
  },
};

/** Light mode — vivid blue accents on a cream canvas. The id predates the
 *  rebrand and stays stable so saved configs keep resolving. */
export const classicBlueTheme: DashboardTheme = {
  name: "nous-blue",
  label: "Classic Blue",
  description: "Light mode — vivid blue accents on cream canvas",
  palette: {
    background: { hex: "#E8F2FD", alpha: 1 },
    midground: { hex: "#0053FD", alpha: 1 },
    foreground: { hex: "#170d02", alpha: 0 },
    warmGlow: "rgba(0, 83, 253, 0.12)",
    noiseOpacity: 0,
  },
  typography: DEFAULT_TYPOGRAPHY,
  layout: DEFAULT_LAYOUT,
  terminalBackground: "#f5f8fc",
  terminalForeground: "#170d02",
  seriesColors: {
    inputTokenAccent: "#001934",
    outputTokenAccent: "#0053fd",
  },
  swatchColors: ["#170d02", "#0053FD", "#E8F2FD"],
};

/**
 * Same look as ``envoyTealTheme`` but with a larger root font size, looser
 * line-height, and ``spacious`` density so every rem-based size in the
 * dashboard scales up. For users who find the default 15px UI too dense.
 */
export const defaultLargeTheme: DashboardTheme = {
  name: "default-large",
  label: "Envoy Teal (Large)",
  description: "Envoy Teal with bigger fonts and roomier spacing",
  palette: envoyTealTheme.palette,
  typography: {
    ...DEFAULT_TYPOGRAPHY,
    baseSize: "18px",
    lineHeight: "1.65",
  },
  layout: {
    ...DEFAULT_LAYOUT,
    density: "spacious",
  },
};

export const BUILTIN_THEMES: Record<string, DashboardTheme> = {
  clarity: clarityLightTheme,
  "clarity-dark": clarityDarkTheme,
  default: envoyTealTheme,
  "default-large": defaultLargeTheme,
  "nous-blue": classicBlueTheme,
  midnight: midnightTheme,
  ember: emberTheme,
  mono: monoTheme,
  cyberpunk: cyberpunkTheme,
  rose: roseTheme,
};
