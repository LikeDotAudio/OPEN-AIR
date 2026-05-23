# oaTests/Workers/MakeDoxygen.py
# Author: Gemini
# Version: 20260427.2000.1
#
# Description: A simple script to run Doxygen on the project.
#
import os
import subprocess
import webbrowser


def make_doxygen():
    """
    Runs Doxygen on the project and opens the generated documentation.
    """
    script_dir = os.path.dirname(os.path.realpath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))
    doxyfile_path = os.path.join(project_root, 'Doxyfile')

    if not os.path.exists(doxyfile_path):
        print(f"Error: Doxyfile not found at {doxyfile_path}")
        return

    print(f"Running Doxygen with Doxyfile: {doxyfile_path}")
    try:
        subprocess.run(['doxygen', doxyfile_path], check=True, cwd=project_root)
        print("Doxygen run completed successfully.")

        # Open the generated documentation
        index_path = os.path.join(project_root, 'oaDocumentation', 'Doxygen', 'html', 'index.html')
        if os.path.exists(index_path):
            webbrowser.open('file://' + os.path.realpath(index_path))
            print(f"Opening documentation at: {index_path}")
        else:
            print(f"Error: Could not find generated index.html at {index_path}")

    except subprocess.CalledProcessError as e:
        print(f"Doxygen run failed with error: {e}")
    except FileNotFoundError:
        print("Error: 'doxygen' command not found. Is Doxygen installed and in your PATH?")

if __name__ == '__main__':
    make_doxygen()
