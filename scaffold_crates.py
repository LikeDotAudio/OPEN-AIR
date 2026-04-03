import os
import subprocess

CRATES = [
    {"dir": "oaComVisa/Core/oaVisaCore_rs", "name": "oavisacore_rs"},
    {"dir": "oaGuiBuilder/Core/oaGeometryMath_rs", "name": "oageometrymath_rs"},
    {"dir": "oaTranslator/Core/oaTranslatorCore_rs", "name": "oatranslatorcore_rs"},
    {"dir": "oaGuiManager/FileReaders/oaBlueprintParser_rs", "name": "oablueprintparser_rs"},
]

CARGO_TOML_TPL = """[package]
name = "{name}"
version = "0.1.0"
edition = "2021"

[lib]
name = "{name}"
crate-type = ["cdylib"]

[dependencies]
pyo3 = {{ version = "0.21.0", features = ["extension-module"] }}

[profile.release]
lto = true
"""

PYPROJECT_TOML_TPL = """[build-system]
requires = ["maturin>=1.0,<2.0"]
build-backend = "maturin"

[project]
name = "{name}"
version = "0.1.0"
"""

HOOK_TPL = """import sys
import os
import subprocess

def ensure_compiled():
    try:
        import {name}
        return
    except ImportError:
        pass
    
    print("🦀 Compiling {name}...")
    crate_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        subprocess.run([sys.executable, "-m", "maturin", "develop", "--release"], cwd=crate_dir, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to compile {name}: {{e}}")
        raise e
"""

LIB_RS_TPL = """use pyo3::prelude::*;

#[pyfunction]
fn hello() -> PyResult<String> {{
    Ok("Hello from {name}".to_string())
}}

#[pymodule]
fn {name}(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {{
    m.add_function(wrap_pyfunction!(hello, m)?)?;
    Ok(())
}}
"""

for c in CRATES:
    d = c["dir"]
    name = c["name"]
    os.makedirs(os.path.join(d, "src"), exist_ok=True)
    
    with open(os.path.join(d, "Cargo.toml"), "w") as f:
        f.write(CARGO_TOML_TPL.format(name=name))
    with open(os.path.join(d, "pyproject.toml"), "w") as f:
        f.write(PYPROJECT_TOML_TPL.format(name=name))
    with open(os.path.join(d, "compiler_hook.py"), "w") as f:
        f.write(HOOK_TPL.format(name=name))
    with open(os.path.join(d, "src", "lib.rs"), "w") as f:
        f.write(LIB_RS_TPL.format(name=name))

    print(f"Scaffolded {name}")
