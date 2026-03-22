# Audit Runner/run_all_audits.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import os
import subprocess
import pathlib
from datetime import datetime

# Directory containing the audit TOML files
AUDIT_DIR = "/home/anthony/Documents/OPEN-AIR/.gemini/commands"
# Directory to save the audit logs
OUTPUT_DIR = "/home/anthony/Documents/OPEN-AIR/oaDataAudits"

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
                stripped_line = line.strip()
                
                if stripped_line.startswith('prompt = """'):
                    in_multiline = True
                    # Extract content after 'prompt = """' on the same line
                    prompt_part = stripped_line[len('prompt = """'):]
                    prompt_lines.append(prompt_part)
                    continue
                
                if in_multiline:
                    if stripped_line.endswith('"""'):
                        # Extract content before '"""'
                        prompt_part = stripped_line[:-len('"""')]
                        prompt_lines.append(prompt_part)
                        in_multiline = False
                        break # Found the end of the prompt
                    else:
                        # Append the line as is, preserving internal newlines
                        prompt_lines.append(line.rstrip())
            
            # Clean up and join
            if prompt_lines:
                return "\n".join(prompt_lines).strip()
            else:
                return None
                
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error parsing TOML file {file_path}: {e}")
        return None
def run_all_audits():
    print(f"🚀 Starting Audits using {DEFAULT_MODEL}...")
    audit_path = pathlib.Path(AUDIT_DIR)
    
    if not audit_path.exists():
        print(f"❌ Error: Audit directory not found: {AUDIT_DIR}")
        return

    # Ensure the output directory exists
    pathlib.Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # Filter for Audit files, skipping AuditAll.toml
    audit_files = sorted([f for f in audit_path.glob("Audit*.toml") if f.name != "AuditAll.toml"])
    
    if not audit_files:
        print("No audit files found.")
        return

    session_results = []
    session_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    for file_path in audit_files:
        audit_name = file_path.stem # e.g., AuditArchitecture
        audit_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        individual_log_name = f"{audit_name}_{audit_timestamp}.md"
        individual_log_path = os.path.join(OUTPUT_DIR, individual_log_name)
        
        print(f"🔍 Running: {file_path.name}...")
        prompt_content = extract_prompt_from_toml(file_path)
        
        result_entry = ""
        status = "UNKNOWN"

        if not prompt_content:
            print(f"⚠️  No prompt content found in {file_path.name}.")
            status = "SKIPPED"
            result_entry = f"## File: {file_path.name} (SKIPPED)\n\nNo prompt content found in the TOML file.\n\n---\n\n"
        else:
            try:
                # Execute the command with npx gemini
                result = subprocess.run(
                    GEMINI_CMD_BASE,
                    input=prompt_content,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                output_text = result.stdout.strip()
                status = "PASSED"
                result_entry = f"## File: {file_path.name} (PASSED)\n\n{output_text}\n\n---\n\n"
                print(f"✅ Success: {file_path.name} recorded.")
                
            except subprocess.CalledProcessError as e:
                error_detail = e.stderr.strip()
                print(f"❌ Failed {file_path.name} (Exit Code {e.returncode})")
                status = "FAILED"
                result_entry = f"## File: {file_path.name} (FAILED)\n\n"
                result_entry += f"**Exit Code:** {e.returncode}\n\n"
                result_entry += f"**Error Details:**\n\n```text\n{error_detail}\n```\n\n"
                if e.stdout:
                    result_entry += f"**Partial Output:**\n\n{e.stdout.strip()}\n\n"
                result_entry += "---\n\n"

            except FileNotFoundError:
                print(f"❌ Error: Command '{GEMINI_CMD_BASE[0]}' not found.")
                status = "ERROR"
                result_entry = f"## File: {file_path.name} (ERROR)\n\n"
                result_entry += f"**Error:** Command '{GEMINI_CMD_BASE[0]}' not found.\n\n---\n\n"
            except Exception as e:
                print(f"❌ Unexpected error on {file_path.name}: {e}")
                status = "UNEXPECTED ERROR"
                result_entry = f"## File: {file_path.name} (UNEXPECTED ERROR)\n\n"
                result_entry += f"**Error:** {e}\n\n---\n\n"

        # Write individual audit file IMMEDIATELY
        with open(individual_log_path, "w", encoding="utf-8") as f_ind:
            f_ind.write(f"# Audit Result: {audit_name}\n")
            f_ind.write(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f_ind.write(f"**Model:** {DEFAULT_MODEL}\n\n")
            f_ind.write(result_entry)
        
        session_results.append(result_entry)
        
        if status == "ERROR":
            break # Stop if the command itself isn't found

    # Create the combined session log at the END
    session_log_path = os.path.join(OUTPUT_DIR, f"AuditSession_{session_timestamp}.md")
    with open(session_log_path, "w", encoding="utf-8") as f_session:
        f_session.write(f"# Audit Session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f_session.write(f"**Model used:** {DEFAULT_MODEL}\n\n---\n\n")
        for entry in session_results:
            f_session.write(entry)

    print(f"🏁 All audits completed. Session log saved in {session_log_path}")

if __name__ == "__main__":
    run_all_audits()
