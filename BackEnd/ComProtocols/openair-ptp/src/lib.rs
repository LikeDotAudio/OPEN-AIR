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
pub mod oa_ptp_clock_rs;

#[cfg(feature = "python")]
pub mod oa_ptp_parser_rs;
