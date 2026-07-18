//! openair-contracts — the Rust mirror of `@openair/contracts`.
//!
//! `topics` is HAND-WRITTEN (grammar is behavior, not shape) and kept honest
//! against the TypeScript implementation by `../vectors/topics.json` — the
//! shared golden-vector suite. `gen/` will hold cargo-typify output generated
//! from `contracts/schemas/` (rollout step 3+); that module is never edited
//! by hand.

pub mod topics;
