#![allow(non_snake_case, unused_variables, dead_code, unused_imports, unused_mut, mismatched_lifetime_syntaxes)]
//! `openair-ember` — Ember+ (Lawo) tree model.
//!
//! **This crate is a PyO3 extension shim.** Its real implementation lives in the
//! sibling module(s) below and is gated behind the `python` feature, which is NOT
//! enabled by default. A default `cargo build` therefore produces an empty library
//! — that is expected, not missing code. Build with `--features python` to compile
//! the implementation.
//!
//! (The `cargo new` template `add()` that used to sit here has been removed: a
//! function asserting 2 + 2 as the crate's public entry point misrepresented the
//! crate as unimplemented.)
/**
 * Header: lib.rs
 * Purpose: lib.rs implementation.
 * Description: Logic and implementation for lib.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// NOTE: `pyo3` is an optional dependency enabled only by the `python` feature,
// so it must not be imported at crate root ungated — doing so made
// `cargo check -p openair-ember` fail without the feature. The real module below
// carries its own gated imports. (This was latent: CI checks only `openair-yak`
// in this workspace, so a whole crate failing to compile went unnoticed.)

#[cfg(feature = "python")]
pub mod oa_ember_tree_rs;
