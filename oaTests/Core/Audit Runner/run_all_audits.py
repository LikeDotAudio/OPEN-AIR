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

    # Generate a timestamp for the log file
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    log_file_path = os.path.join(OUTPUT_DIR, f"AuditLog_{timestamp}.md")

    # Filter for Audit files, skipping AuditAll.toml
    audit_files = sorted([f for f in audit_path.glob("Audit*.toml") if f.name != "AuditAll.toml"])
    
    if not audit_files:
        print("No audit files found.")
        return

    # Open the log file in append mode ('a')
    with open(log_file_path, "a", encoding="utf-8") as f_out:
        # Write a session header with the current timestamp
        f_out.write(f"# Audit Session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f_out.write(f"**Model used:** {DEFAULT_MODEL}\n\n---\n\n")

        for file_path in audit_files:
            print(f"🔍 Running: {file_path.name}...")
            prompt_content = extract_prompt_from_toml(file_path)
            
            if not prompt_content:
                print(f"⚠️  No prompt content found in {file_path.name}.")
                f_out.write(f"## File: {file_path.name} (SKIPPED)\n\n")
                f_out.write("No prompt content found in the TOML file.\n\n---\n\n")
                continue
                
            try:
                # Execute the command with npx gemini
                # Pass the prompt content as input to the command
                result = subprocess.run(
                    GEMINI_CMD_BASE,
                    input=prompt_content,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                output_text = result.stdout.strip()
                
                # Log to the markdown file
                f_out.write(f"## File: {file_path.name} (PASSED)\n\n")
                f_out.write(f"{output_text}\n\n") # Model output is already markdown
                f_out.write("---\n\n")
                
                print(f"✅ Success: {file_path.name} recorded.")
                
            except subprocess.CalledProcessError as e:
                error_detail = e.stderr.strip()
                print(f"❌ Failed {file_path.name} (Exit Code {e.returncode})")
                
                # Log the error to the file
                f_out.write(f"## File: {file_path.name} (FAILED)\n\n")
                f_out.write(f"**Exit Code:** {e.returncode}\n\n")
                f_out.write(f"**Error Details:**\n\n```text\n{error_detail}\n```\n\n")
                if e.stdout:
                    f_out.write(f"**Partial Output:**\n\n{e.stdout.strip()}\n\n")
                f_out.write("---\n\n")

            except FileNotFoundError:
                print(f"❌ Error: Command '{GEMINI_CMD_BASE[0]}' not found. Ensure Node.js and npx are installed and in your PATH.")
                f_out.write(f"## File: {file_path.name} (ERROR)\n\n")
                f_out.write(f"**Error:** Command '{GEMINI_CMD_BASE[0]}' not found. Ensure Node.js and npx are installed and in your PATH.\n\n---\n\n")
                break # Stop if the command itself isn't found
            except Exception as e:
                print(f"❌ Unexpected error on {file_path.name}: {e}")
                f_out.write(f"## File: {file_path.name} (UNEXPECTED ERROR)\n\n")
                f_out.write(f"**Error:** {e}\n\n---\n\n")

    print(f"🏁 All audits completed. Results saved in {log_file_path}")

if __name__ == "__main__":
    run_all_audits()
