import os
import subprocess

modules = [
    ("oaComAES70", "oaAES70Core-rs", "Methods"),
    ("oaComEmber", "oaEmberTree-rs", "Methods"),
    ("oaComMidi", "oaMidiEngine-rs", "Methods"),
    ("oaComREST", "oaFastAPI-rs", "Methods"),
    ("oaComSMPTE2138", "oaST2138Codec-rs", "Methods"),
    ("oaComSNMP", "oaSNMPAgent-rs", "Methods"),
    ("oaComVisa", "oaVisaFormat-rs", "Methods"),
    ("oaPTP", "oaPTPClock-rs", "Methods"),
    ("oaFileImportCSV", "oaCSVParser-rs", "Methods"),
    ("oaFileExportCSV", "oaCSVWriter-rs", "Methods"),
    ("oaFileImportHTML", "oaHTMLScraper-rs", "Methods"),
    ("oaFileImportShow", "oaShowfileUnpacker-rs", "Methods"),
    ("oaReports", "oaReportGen-rs", "Methods"),
    ("oaConfiguration", "oaConfigEngine-rs", "Methods"),
    ("oaDocumentation", "oaMarkdownCompiler-rs", "Methods"),
    ("oaStand_Alone_Utilities", "oaLogAligner-rs", "Methods"),
    ("oaDataAudits", "oaStateDiffer-rs", "Methods"),
    ("oaDataLogs", "oaAsyncLogger-rs", "Methods"),
    ("oaDataSNMP", "oaMIBCache-rs", "Methods"),
    ("oaDataSplinks", "oaSplinkGraph-rs", "Methods"),
    ("oaDataCache", "oaDiskFlusher-rs", "Methods"),
    ("oaThreadManager", "oaThreadPool-rs", "Methods"),
    ("oaOchestration", "oaHeartbeatCore-rs", "Methods"),
    ("oaGuiTelemetry", "oaTimeSeriesDB-rs", "Methods"),
    ("oaGuiMediaElements", "oaImageScaler-rs", "Methods"),
    ("oaStyle", "oaCSSParser-rs", "Methods"),
    ("oaGuiBuildShell", "oaLayoutEngine-rs", "Methods"),
    ("oaGuiEditorWYSIWYG", "oaHitboxMath-rs", "Methods"),
    ("oaGuiFolderParser", "oaFastDir-rs", "Methods"),
    ("oaTranslator", "oaManifestGen-rs", "Methods"),
]

def scaffold():
    base_dir = "/home/anthony/Documents/OPEN-AIR"
    
    for mod_dir, rust_name, sub_dir in modules:
        target_path = os.path.join(base_dir, mod_dir, sub_dir, rust_name)
        if os.path.exists(target_path):
            print(f"Skipping {rust_name}, already exists at {target_path}")
            continue
            
        print(f"Scaffolding {rust_name} in {mod_dir}...")
        
        # Ensure parent exists
        os.makedirs(os.path.join(base_dir, mod_dir, sub_dir), exist_ok=True)
        
        # Cargo new
        subprocess.run(["cargo", "new", "--lib", rust_name], cwd=os.path.join(base_dir, mod_dir, sub_dir), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Update Cargo.toml
        cargo_toml_path = os.path.join(target_path, "Cargo.toml")
        mod_name_snake = rust_name.replace("-", "_")
        with open(cargo_toml_path, "a") as f:
            f.write(f"\n[lib]\nname = \"{mod_name_snake}\"\ncrate-type = [\"cdylib\"]\n\n[dependencies]\npyo3 = {{ version = \"0.21.0\", features = [\"extension-module\"] }}\n")
            
        # Create pyproject.toml
        pyproject_path = os.path.join(target_path, "pyproject.toml")
        with open(pyproject_path, "w") as f:
            f.write(f"""[build-system]
requires = ["maturin>=1.0,<2.0"]
build-backend = "maturin"

[project]
name = "{mod_name_snake}"
requires-python = ">=3.8"
classifiers = [
    "Programming Language :: Rust",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
]
""")

        # Create basic lib.rs
        lib_rs_path = os.path.join(target_path, "src", "lib.rs")
        with open(lib_rs_path, "w") as f:
            f.write(f"""use pyo3::prelude::*;

#[pyfunction]
fn hello() -> PyResult<String> {{
    Ok("Hello from {rust_name}!".to_string())
}}

#[pymodule]
fn {mod_name_snake}(m: &Bound<'_, PyModule>) -> PyResult<()> {{
    m.add_function(wrap_pyfunction!(hello, m)?)?;
    Ok(())
}}
""")

        # Create compiler_hook.py in the Rust module dir
        hook_path = os.path.join(target_path, "compiler_hook.py")
        with open(hook_path, "w") as f:
            f.write(f"""import os, subprocess, sys

def ensure_compiled():
    module_dir = os.path.dirname(__file__)
    # Check if compiled lib exists
    has_so = any(f.endswith('.so') or f.endswith('.pyd') for f in os.listdir(module_dir))
    if not has_so:
        print(f"[{{module_dir}}] Native binary not found. Compiling via Cargo...")
        try:
            subprocess.run(["maturin", "develop", "--release"], cwd=module_dir, check=True)
            print("Compilation successful.")
        except subprocess.CalledProcessError:
            print("CRITICAL: Failed to compile Rust extension. Ensure Rust/Cargo is installed.")
            raise RuntimeError("Compilation failed")
""")

if __name__ == "__main__":
    scaffold()
