/// Squared Euclidean distance between two 9-D feature vectors.
pub fn sqdist(a: &[f64; 9], b: &[f64; 9]) -> f64 {
    let mut s = 0.0;
    for j in 0..9 {
        let d = a[j] - b[j];
        s += d * d;
    }
    s
}
