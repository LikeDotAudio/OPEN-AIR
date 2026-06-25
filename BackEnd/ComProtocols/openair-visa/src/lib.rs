pub fn add(left: u64, right: u64) -> u64 {
    left + right
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn it_works() {
        let result = add(2, 2);
        assert_eq!(result, 4);
    }
}

#[cfg(feature = "python")]
pub mod oa_visa_core_rs;

#[cfg(feature = "python")]
pub mod oa_visa_format_rs;

#[cfg(feature = "python")]
pub mod oa_visa_scanner_rs;
