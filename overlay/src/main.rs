use tauri::Manager;
use tauri::WindowBuilder;
use tauri::WindowUrl;

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let window = WindowBuilder::new(
                app,
                "main",
                WindowUrl::App("index.html".into())
            )
            .title("AI Assistant Overlay")
            .decorations(false)
            .transparent(true)
            .always_on_top(true)
            .skip_taskbar(true)
            .build()?;

            // Set window properties
            window.set_ignore_cursor_events(true)?;
            window.set_focusable(false)?;
            
            // Handle window events
            window.on_window_event(|event| {
                match event {
                    tauri::WindowEvent::CloseRequested { .. } => {
                        // Prevent window from closing
                        event.prevent_default();
                    }
                    _ => {}
                }
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            toggle_interaction,
            capture_screen,
            send_message
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[tauri::command]
fn toggle_interaction(window: tauri::Window, should_interact: bool) {
    window.set_ignore_cursor_events(!should_interact).unwrap();
}

#[tauri::command]
async fn capture_screen() -> Result<Vec<u8>, String> {
    // Implement screen capture logic
    Ok(Vec::new())
}

#[tauri::command]
async fn send_message(message_type: String, payload: String) -> Result<(), String> {
    // Implement message sending logic
    Ok(())
}
