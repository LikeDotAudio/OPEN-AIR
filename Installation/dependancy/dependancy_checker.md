# 📝 **Module Documentation: `dependancy_checker.py`** 🕵️‍♀️📦

**Student Name:** [Your Name]  
**Course:** Software Engineering 101  
**Date:** 2026-01-19  
**Assignment:** Project Documentation  

---

## 🧐 **Overview**
 this module is **CRITICAL**! 🚨 It ensures that the computer running our code has all the necessary Python libraries installed. It acts like a strict bouncer at a club 🕵️‍♂️—if you don't have the right "credentials" (libraries like `numpy`, `pandas`, `pyvisa`), you don't get in! It can even automatically install them using `pip`! 🤯

## 🛠️ **How It Works**
The script maintains a list of `EXTERNAL_PACKAGES` (things we need from PyPI) and `BUILTIN_PACKAGES`. It tries to import them.
*   If `CLEAN_INSTALL_MODE` is True, it **force uninstalls** and then **reinstalls** everything to ensure a fresh state. 🚿
*   If a package is missing, it runs a subprocess command to `pip install` it.
*   It handles weird permissions issues on Linux (Debian) by using the `--break-system-packages` flag (safely!) and detecting "managed by external" errors.

---

## 📚 **Imports**
*   `os`, `sys`, `subprocess`: For running system commands and pip. 🖥️
*   `importlib`: (Implicitly used via `__import__`).
*   `managers.configini.config`: To update config after install. 🏗️
*   `managers.configini.config_reader`: (Referenced in comments, but avoided to prevent circular deps).

---

## ⚙️ **Constants**
*   `EXTERNAL_PACKAGES`: Dictionary mapping friendly names to import names (e.g., `{"numpy": "numpy"}`).
*   `BUILTIN_PACKAGES`: Standard libs to check.
*   `FLAG_BREAK_SYSTEM_PACKAGES`: `"--break-system-packages"` (Important for modern Linux!).

---

## ⚙️ **Functions**

### 1️⃣ `_update_config_after_install(debug_log_func)`
**Description:**  
After a successful "Clean Install", this function flips the `CLEAN_INSTALL_MODE` switch to `False` and `SKIP_DEP_CHECK` to `True` in `config.ini`. This prevents the app from reinstalling everything *every* time it starts. Smart, right? 🧠

### 2️⃣ `_execute_pip_command(...)`
**Description:**  
The workhorse! 🐴 Executing shell commands safely.
**Arguments:** `action` ("install"/"uninstall"), `package_name`, logging funcs.
**Logic:**
1.  Builds the command: `python -m pip install [package] --break-system-packages`.
2.  Runs it using `subprocess.run`.
3.  **Error Handling:** Checks specifically for "permission denied" or "managed by debian" errors during uninstall and allows the process to continue gracefully. 🛡️
**Returns:** `True` (success/handled) or `False` (failure).

### 3️⃣ `action_check_dependancies(console_print_func, debug_log_func, should_clean_install)`
**Description:**  
The main logic loop.
**Logic:**
1.  Iterates through `EXTERNAL_PACKAGES`.
2.  Checks `should_clean_install`.
    *   **True:** Uninstall -> Install.
    *   **False:** Try Import -> If fail, Install.
3.  Iterates through `BUILTIN_PACKAGES` (just checks import).
4.  If anything fails, it prints a **CRITICAL FAILURE** message and instructions for manual installation. ❌
5.  If success, it logs a "glorious success"! 🎉

### 4️⃣ `run_interactive_pre_check(...)`
**Description:**  
The entry point called by the main launcher.
**Logic:**
1.  Checks `app_constants.SKIP_DEP_CHECK`. If true, returns immediately (Fast startup! ⚡).
2.  Otherwise, runs `action_check_dependancies`.
3.  If successful and was in clean mode, calls `_update_config_after_install`.

---

## 🎓 **Conclusion**
This script is super robust! It handles different OS quirks and ensures the environment is perfect before the main app logic runs. It prevents so many "ModuleNotFound" errors! 🙌