import type { Usage } from '@envoy/shared/gateway-events'

export { usageFromTick } from '@envoy/shared/usage-tick'

export const ZERO: Usage = { calls: 0, input: 0, output: 0, total: 0 }
