// oaComREST/Methods/oaFastAPI-rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260331.1820.1

use pyo3::prelude::*;
use axum::{
    routing::{get, post},
    Router,
    extract::{State, Path},
    Json,
};
use std::sync::{Arc, Mutex};
use std::collections::HashMap;
use tokio::runtime::Runtime;
use serde_json::Value;

#[pyclass]
struct RestServer {
    runtime: Option<Runtime>,
    routes: Arc<Mutex<HashMap<String, Py<PyAny>>>>,
}

#[pymethods]
impl RestServer {
    #[new]
    fn new() -> Self {
        RestServer {
            runtime: Some(Runtime::new().unwrap()),
            routes: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    fn add_route(&self, path: String, callback: Py<PyAny>) {
        let mut routes = self.routes.lock().unwrap();
        routes.insert(path, callback);
    }

    fn start(&mut self, host: String, port: u16) -> PyResult<()> {
        let routes = self.routes.clone();
        let rt = self.runtime.take().ok_or_else(|| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Server already started"))?;
        
        std::thread::spawn(move || {
            let app = Router::new()
                .route("/api/*path", get(handle_get))
                .with_state(routes);

            let addr = format!("{}:{}", host, port);
            rt.block_on(async {
                let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
                axum::serve(listener, app).await.unwrap();
            });
        });

        Ok(())
    }
}

async fn handle_get(
    Path(path): Path<String>,
    State(routes): State<Arc<Mutex<HashMap<String, Py<PyAny>>>>>,
) -> Json<Value> {
    let full_path = format!("/api/{}", path);
    let routes = routes.lock().unwrap();
    
    if let Some(callback) = routes.get(&full_path) {
        // Here we'd need to call into Python.
        // This requires the GIL, which we don't have here in the async handler.
        // For now, return a placeholder.
        Json(serde_json::json!({"error": "GIL needed for Python callback", "path": full_path}))
    } else {
        Json(serde_json::json!({"error": "Route not found", "path": full_path}))
    }
}

#[pymodule]
fn oafastapi_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<RestServer>()?;
    Ok(())
}
