// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{WindowBuilder, WindowUrl, Manager};
use std::sync::{Arc, Mutex};
use std::process::Command;

// Define states
struct ScreenCaptureState(Arc<Mutex<Option<String>>>);

#[tauri::command]
async fn send_message(message_type: String, payload: String) -> Result<(), String> {
    println!("Send message: {} - {}", message_type, payload);
    Ok(())
}

#[tauri::command]
async fn capture_screen(app_handle: tauri::AppHandle) -> Result<String, String> {
    let state = app_handle.state::<ScreenCaptureState>();
    let screenshot = state.0.lock().unwrap().clone();
    
    match screenshot {
        Some(data) => Ok(data),
        None => Err("No screenshot data available".into())
    }
}

#[tauri::command]
async fn toggle_interaction(app_handle: tauri::AppHandle, should_interact: bool) -> Result<(), String> {
    if let Some(window) = app_handle.get_window("main") {
        window.set_ignore_cursor_events(!should_interact)
            .map_err(|e| e.to_string())?;
        
        println!("Interaction set to: {}", should_interact);
    }
    Ok(())
}

fn main() {
    let screen_capture_state = ScreenCaptureState(Arc::new(Mutex::new(None)));
    
    tauri::Builder::default()
        .manage(screen_capture_state)
        .setup(|app| {
            WindowBuilder::new(app, "main", WindowUrl::default())
                .title("AI Assistant Overlay")
                .resizable(true)
                .transparent(true)
                .decorations(false)
                .always_on_top(true)
                .build()?;
                
            // Start with interaction disabled (click-through)
            if let Some(window) = app.get_window("main") {
                window.set_ignore_cursor_events(true)
                    .expect("Failed to set cursor events");
            }
            
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            send_message,
            capture_screen,
            toggle_interaction
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
