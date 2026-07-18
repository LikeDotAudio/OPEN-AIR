/**
 * @openair/contracts — the single source of truth for every cross-boundary
 * shape in OPEN-AIR: topic grammar, DeviceRecord, AgentHeartbeat, the GUI
 * envelope, layout JSON, and the YAK contracts.
 *
 * This file is the ONLY public surface of the package (Phase 1 §1.2).
 *
 * Rollout (Documents/Audits/Phase 1.md §7):
 *   step 2 — topics/ (grammar + legacy map + vectors)
 *   step 3 — heartbeat.ts, device-record.ts
 *   step 4 — layout/, yak/ (incl. the yak_handler runtime message)
 *   step 5 — validate CLI ratchet
 *   step 6 — Rust adoption seed
 */

export const CONTRACTS_VERSION = '0.1.0' as const
