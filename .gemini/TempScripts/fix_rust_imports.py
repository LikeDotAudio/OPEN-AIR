import os
import re

IMPORT_MAP = {
    "oaAudioMixer_rs": "oa_audio_mixer_rs",
    "oaConfigEngine_rs": "oa_config_engine_rs",
    "oaAsyncSink_rs": "oa_async_sink_rs",
    "oaLoggingGate_rs": "oa_logging_gate_rs",
    "oaSafetyCore_rs": "oa_safety_core_rs",
    "oaHeartbeatCore_rs": "oa_heartbeat_core_rs",
    "oaThreadPool_rs": "oa_thread_pool_rs",
    "oaClockSync_rs": "oa_clock_sync_rs",
    "oaCoreRouter_rs": "oa_core_router_rs",
    "oaAES70Core_rs": "oa_aes70_core_rs",
    "oaEmberTree_rs": "oa_ember_tree_rs",
    "oaMidiMapper_rs": "oa_midi_mapper_rs",
    "oaMidiEngine_rs": "oa_midi_engine_rs",
    "oaMQTTManager_rs": "oa_mqtt_manager_rs",
    "oaOSCCore_rs": "oa_osc_core_rs",
    "oaFastAPI_rs": "oa_fast_api_rs",
    "oaST2138Codec_rs": "oa_st2138_codec_rs",
    "oaMIBCache_rs": "oa_mib_cache_rs",
    "oaSNMPAgent_rs": "oa_snmp_agent_rs",
    "oaVisaCore_rs": "oa_visa_core_rs",
    "oaVisaFormat_rs": "oa_visa_format_rs",
    "oaVisaScanner_rs": "oa_visa_scanner_rs",
    "oaPTPClock_rs": "oa_ptp_clock_rs",
    "oaPtpParser_rs": "oa_ptp_parser_rs",
    "oaFastDir_rs": "oa_fast_dir_rs",
    "oaLayoutEngine_rs": "oa_layout_engine_rs",
    "oaPatternEngine_rs": "oa_pattern_engine_rs",
    "oaGeometryMath_rs": "oa_geometry_math_rs",
    "oaEditorState_rs": "oa_editor_state_rs",
    "oaHitboxMath_rs": "oa_hitbox_math_rs",
    "oaMeteringEngine_rs": "oa_metering_engine_rs",
    "oaCMDPMath_rs": "oa_cmdp_math_rs",
    "oaNeedleEngine_rs": "oa_needle_engine_rs",
    "oaNeedleGeometry_rs": "oa_needle_geometry_rs",
    "oaProceduralArt_rs": "oa_procedural_art_rs",
    "oaRotaryCore_rs": "oa_rotary_core_rs",
    "oaFastScanner_rs": "oa_fast_scanner_rs",
    "oaBlueprintParser_rs": "oa_blueprint_parser_rs",
    "oaImageScaler_rs": "oa_image_scaler_rs",
    "oaTimeSeriesDB_rs": "oa_time_series_db_rs",
    "oaCSSParser_rs": "oa_css_parser_rs",
    "oaCSVWriter_rs": "oa_csv_writer_rs",
    "oaCSVParser_rs": "oa_csv_parser_rs",
    "oaHTMLScraper_rs": "oa_html_scraper_rs",
    "oaPDFParser_rs": "oa_pdf_parser_rs",
    "oaShowfileUnpacker_rs": "oa_showfile_unpacker_rs",
    "oaSplinkRegistry_rs": "oa_splink_registry_rs",
    "oaSplinkCore_rs": "oa_splink_core_rs",
    "oaDiskFlusher_rs": "oa_disk_flusher_rs",
    "oaTaskPool_rs": "oa_task_pool_rs",
    "oaTranslatorCore_rs": "oa_translator_core_rs",
    "oaTrie_rs": "oa_trie_rs",
    "oaStateDiffer_rs": "oa_state_differ_rs",
    "oaStateRegistry_rs": "oa_state_registry_rs",
    "oaMarkdownCompiler_rs": "oa_markdown_compiler_rs",
    "oaLogAligner_rs": "oa_log_aligner_rs",
    "oaDebugToggler_rs": "oa_debug_toggler_rs",
    "oaLogProcessor_rs": "oa_log_processor_rs",
    "oaManifestGen_rs": "oa_manifest_gen_rs"
}

def fix_content(content):
    # 1. Remove all compiler_hook imports
    # Handles:
    #     #     #     content = re.sub(r"    content = re.sub(r"    content = re.sub(r"    
 calls
    content = re.sub(r"^\s*.*ensure_compiled\(\)\n?", "", content, flags=re.MULTILINE)

    # 3. Update imports
    sorted_keys = sorted(IMPORT_MAP.keys(), key=len, reverse=True)
    
    for old_camel in sorted_keys:
        new_snake = IMPORT_MAP[old_camel]
        old_lower = old_camel.lower()
        
        mod_pattern = rf"({old_camel}|{old_lower})"
        
        # Replace 'import old_rs' -> 'from oaRustCore import new_snake as old_rs'
        import_stmt_pattern = re.compile(rf"\bimport {mod_pattern}\b(?!\s+import)", re.IGNORECASE)
        def repl_import(m):
            actual_used = m.group(1)
            return f"from oaRustCore import {new_snake} as {actual_used}"
        content = import_stmt_pattern.sub(repl_import, content)
        
        # Replace 'from [.]old_rs[.old_rs] import X' -> 'from oaRustCore.new_snake import X'
        from_stmt_pattern = re.compile(rf"\bfrom \.?\.?{mod_pattern}(\.{mod_pattern})?\s+import\b", re.IGNORECASE)
        content = from_stmt_pattern.sub(f"from oaRustCore.{new_snake} import", content)

    # Final cleanup of multiple newlines
    content = re.sub(r"\n{3,}", "\n\n", content)
    
    return content

if __name__ == "__main__":
    import sys
    for file_path in sys.argv[1:]:
        if not os.path.isfile(file_path): continue
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        new_content = fix_content(content)
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Fixed: {file_path}")
