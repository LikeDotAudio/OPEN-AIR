//! Blind K-Means++ clustering over the extracted feature space. Groups files
//! that "sound alike" without looking at their names. Loops are clustered
//! separately from one-shots (cluster ids offset by k) so the two graphs get
//! their own groupings.
use crate::kmeans::kmeans_assign;
use crate::peak::Peak;

pub fn cluster_samples(results: &mut [Peak], k: usize) {
    let idx_hits: Vec<usize> = (0..results.len()).filter(|&i| results[i].group != "Loops/Patterns").collect();
    let idx_loops: Vec<usize> = (0..results.len()).filter(|&i| results[i].group == "Loops/Patterns").collect();
    kmeans_assign(results, &idx_hits, k, 0);
    kmeans_assign(results, &idx_loops, k, k as i32);
}
