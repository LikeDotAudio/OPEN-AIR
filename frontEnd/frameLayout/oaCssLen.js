// frameLayout/oaCssLen.js — px/% length helper.
// Convert a layout value to a CSS length: number or numeric-string -> px,
// "%"/other CSS strings pass through. Lets width/height be entered as px OR %.
window.oaCssLen = (v) => {
  if (v == null) return null;
  if (typeof v === 'number') return `${v}px`;
  const s = String(v).trim();
  return /^-?\d+(\.\d+)?$/.test(s) ? `${s}px` : s;
};
