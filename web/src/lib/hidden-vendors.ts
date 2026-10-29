/**
 * Upstream-vendor surfaces the Envoy dashboard does not advertise: the Nous
 * Portal (its subscription sign-in, its `NOUS_*` keys and subscriber
 * tool-gateway overrides, and the toolset providers that need it). The
 * backend still supports them, so anything already in use stays visible —
 * that is how it gets changed or removed.
 */

const HIDDEN_PROVIDER_IDS: ReadonlySet<string> = new Set(["nous"]);
const HIDDEN_ENV_PREFIXES: readonly string[] = ["NOUS_"];
/** The Nous Subscriber tool-gateway overrides (not the generic gateway URLs). */
const HIDDEN_ENV_KEYS: ReadonlySet<string> = new Set([
  "FIRECRAWL_GATEWAY_URL",
  "TOOL_GATEWAY_DOMAIN",
  "TOOL_GATEWAY_SCHEME",
  "TOOL_GATEWAY_USER_TOKEN",
]);

/** Whether a provider offer (by provider id) is hidden unless it is in use. */
export function isHiddenProvider(id: string, inUse: boolean): boolean {
  return !inUse && HIDDEN_PROVIDER_IDS.has(id);
}

/** Whether an env-var row is hidden: a hidden vendor's key that is not set. */
export function isHiddenEnvKey(key: string, isSet: boolean): boolean {
  if (isSet) return false;
  return HIDDEN_ENV_KEYS.has(key) || HIDDEN_ENV_PREFIXES.some((prefix) => key.startsWith(prefix));
}
