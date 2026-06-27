#![allow(non_snake_case, unused_variables, dead_code, unused_imports)]
pub fn add(left: u64, right: u64) -> u64 {
    left + right
}

#[cfg(test)]
mod tests {
    #![allow(non_snake_case, unused_variables, dead_code, unused_imports)]
use pyo3::prelude::*;

    #[test]
    fn it_works() {
        let result = add(2, 2);
        assert_eq!(result, 4);
    }
}

#[cfg(feature = "python")]
pub mod oa_snmp_agent_rs;

#[cfg(feature = "python")]
pub mod oa_mib_cache_rs;
