use pyo3::prelude::*;

pub mod oa_audio_mixer_rs;
pub mod oa_config_engine_rs;
pub mod oa_async_sink_rs;
pub mod oa_logging_gate_rs;
pub mod oa_safety_core_rs;
pub mod oa_heartbeat_core_rs;
pub mod oa_thread_pool_rs;
pub mod oa_clock_sync_rs;
pub mod oa_core_router_rs;
pub mod oa_aes70_core_rs;
pub mod oa_ember_tree_rs;
pub mod oa_midi_mapper_rs;
pub mod oa_midi_engine_rs;
pub mod oa_mqtt_manager_rs;
pub mod oa_osc_core_rs;
pub mod oa_fast_api_rs;
pub mod oa_st2138_codec_rs;
pub mod oa_mib_cache_rs;
pub mod oa_snmp_agent_rs;
pub mod oa_visa_core_rs;
pub mod oa_visa_format_rs;
pub mod oa_visa_scanner_rs;
pub mod oa_ptp_clock_rs;
pub mod oa_ptp_parser_rs;
pub mod oa_fast_dir_rs;
pub mod oa_layout_engine_rs;
pub mod oa_pattern_engine_rs;
pub mod oa_geometry_math_rs;
pub mod oa_editor_state_rs;
pub mod oa_hitbox_math_rs;
pub mod oa_metering_engine_rs;
pub mod oa_cmdp_math_rs;
pub mod oa_needle_engine_rs;
pub mod oa_needle_geometry_rs;
pub mod oa_procedural_art_rs;
pub mod oa_rotary_core_rs;
pub mod oa_fast_scanner_rs;
pub mod oa_blueprint_parser_rs;
pub mod oa_image_scaler_rs;
pub mod oa_time_series_db_rs;
pub mod oa_css_parser_rs;
pub mod oa_csv_writer_rs;
pub mod oa_csv_parser_rs;
pub mod oa_html_scraper_rs;
pub mod oa_pdf_parser_rs;
pub mod oa_showfile_unpacker_rs;
pub mod oa_splink_registry_rs;
pub mod oa_splink_core_rs;
pub mod oa_disk_flusher_rs;
pub mod oa_task_pool_rs;
pub mod oa_translator_core_rs;
pub mod oa_trie_rs;
pub mod oa_state_differ_rs;
pub mod oa_state_registry_rs;
pub mod oa_markdown_compiler_rs;
pub mod oa_log_aligner_rs;
pub mod oa_debug_toggler_rs;
pub mod oa_log_processor_rs;
pub mod oa_manifest_gen_rs;

#[pymodule]
fn oaRustCore(m: &Bound<'_, PyModule>) -> PyResult<()> {
    let sys_modules = m.py().import_bound("sys")?.getattr("modules")?;

    macro_rules! add_submodule {
        ($mod_name:ident, $func:ident, $camel_name:expr) => {
            let sub = PyModule::new_bound(m.py(), stringify!($mod_name))?;
            $mod_name::$func(&sub)?;
            m.add_submodule(&sub)?;
            
            // ⚡ IMPORT HACK: Register multiple aliases in sys.modules to satisfy legacy code
            let aliases = [
                format!("oaRustCore.{}", stringify!($mod_name)),
                format!("oaRustCore.{}", $camel_name),
                format!("oaRustCore.{}", $camel_name.to_lowercase()),
                stringify!($mod_name).to_string(),
                $camel_name.to_string(),
                $camel_name.to_lowercase(),
            ];
            
            for alias in aliases {
                sys_modules.set_item(alias, &sub)?;
            }
        };
    }

    add_submodule!(oa_audio_mixer_rs, oaaudiomixer_rs, "oaAudioMixer_rs");
    add_submodule!(oa_config_engine_rs, oaconfigengine_rs, "oaConfigEngine_rs");
    add_submodule!(oa_async_sink_rs, oaasyncsink_rs, "oaAsyncSink_rs");
    add_submodule!(oa_logging_gate_rs, oalogginggate_rs, "oaLoggingGate_rs");
    add_submodule!(oa_safety_core_rs, oasafetycore_rs, "oaSafetyCore_rs");
    add_submodule!(oa_heartbeat_core_rs, oaHeartbeatCore_rs, "oaHeartbeatCore_rs");
    add_submodule!(oa_thread_pool_rs, oathreadpool_rs, "oaThreadPool_rs");
    add_submodule!(oa_clock_sync_rs, oaclocksync_rs, "oaClockSync_rs");
    add_submodule!(oa_core_router_rs, oacorerouter_rs, "oaCoreRouter_rs");
    add_submodule!(oa_aes70_core_rs, oaaes70core_rs, "oaAES70Core_rs");
    add_submodule!(oa_ember_tree_rs, oaembertree_rs, "oaEmberTree_rs");
    add_submodule!(oa_midi_mapper_rs, oamidimapper_rs, "oaMidiMapper_rs");
    add_submodule!(oa_midi_engine_rs, oamidiengine_rs, "oaMidiEngine_rs");
    add_submodule!(oa_mqtt_manager_rs, oamqttmanager_rs, "oaMQTTManager_rs");
    add_submodule!(oa_osc_core_rs, oaosccore_rs, "oaOSCCore_rs");
    add_submodule!(oa_fast_api_rs, oafastapi_rs, "oaFastAPI_rs");
    add_submodule!(oa_st2138_codec_rs, oast2138codec_rs, "oaST2138Codec_rs");
    add_submodule!(oa_mib_cache_rs, oaMIBCache_rs, "oaMIBCache_rs");
    add_submodule!(oa_snmp_agent_rs, oasnmpagent_rs, "oaSNMPAgent_rs");
    add_submodule!(oa_visa_core_rs, oavisacore_rs, "oaVisaCore_rs");
    add_submodule!(oa_visa_format_rs, oavisaformat_rs, "oaVisaFormat_rs");
    add_submodule!(oa_visa_scanner_rs, oavisascanner_rs, "oaVisaScanner_rs");
    add_submodule!(oa_ptp_clock_rs, oaptpclock_rs, "oaPTPClock_rs");
    add_submodule!(oa_ptp_parser_rs, oaptpparser_rs, "oaPtpParser_rs");
    add_submodule!(oa_fast_dir_rs, oaFastDir_rs, "oaFastDir_rs");
    add_submodule!(oa_layout_engine_rs, oaLayoutEngine_rs, "oaLayoutEngine_rs");
    add_submodule!(oa_pattern_engine_rs, oapatternengine_rs, "oaPatternEngine_rs");
    add_submodule!(oa_geometry_math_rs, oageometrymath_rs, "oaGeometryMath_rs");
    add_submodule!(oa_editor_state_rs, oaeditorstate_rs, "oaEditorState_rs");
    add_submodule!(oa_hitbox_math_rs, oaHitboxMath_rs, "oaHitboxMath_rs");
    add_submodule!(oa_metering_engine_rs, oameteringengine_rs, "oaMeteringEngine_rs");
    add_submodule!(oa_cmdp_math_rs, oacmdpmath_rs, "oaCMDPMath_rs");
    add_submodule!(oa_needle_engine_rs, oaneedleengine_rs, "oaNeedleEngine_rs");
    add_submodule!(oa_needle_geometry_rs, oaneedlegeometry_rs, "oaNeedleGeometry_rs");
    add_submodule!(oa_procedural_art_rs, oaproceduralart_rs, "oaProceduralArt_rs");
    add_submodule!(oa_rotary_core_rs, oarotarycore_rs, "oaRotaryCore_rs");
    add_submodule!(oa_fast_scanner_rs, oafastscanner_rs, "oaFastScanner_rs");
    add_submodule!(oa_blueprint_parser_rs, oablueprintparser_rs, "oaBlueprintParser_rs");
    add_submodule!(oa_image_scaler_rs, oaImageScaler_rs, "oaImageScaler_rs");
    add_submodule!(oa_time_series_db_rs, oaTimeSeriesDB_rs, "oaTimeSeriesDB_rs");
    add_submodule!(oa_css_parser_rs, oaCSSParser_rs, "oaStyle_rs");
    add_submodule!(oa_csv_writer_rs, oacsvwriter_rs, "oaFileExportCSV_rs");
    add_submodule!(oa_csv_parser_rs, oacsvparser_rs, "oaFileImportCSV_rs");
    add_submodule!(oa_html_scraper_rs, oahtmlscraper_rs, "oaFileImportHTML_rs");
    add_submodule!(oa_pdf_parser_rs, oapdfparser_rs, "oaFileImportPDF_rs");
    add_submodule!(oa_showfile_unpacker_rs, oashowfileunpacker_rs, "oaFileImportShow_rs");
    add_submodule!(oa_splink_registry_rs, oasplinkregistry_rs, "oaSplinkRegistry_rs");
    add_submodule!(oa_splink_core_rs, oasplinkcore_rs, "oaSplinkCore_rs");
    add_submodule!(oa_disk_flusher_rs, oadiskflusher_rs, "oaDiskFlusher_rs");
    add_submodule!(oa_task_pool_rs, oataskpool_rs, "oaTaskPool_rs");
    add_submodule!(oa_translator_core_rs, oatranslatorcore_rs, "oaTranslatorCore_rs");
    add_submodule!(oa_trie_rs, oatrie_rs, "oaTrie_rs");
    add_submodule!(oa_state_differ_rs, oaStateDiffer_rs, "oaStateDiffer_rs");
    add_submodule!(oa_state_registry_rs, oastateregistry_rs, "oaStateRegistry_rs");
    add_submodule!(oa_markdown_compiler_rs, oaMarkdownCompiler_rs, "oaMarkdownCompiler_rs");
    add_submodule!(oa_log_aligner_rs, oalogaligner_rs, "oaLogAligner_rs");
    add_submodule!(oa_debug_toggler_rs, oadebugtoggler_rs, "oaDebugToggler_rs");
    add_submodule!(oa_log_processor_rs, oalogprocessor_rs, "oaLogProcessor_rs");
    add_submodule!(oa_manifest_gen_rs, oamanifestgen_rs, "oaManifestGen_rs");

    Ok(())
}
