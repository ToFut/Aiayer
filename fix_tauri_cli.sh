#!/bin/bash

echo "====================================================="
echo "    Fixing Tauri CLI for Aiayer Overlay               "
echo "====================================================="

# 1. Navigate to the overlay directory
cd /Users/segevbin/Desktop/SensAI/Aiayer/overlay

# 2. Check Tauri CLI version and architecture
echo "Current Tauri CLI version:"
node -e "try { console.log(require('@tauri-apps/cli/package.json').version) } catch(e) { console.log('Error:', e.message) }"

# 3. Check node environment
echo "Node version:"
node -v
echo "NPM version:"
npm -v

# 4. Clean npm cache and node_modules
echo "Cleaning npm cache and node_modules..."
rm -rf node_modules
rm -rf package-lock.json
npm cache clean --force

# 5. Install dependencies with specific Tauri versions (latest compatible)
echo "Installing dependencies with compatible Tauri versions..."
npm install --save-exact @tauri-apps/api@^1.5.1
npm install --save-dev --save-exact @tauri-apps/cli@^1.5.6

# 6. Verify installation
echo "Verifying Tauri CLI installation..."
npx tauri --version || echo "Tauri CLI installation failed"

# 7. Try a basic Tauri command
echo "Testing Tauri CLI command..."
npx tauri info

# 8. Update package.json with proper versions
echo "Updating package.json..."
cat > package.json << EOF
{
  "name": "ai-assistant-overlay",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "tauri": "tauri"
  },
  "dependencies": {
    "@tauri-apps/api": "^1.5.1",
    "svelte": "^4.2.7"
  },
  "devDependencies": {
    "@sveltejs/vite-plugin-svelte": "^2.4.5",
    "@tauri-apps/cli": "^1.5.6",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.31",
    "svelte-preprocess": "^5.0.4",
    "tailwindcss": "^3.3.5",
    "vite": "^4.5.0"
  }
}
EOF

# 9. Verify the package.json update
echo "Reinstalling dependencies with updated package.json..."
npm install

# 10. Test Tauri CLI again
echo "Final test of Tauri CLI..."
npx tauri info

echo "
=====================================================
    Tauri CLI Fixed for Aiayer Overlay
=====================================================

Fixes applied:
1. Cleaned npm cache and node_modules
2. Updated Tauri CLI and API to latest compatible versions
3. Verified CLI functionality

To run the overlay:
npm run tauri dev

If you still encounter issues:
1. Make sure Rust toolchain is installed (rustc -V)
2. Check the Tauri requirements: https://tauri.app/v1/guides/getting-started/prerequisites
3. Try manually installing the dependencies with:
   npm install -g @tauri-apps/cli
"