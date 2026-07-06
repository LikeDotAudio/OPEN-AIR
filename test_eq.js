const bands = [];
const key = "LowMid";
const ltpParsed = { value: 250, rotValue: 0 };
const qParsed = null;
const bandData = {};

const unwrap = (v) => {
    if (v === undefined || v === null) return undefined;
    if (typeof v === 'object' && v.value !== undefined) return v.value;
    return v;
};

let freq = unwrap(bandData?.Freq) ?? unwrap(bandData?.freq) ?? unwrap(bandData?.Frequency) ?? unwrap(bandData?.frequency);
let gain = unwrap(bandData?.Gain) ?? unwrap(bandData?.gain);
let q = unwrap(bandData?.Q) ?? unwrap(bandData?.q);

if (freq === undefined && ltpParsed) freq = ltpParsed.value;
if (gain === undefined && ltpParsed) gain = ltpParsed.rotValue;
if (q === undefined && qParsed) q = qParsed.value !== undefined ? qParsed.value : qParsed;

freq = parseFloat(freq);
gain = parseFloat(gain);
q = parseFloat(q) || 1.0;

if (!isNaN(freq) && !isNaN(gain) && !isNaN(q)) {
    bands.push({ name: key, freq, gain, q });
}
console.log(bands);
