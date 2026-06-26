use pyo3::prelude::*;

pub mod oa_visa_known_devices;
pub mod oa_visa_connect;
pub mod oa_visa_get_idn;
pub mod oa_visa_scan_for_devices;
pub mod oa_visa_reset;
pub mod oa_visa_status;
pub mod oa_visa_error_check;
pub mod oa_visa_pyvisa_wrapper;
pub mod oa_visa_mqtt;
pub mod oa_visa_scanner;
pub mod oa_visa_mdns_zeroconf;
pub mod oa_visa_usb_enumerator;
pub mod oa_visa_resource_manager;
pub mod oa_visa_proxy;

use oa_visa_connect::Instrument;
use oa_visa_resource_manager::ResourceManager;
use oa_visa_proxy::VisaProxy;

#[pymodule]
fn openair_visa(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<ResourceManager>()?;
    m.add_class::<Instrument>()?;
    m.add_class::<VisaProxy>()?;
    m.add_function(wrap_pyfunction!(oa_visa_reset::oa_visa_reset, m)?)?;
    m.add_function(wrap_pyfunction!(oa_visa_status::oa_visa_status, m)?)?;
    m.add_function(wrap_pyfunction!(oa_visa_error_check::oa_visa_error_check, m)?)?;
    m.add_function(wrap_pyfunction!(oa_visa_mqtt::logic_mqtt_listen::start_mqtt_daemon, m)?)?;
    Ok(())
}
