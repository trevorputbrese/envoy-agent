import { describe, expect, it } from "vitest";

import { isHiddenEnvKey, isHiddenProvider } from "./hidden-vendors";

describe("hidden vendor surfaces", () => {
  it("hides an unused Nous Portal offer but keeps one in use", () => {
    expect(isHiddenProvider("nous", false)).toBe(true);
    expect(isHiddenProvider("nous", true)).toBe(false);
    expect(isHiddenProvider("anthropic", false)).toBe(false);
  });

  it("hides unset NOUS_ keys so a set one can still be cleared", () => {
    expect(isHiddenEnvKey("NOUS_API_KEY", false)).toBe(true);
    expect(isHiddenEnvKey("NOUS_API_KEY", true)).toBe(false);
    expect(isHiddenEnvKey("TOOL_GATEWAY_USER_TOKEN", false)).toBe(true);
    expect(isHiddenEnvKey("TOOL_GATEWAY_URL", false)).toBe(false);
    expect(isHiddenEnvKey("OPENROUTER_API_KEY", false)).toBe(false);
  });
});
