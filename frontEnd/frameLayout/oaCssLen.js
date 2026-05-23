// frameLayout/oaCssLen.js — px/% length helper.
// Convert a layout value to a CSS length: number or numeric-string -> px,
// "%"/other CSS strings pass through. Lets width/height be entered as px OR %.
window.oaCssLen = (v) => {
  if (v == null) return null;
  if (typeof v === 'number') return `${v}px`;
  const s = String(v).trim();
  return /^-?\d+(\.\d+)?$/.test(s) ? `${s}px` : s;
};

// Pick a state label from an object that may use the new schema
// (label:{ active, inactive, text }) OR legacy flat label_active/label_inactive/label.
// `which` is 'active' | 'inactive'. Returns the label value (string or {En,…} dict).
window.oaPickLabel = (o, which) => {
  if (!o) return undefined;
  const lab = o.label;
  const pair = (lab && typeof lab === 'object' && ('active' in lab || 'inactive' in lab)) ? lab : null;
  if (which === 'inactive') {
    if (o.label_inactive !== undefined) return o.label_inactive;
    if (pair) return pair.inactive !== undefined ? pair.inactive : pair.active;
    return o.label_active !== undefined ? o.label_active : lab;
  }
  if (o.label_active !== undefined) return o.label_active;
  if (pair) return pair.active;
  return lab;
};
