import os
import shutil

# The list of legacy paths from your previous structure
LEGACY_PATHS = [
    "oaAudioMixer/Core/oaAudioMixer_rs",
    "oaConfigurationManager/Methods/oaConfigEngine_rs",
    "oaLogging/Core/oaAsyncSink_rs",
    "oaLogging/Methods/oaLoggingGate_rs",
    "oaOchestration/Core/oaSafetyCore_rs",
    "oaOchestration/Methods/oaHeartbeatCore_rs",
    "oaThreadManager/Methods/oaThreadPool_rs",
    "oaWatchdog/Methods/oaClockSync_rs",
    "oaComBroker/Methods/oaCoreRouter_rs",
    "oaComProtocols/oaComAES70/Methods/oaAES70Core_rs",
    "oaComProtocols/oaComEmber/Methods/oaEmberTree_rs",
    "oaComProtocols/oaComMidi/Core/oaMidiMapper_rs",
    "oaComProtocols/oaComMidi/Methods/oaMidiEngine_rs",
    "oaComProtocols/oaComMQTT/Core/oaMQTTManager_rs",
    "oaComProtocols/oaComOSC/Methods/oaOSCCore_rs",
    "oaComProtocols/oaComREST/Methods/oaFastAPI_rs",
    "oaComProtocols/oaComSMPTE2138/Methods/oaST2138Codec_rs",
    "oaComProtocols/oaComSNMP/Methods/oaMIBCache_rs",
    "oaComProtocols/oaComSNMP/Methods/oaSNMPAgent_rs",
    "oaComProtocols/oaComVisa/Core/oaVisaCore_rs",
    "oaComProtocols/oaComVisa/Methods/oaVisaFormat_rs",
    "oaComProtocols/oaComVisa/Methods/oaVisaScanner_rs",
    "oaPTP/Methods/oaPTPClock_rs",
    "oaPTP/Methods/oaPtpParser_rs",
    "oaGui/Methods/oaFastDir_rs",
    "oaGui/Methods/oaLayoutEngine_rs",
    "oaGuiElements/Methods/oaPatternEngine_rs",
    "oaGui/Core/oaGeometryMath_rs",
    "oaGuiEditorWYSIWYG/Core/oaEditorState_rs",
    "oaGuiEditorWYSIWYG/Methods/oaHitboxMath_rs",
    "oaGuiElements/Core/metering/oaMeteringEngine_rs",
    "oaGuiElements/Methods/oaCMDPMath_rs",
    "oaGuiElements/Methods/oaNeedleEngine_rs",
    "oaGuiElements/Methods/oaNeedleGeometry_rs",
    "oaGuiElements/Methods/oaProceduralArt_rs",
    "oaGuiElements/Methods/oaRotaryCore_rs",
    "oaGui/Core/oaFastScanner_rs",
    "oaGui/FileReaders/oaBlueprintParser_rs",
    "oaGui/Methods/oaImageScaler_rs",
    "oaGui/Methods/oaTimeSeriesDB_rs",
    "oaStyle/Methods/oaCSSParser_rs",
    "oaFileExportCSV/Methods/oaCSVWriter_rs",
    "oaFileImportCSV/Methods/oaCSVParser_rs",
    "oaFileImportHTML/Methods/oaHTMLScraper_rs",
    "oaFileImportPDF/Methods/oaPDFParser_rs",
    "oaFileImportShow/Methods/oaShowfileUnpacker_rs",
    "oaSplinker/Core/oaSplinkRegistry_rs",
    "oaSplinker/Methods/oaSplinkCore_rs",
    "oaStateCache/Core/oaDiskFlusher_rs",
    "oaStateCache/Core/oaTaskPool_rs",
    "oaStateCache/Core/oaTranslatorCore_rs",
    "oaStateCache/Core/oaTrie_rs",
    "oaStateCache/Methods/oaStateDiffer_rs",
    "oaStateCache/Methods/oaStateRegistry_rs",
    "oaDocumentation/Methods/oaMarkdownCompiler_rs",
    "oaStand_Alone_Utilities/Methods/oaLogAligner_rs",
    "oaTests/Methods/oaDebugToggler_rs",
    "oaTests/Methods/oaLogProcessor_rs",
    "oaTranslator/Methods/oaManifestGen_rs"
]

def purge_the_schmutz():
    freed_space_count = 0

    for path in LEGACY_PATHS:
        # 1. Purge 'target' (The 6GB culprit)
        target_path = os.path.join(path, "target")
        if os.path.exists(target_path):
            print(f"Purging build artifacts: {target_path}")
            shutil.rmtree(target_path)
            freed_space_count += 1

        # 2. Remove Cargo.toml
        cargo_file = os.path.join(path, "Cargo.toml")
        if os.path.exists(cargo_file):
            print(f"Removing legacy config: {cargo_file}")
            os.remove(cargo_file)

        # 3. Remove Cargo.lock
        lock_file = os.path.join(path, "Cargo.lock")
        if os.path.exists(lock_file):
            os.remove(lock_file)

        # 4. Remove src folder
        src_path = os.path.join(path, "src")
        if os.path.exists(src_path):
            print(f"Cleaning legacy source: {src_path}")
            shutil.rmtree(src_path)

        # 5. Remove compiler_hook.py
        hook_path = os.path.join(path, "compiler_hook.py")
        if os.path.exists(hook_path):
            print(f"Removing legacy hook: {hook_path}")
            os.remove(hook_path)

    print("\n" + "="*30)
    print(f"CLEANUP COMPLETE: {freed_space_count} legacy build environments purged.")
    print("Your disk should be significantly lighter now, Anthony.")
    print("="*30)

if __name__ == "__main__":
    purge_the_schmutz()
