import { cn } from "@/lib/utils";

/** The Envoy emblem (the CLI's ◈ nested diamond), drawn in `currentColor`
 *  so the shell decides its colour. `src/assets/envoy-icon.svg` is the same
 *  mark on the favicon tile. */
export function EnvoyMark({ className }: EnvoyMarkProps) {
  return (
    <svg
      aria-hidden
      className={cn("app-wordmark-mark h-6 w-6 shrink-0", className)}
      fill="none"
      viewBox="0 0 24 24"
    >
      <path
        d="M12 2.6 21.4 12 12 21.4 2.6 12Z"
        stroke="currentColor"
        strokeLinejoin="round"
        strokeWidth="1.9"
      />
      <path d="M12 7.6 16.4 12 12 16.4 7.6 12Z" fill="currentColor" />
    </svg>
  );
}

/** Product wordmark: emblem, "Envoy", and a divided "Agent" product label
 *  (the main Envoy app's header treatment). `label` is the accessible name. */
export function EnvoyWordmark({ className, label }: EnvoyWordmarkProps) {
  return (
    <span
      aria-label={label}
      className={cn("app-wordmark inline-flex min-w-0 items-center gap-2.5", className)}
      role="img"
    >
      <EnvoyMark />
      <span aria-hidden className="app-wordmark-name font-sans text-[1.25rem] font-medium leading-none">
        Envoy
      </span>
      <span
        aria-hidden
        className="app-wordmark-product border-l border-current/30 pl-2.5 font-sans text-xs leading-none text-text-secondary"
      >
        Agent
      </span>
    </span>
  );
}

interface EnvoyMarkProps {
  className?: string;
}

interface EnvoyWordmarkProps {
  className?: string;
  label: string;
}
