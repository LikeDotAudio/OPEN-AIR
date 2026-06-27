#[cfg(feature = "python")]
use pyo3::prelude::*;

pub mod oa_visa_known_devices;
#[cfg(feature = "python")] pub mod oa_visa_connect;
#[cfg(feature = "python")] pub mod oa_visa_get_idn;
pub mod oa_visa_scan_for_devices;
#[cfg(feature = "python")] pub mod oa_visa_reset;
#[cfg(feature = "python")] pub mod oa_visa_status;
#[cfg(feature = "python")] pub mod oa_visa_error_check;
#[cfg(feature = "python")] pub mod oa_visa_pyvisa_wrapper;
#[cfg(feature = "python")] pub mod oa_visa_mqtt;
pub mod oa_visa_scanner;
pub mod oa_visa_mdns_zeroconf;
pub mod oa_visa_usb_enumerator;
#[cfg(feature = "python")] pub mod oa_visa_resource_manager;
#[cfg(feature = "python")] pub mod oa_visa_proxy;

#[cfg(feature = "python")] use oa_visa_connect::Instrument;
#[cfg(feature = "python")] use oa_visa_resource_manager::ResourceManager;
#[cfg(feature = "python")] use oa_visa_proxy::VisaProxy;

#[cfg(feature = "python")]
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
