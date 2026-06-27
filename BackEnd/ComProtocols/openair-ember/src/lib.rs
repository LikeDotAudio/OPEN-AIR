#![allow(non_snake_case, unused_variables, dead_code, unused_imports, unused_mut, mismatched_lifetime_syntaxes)]
use pyo3::prelude::*;

pub fn add(left: u64, right: u64) -> u64 {
    left + right
}

#[cfg(test)]
mod tests {
    #![allow(non_snake_case, unused_variables, dead_code, unused_imports, unused_mut)]
use pyo3::prelude::*;

    #[test]
    fn it_works() {
        let result = add(2, 2);
        assert_eq!(result, 4);
    }
}

#[cfg(feature = "python")]
pub mod oa_ember_tree_rs;
