
import os
import re

def expand_msg(text):
    # 1. Whole word 'msg' -> 'message'
    text = re.sub(r'\bmsg\b', 'message', text)
    # 2. Whole word 'msgs' -> 'messages'
    text = re.sub(r'\bmsgs\b', 'messages', text)
    # 3. 'msg_' at the start of a word -> 'message_'
    text = re.sub(r'\bmsg_', 'message_', text)
    # 4. '_msg' at the end of a word -> '_message'
    text = re.sub(r'_msg\b', '_message', text)
    # 5. '_msg_' within a word -> '_message_'
    text = re.sub(r'_msg_', '_message_', text)
    # 6. '_msgs' at the end of a word -> '_messages'
    text = re.sub(r'_msgs\b', '_messages', text)
    # 7. 'Msg' (CamelCase) -> 'Message'
    text = re.sub(r'\bMsg\b', 'Message', text)
    # 8. 'Msgs' (CamelCase) -> 'Messages'
    text = re.sub(r'\bMsgs\b', 'Messages', text)
    # 9. 'Msg_' at the start of a word -> 'Message_'
    text = re.sub(r'\bMsg_', 'Message_', text)
    # 10. '_Msg' at the end of a word -> '_Message'
    text = re.sub(r'_Msg\b', '_Message', text)
    
    return text

def process_files():
    directories = [
        "oaAudioMixer", "oaComBroker", "oaComProtocols", "oaConfigurationManager", 
        "oaDocumentation", "oaFileExportCSV", "oaFileImportCSV", "oaFileImportHTML", 
        "oaFileImportPDF", "oaFileImportShow", "oaGui", "oaGuiBackground", 
        "oaGuiBuilder", "oaGuiEditorWYSIWYG", "oaGuiElements", "oaGuiManager", 
        "oaGuiMediaElements", "oaGuiShowtime", "oaGuiSplashScreen", "oaGuiTelemetry", 
        "oaInstallation", "oaLogging", "oaOchestration", "oaPTP", "oaRustCore", 
        "oaSplinker", "oaStand_Alone_Utilities", "oaStateCache", "oaStyle", "oaTests", 
        "oaThreadManager", "oaTranslator", "oaWatchdog", "openair.py"
    ]
    
    for item in directories:
        if os.path.isfile(item):
            process_file(item)
        elif os.path.isdir(item):
            for root, _, files in os.walk(item):
                for file in files:
                    if file.endswith(('.py', '.rs')):
                        process_file(os.path.join(root, file))

def process_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = expand_msg(content)
        
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated: {file_path}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    process_files()
