use std::collections::HashMap;
use std::fs;
use std::path::Path;
use serde_json::Value;
use log::{info, error, debug};

pub struct YakRepository {
    // Model Name -> (Command Name -> SCPI String)
    pub models: HashMap<String, HashMap<String, String>>,
}

impl YakRepository {
    pub fn new(root_path: &str) -> Self {
        let mut repo = YakRepository {
            models: HashMap::new(),
        };
        eprintln!("   🔍 [YAK REPO] Scanning YAK repository at: {}", root_path);
        repo.scan_directory(Path::new(root_path));
        
        let total_commands: usize = repo.models.values().map(|c| c.len()).sum();
        eprintln!("   ✅ [YAK REPO] Loaded {} models and {} total command definitions.", repo.models.len(), total_commands);
        repo
    }

    fn scan_directory(&mut self, path: &Path) {
        if let Ok(entries) = fs::read_dir(path) {
            for entry in entries.flatten() {
                let p = entry.path();
                if p.is_dir() {
                    self.scan_directory(&p);
                } else if p.is_file() && p.extension().map_or(false, |ext| ext == "json") {
                    // Extract model name from the grandparent folder (e.g. 1_N9340B / 0_Frequency / file.json)
                    let mut model_name = String::new();
                    if let Some(parent) = p.parent() {
                        if let Some(grandparent) = parent.parent() {
                            model_name = grandparent.file_name().unwrap_or_default().to_string_lossy().to_string();
                        }
                    }
                    
                    if !model_name.is_empty() {
                        // Strip leading digits and underscore (e.g., "1_N9340B" -> "N9340B")
                        let clean_model = if let Some(idx) = model_name.find('_') {
                            if model_name[..idx].chars().all(|c| c.is_ascii_digit()) {
                                model_name[idx + 1..].to_string()
                            } else {
                                model_name.clone()
                            }
                        } else {
                            model_name.clone()
                        };

                        self.parse_file(&p, &clean_model);
                    }
                }
            }
        } else {
            error!("Failed to read directory: {:?}", path);
        }
    }

    fn parse_file(&mut self, path: &Path, model_name: &str) {
        if let Ok(content) = fs::read_to_string(path) {
            if let Ok(val) = serde_json::from_str::<Value>(&content) {
                self.extract_commands(&val, model_name);
            }
        }
    }

    fn extract_commands(&mut self, val: &Value, model_name: &str) {
        if let Value::Object(obj) = val {
            for (k, v) in obj {
                let mut found_msg = None;
                
                // Pattern B: direct "Execute Command" child
                if let Some(exec_cmd) = v.get("Execute Command") {
                    if let Some(msg) = exec_cmd.get("message").and_then(|m| m.as_str()) {
                        found_msg = Some(msg.to_string());
                    }
                }
                // Pattern A: "Execute Command" inside "fields"
                if let Some(fields) = v.get("fields") {
                    if let Some(exec_cmd) = fields.get("Execute Command") {
                        if let Some(msg) = exec_cmd.get("message").and_then(|m| m.as_str()) {
                            found_msg = Some(msg.to_string());
                        }
                    }
                }

                if let Some(msg) = found_msg {
                    self.models
                        .entry(model_name.to_string())
                        .or_insert_with(HashMap::new)
                        .insert(k.clone(), msg);
                }

                // Recurse to handle deep nesting
                self.extract_commands(v, model_name);
            }
        } else if let Value::Array(arr) = val {
            for item in arr {
                self.extract_commands(item, model_name);
            }
        }
    }

    pub fn get_scpi(&self, model_name: &str, command_name: &str) -> Option<String> {
        // Search specific model first
        if let Some(commands) = self.models.get(model_name) {
            if let Some(scpi) = commands.get(command_name) {
                return Some(scpi.clone());
            }
        }
        
        // Fallback: search all models (in case model name wasn't provided or didn't match perfectly)
        for commands in self.models.values() {
            if let Some(scpi) = commands.get(command_name) {
                return Some(scpi.clone());
            }
        }
        
        None
    }
}
