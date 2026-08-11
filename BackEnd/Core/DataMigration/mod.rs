//! Data Migration Rust module aggregator.

#[path = "1_IAS/ias_importer.rs"]
pub mod ias_importer;

#[path = "2_Soundbase/soundbase_importer.rs"]
pub mod soundbase_importer;

#[path = "3_Wireless_Workbench/wwb_importer.rs"]
pub mod wwb_importer;

#[path = "4_CSV/csv_importer.rs"]
pub mod csv_importer;

#[path = "Data editor/data_editor.rs"]
pub mod data_editor;
