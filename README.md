# AI Assistant Overlay

A Tauri-based overlay application that provides an intelligent interface transformation layer for local applications. The overlay processes all data locally and communicates with the Python backend through WebSocket connections.

## Features

- **Local Processing**: All interface transformations occur on the user's device
- **Real-time Updates**: Instant interface element updates and transformations
- **Privacy-First**: No external network calls or data sharing
- **Cross-Platform**: Works across different operating systems
- **Customizable**: Easy to extend with new element types and transformations

## Architecture

The overlay consists of several key components:

### 1. Window Manager
- Controls overlay window state and properties
- Manages window positioning and sizing
- Handles visibility and interaction settings

### 2. Event Handler
- Processes events between frontend and backend
- Manages interface transformation requests
- Handles interaction toggling and element updates

### 3. Overlay Manager
- Transforms interface elements based on type
- Manages element properties and states
- Handles interface updates and clearing

## Data Structures

### UI Elements
```rust
pub struct UIElement {
    pub id: String,
    pub element_type: String,
    pub x: i32,
    pub y: i32,
    pub width: u32,
    pub height: u32,
    pub properties: serde_json::Value,
}
```

### Transformed Elements
```rust
pub struct TransformedElement {
    pub original: UIElement,
    pub transformed_properties: serde_json::Value,
}
```

## Event Flow

1. **Interface Transformation**:
   - Frontend sends transform request with UI elements
   - Event handler processes request
   - Overlay manager transforms elements
   - Window manager updates display

2. **Interaction Toggling**:
   - Frontend sends toggle request
   - Event handler processes request
   - Window manager shows/hides window

3. **Element Updates**:
   - Frontend sends update request
   - Event handler processes request
   - Overlay manager updates element properties
   - Window manager refreshes display

## Getting Started

### Prerequisites

- Rust (latest stable version)
- Node.js (v16 or later)
- Tauri CLI

### Installation

1. Install dependencies:
```bash
npm install
```

2. Build the application:
```bash
npm run tauri build
```

### Development

1. Start the development server:
```bash
npm run tauri dev
```

2. Run tests:
```bash
npm test
```

## Project Structure

```
overlay/
├── src/              # Frontend source
│   ├── components/   # Svelte components
│   ├── services/     # Frontend services
│   └── ...
├── src-tauri/        # Tauri backend
│   ├── src/         # Rust source
│   └── ...
└── ...
```

## Building

```bash
# Development build
npm run tauri dev

# Production build
npm run tauri build
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Tauri for the cross-platform application framework
- Svelte for the frontend framework
- All contributors and maintainers 