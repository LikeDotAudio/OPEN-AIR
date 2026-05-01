import os
import re
import shutil

# The raw list of 59 crates
CRATES = [
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

def to_snake_case(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

def run_migration():
    # Base directory for the new core
    core_src_dir = os.path.join("oaRustCore", "src")
    os.makedirs(core_src_dir, exist_ok=True)

    lib_rs_content = ["use pyo3::prelude::*;\n"]
    pymodule_content = ["#[pymodule]", "fn oaRustCore(_py: Python, m: &PyModule) -> PyResult<()> {"]

    for crate_path in CRATES:
        original_name = crate_path.split("/")[-1]
        # Clean up the name format
        snake_name = to_snake_case(original_name).replace("__", "_")

        # 1. Create the dedicated module folder
        module_dir = os.path.join(core_src_dir, snake_name)
        os.makedirs(module_dir, exist_ok=True)

        # 2. Recursive Copy of the entire src directory (lib.rs becomes mod.rs)
        source_src = os.path.join(crate_path, "src")

        if os.path.exists(source_src):
            # Clear target first to avoid dirty migration
            if os.path.exists(module_dir):
                shutil.rmtree(module_dir)
            os.makedirs(module_dir, exist_ok=True)

            for item in os.listdir(source_src):
                s = os.path.join(source_src, item)
                d = os.path.join(module_dir, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)

            # Special Case: lib.rs in the submodule folder should be mod.rs for the parent
            legacy_lib = os.path.join(module_dir, "lib.rs")
            if os.path.exists(legacy_lib):
                os.rename(legacy_lib, os.path.join(module_dir, "mod.rs"))

            print(f"Migrated full source: {original_name} -> {snake_name}/")
        else:
            print(f"WARNING: Source src not found - {source_src}")

        # 3. Build master lib.rs strings
        lib_rs_content.append(f"pub mod {snake_name};")
        pymodule_content.append(f"    m.add_submodule({snake_name}::create_module(_py)?)?;")

    pymodule_content.append("    Ok(())")
    pymodule_content.append("}")

    # 4. Write the Master lib.rs file
    with open(os.path.join(core_src_dir, "lib.rs"), "w") as f:
        f.write("\n".join(lib_rs_content) + "\n\n" + "\n".join(pymodule_content))
    print("\nSuccessfully generated folder-based oaRustCore/src/lib.rs architecture!")

if __name__ == "__main__":
    run_migration()
