import os
import subprocess
import pathlib

# Directory containing the audit TOML files
AUDIT_DIR = "/home/anthony/Documents/OPEN-AIR/.gemini/commands"

# Set Flash Lite as the default to save on cost and increase speed
DEFAULT_MODEL = "gemini-2.5-flash-lite"
GEMINI_CMD_BASE = ["npx", "gemini", "--model", DEFAULT_MODEL]

def extract_prompt_from_toml(file_path):
    """Parses TOML to extract the multiline 'prompt' string."""
    prompt_lines = []
    in_multiline = False
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if 'prompt = """' in line:
                    in_multiline = True
                    content = line.split('"""', 1)[1].strip()
                    if content: prompt_lines.append(content)
                    continue
                if in_multiline:
                    if '"""' in line:
                        content = line.split('"""', 1)[0].strip()
                        if content: prompt_lines.append(content)
                        in_multiline = False
                        break
                    else:
                        prompt_lines.append(line.rstrip())
        return "\n".join(prompt_lines).strip() if prompt_lines else None
    except Exception as e:
        print(f"❌ Error parsing {file_path}: {e}")
        return None

def run_all_audits():
    print(f"🚀 Starting Audits using {DEFAULT_MODEL}...")
    audit_path = pathlib.Path(AUDIT_DIR)
    
    if not audit_path.exists():
        print(f"❌ Error: Audit directory not found: {AUDIT_DIR}")
        return

    # Filter for Audit files, skipping AuditAll.toml
    audit_files = sorted([f for f in audit_path.glob("Audit*.toml") if f.name != "AuditAll.toml"])
    
    if not audit_files:
        print("No audit files found.")
        return

    for file_path in audit_files:
        print(f"\n--- 🔍 Running: {file_path.name} ---")
        prompt_content = extract_prompt_from_toml(file_path)
        
        if not prompt_content:
            print("⚠️  No prompt content found.")
            continue
            
        try:
            # Running with Flash Lite by default
            result = subprocess.run(
                GEMINI_CMD_BASE,
                input=prompt_content,
                capture_output=True,
                text=True,
                check=True
            )
            
            print(f"✅ Success")
            if result.stdout:
                print(f"Output:\n{result.stdout.strip()}")
                
        except subprocess.CalledProcessError as e:
            # Handle Quota or API errors
            if "QUOTA_EXHAUSTED" in e.stderr or "429" in e.stderr:
                print("❌ Quota exhausted even on Flash Lite. Please check your API limits.")
            else:
                print(f"❌ Failed (Exit Code {e.returncode})")
                if e.stderr:
                    print(f"Error Detail:\n{e.stderr.strip()}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

    print("\n🏁 All audits completed.")

if __name__ == "__main__":
    run_all_audits()