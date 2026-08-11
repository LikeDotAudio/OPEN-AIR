/**
 * Header: oaCssLen.js
 * Purpose: oaCssLen component or utility.
 * Description: Handles logic and rendering for oaCssLen component or utility.
 * 
 * Version: 26.08.08.1
 * Change Log:
 * - 2026-08-08: Added oaWrapperIsSized — the shared button-vs-wrapper sizing test.
 * - 2026-07-05: Initial annotation and documentation added.
 */

// frameLayout/oaCssLen.js — px/% length helper.
// Convert a layout value to a CSS length: number or numeric-string -> px,
// "%"/other CSS strings pass through. Lets width/height be entered as px OR %.
window.oaCssLen = (v) => {
  if (v == null) return null;
  if (typeof v === 'number') return `${v}px`;
  const s = String(v).trim();
  return /^-?\d+(\.\d+)?$/.test(s) ? `${s}px` : s;
};

// Does layout.width/height size this node's WRAPPER, or the widget inside it?
//
// For a button — single or grouped — those numbers are the BUTTON's size, read
// by the widget itself; pinning the wrapper to them as well spends the budget
// twice and the grid overflows into the block below. Everything else is sized
// by its wrapper. WidgetFactory decides layout with this; OcaBlock asks it
// whether a field can actually use a percentage height before stretching to
// offer one. Both must agree, so the rule lives here rather than in either.
window.oaWrapperIsSized = (node) => {
  const t = String((node && node.type) || '').toLowerCase();
  const isButton = t.includes('button') || t.includes('toggle') || t.includes('actuator');
  const isGroup = t.includes('toggler')
    || (isButton && node && node.options && typeof node.options === 'object'
        && Object.keys(node.options).length > 1);
  return !isButton && !isGroup;
};

// Extract the WORDING from a label state that may be the new object form
// { text:<string|{En,…}>, text_size, text_color } OR a legacy string / {En,…} dict.
// Always returns the wording (string or {En,…}); style keys are ignored here.
window.oaLabelText = (state) =>
  (state && typeof state === 'object' && !Array.isArray(state) && 'text' in state) ? state.text : state;

// Per-state label text styling { text_size, text_color } (empty object if none).
window.oaLabelStyle = (state) =>
  (state && typeof state === 'object' && !Array.isArray(state))
    ? { text_size: state.text_size, text_color: state.text_color } : {};

// Pick a state label from an object that may use the new schema
// (label:{ active, inactive, text }) OR legacy flat label_active/label_inactive/label.
// `which` is 'active' | 'inactive'. Returns the WORDING (string or {En,…} dict),
// unwrapping the new { text, text_size, text_color } state form via oaLabelText.
window.oaPickLabel = (o, which) => {
  if (!o) return undefined;
  const lab = o.label;
  const pair = (lab && typeof lab === 'object' && ('active' in lab || 'inactive' in lab)) ? lab : null;
  let raw;
  if (which === 'inactive') {
    if (o.label_inactive !== undefined) raw = o.label_inactive;
    else if (pair) raw = pair.inactive !== undefined ? pair.inactive : pair.active;
    else raw = o.label_active !== undefined ? o.label_active : lab;
  } else {
    if (o.label_active !== undefined) raw = o.label_active;
    else if (pair) raw = pair.active;
    else raw = lab;
  }
  return window.oaLabelText(raw);
};

// Like oaPickLabel but returns the state's { text_size, text_color } styling.
window.oaPickLabelStyle = (o, which) => {
  if (!o) return {};
  const lab = o.label;
  const pair = (lab && typeof lab === 'object' && ('active' in lab || 'inactive' in lab)) ? lab : null;
  if (!pair) return {};
  const state = (which === 'inactive')
    ? (pair.inactive !== undefined ? pair.inactive : pair.active)
    : pair.active;
  return window.oaLabelStyle(state);
};
