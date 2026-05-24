// frameLayout/oaCssLen.js — px/% length helper.
// Convert a layout value to a CSS length: number or numeric-string -> px,
// "%"/other CSS strings pass through. Lets width/height be entered as px OR %.
window.oaCssLen = (v) => {
  if (v == null) return null;
  if (typeof v === 'number') return `${v}px`;
  const s = String(v).trim();
  return /^-?\d+(\.\d+)?$/.test(s) ? `${s}px` : s;
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
