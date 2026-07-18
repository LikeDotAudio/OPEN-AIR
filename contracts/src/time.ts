/**
 * Boundary time conversions (guidelines §2.2 of Phase 1: ISO-8601 UTC
 * everywhere on the bus; unix-seconds converts AT the contract boundary).
 * Vector-pinned against the Rust twin (contracts/rust/src/time.rs).
 */

/** Unix seconds (int or float, as v40 emits) → ISO-8601 UTC with ms. */
export function fromUnixSeconds(seconds: number): string {
  return new Date(Math.round(seconds * 1000)).toISOString()
}
