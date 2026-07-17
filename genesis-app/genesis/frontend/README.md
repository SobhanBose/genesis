# electron-app

A desktop Electron application built with React, Vite, Tailwind CSS, and Electron Builder.

## Overview

This frontend package is an Electron app scaffolded with `electron-vite`.
It contains:

- A main process entrypoint under `src/main`
- Preload scripts under `src/preload`
- A React renderer app under `src/renderer`
- Tailwind CSS for styling
- FontAwesome icons, animations, and routing support
- Build and packaging support via `electron-builder`

## Recommended IDE Setup

- Visual Studio Code
- ESLint extension
- Prettier extension
- Optional: TypeScript and JavaScript language support

## Requirements

- Node.js 18+ recommended
- npm 10+ or compatible package manager
- Windows, macOS, or Linux

## Project Structure

- `package.json` - scripts, dependencies, and build configuration
- `electron.vite.config.mjs` - electron-vite configuration for main, preload, and renderer
- `electron-builder.yml` - packaging configuration for Windows, macOS, and Linux
- `src/main` - application main process code
- `src/preload` - preload scripts for secure renderer communication
- `src/renderer` - React application source
- `resources/` - app resources included in packaged builds
- `build/` - build resources used by electron-builder

## Install

```bash
npm install
```

This installs runtime dependencies and executes `electron-builder install-app-deps` after installation to prepare any native dependencies used by Electron.

## Development

Start the app in development mode with live reload:

```bash
npm run dev
```

## Preview Built App

Build and preview the packaged app locally:

```bash
npm run start
```

## Build

Build the production app bundle:

```bash
npm run build
```

## Packaging

Build native packages for each platform:

```bash
npm run build:win
npm run build:mac
npm run build:linux
```

### Additional packaging options

```bash
npm run build:unpack
```

- `build:win` - Windows installer and packages via NSIS
- `build:mac` - macOS package
- `build:linux` - Linux package formats: AppImage, snap, deb
- `build:unpack` - build then output unpacked app directory

## Build Configuration

### electron.vite.config.mjs

- Uses `externalizeDepsPlugin()` for `main` and `preload`
- Uses `@vitejs/plugin-react` and `@tailwindcss/vite` for renderer
- Defines alias `@renderer` for `src/renderer/src`

### electron-builder.yml

- `appId`: `com.electron.app`
- `productName`: `electron-app`
- Build resources are sourced from `build/`
- `asarUnpack` includes `resources/**`
- Windows packaging uses NSIS with desktop shortcut creation
- macOS packaging includes entitlements inheritance and app metadata
- Linux packaging targets AppImage, snap, and deb
- Publish provider is configured as generic placeholder

## Key Dependencies

### Runtime dependencies

- `react` / `react-dom` - React UI framework
- `@electron-toolkit/preload`, `@electron-toolkit/utils` - Electron helper utilities
- `tailwindcss`, `@tailwindcss/vite` - styling
- `react-router`, `react-router-dom` - client-side routing
- `framer-motion`, `lottie-react` - animations
- `papaparse` - CSV parsing
- `ws` - WebSocket support

### Dev dependencies

- `electron` - Electron runtime
- `electron-builder` - native packaging tool
- `electron-vite` - Electron + Vite build tooling
- `vite` - frontend bundler
- `eslint`, `prettier`, and React lint plugins - code quality

## Code Quality

Run formatting and lint checks:

```bash
npm run format
npm run lint
```

## Notes

- Use `npm install` before running any script.
- `npm run dev` is the primary development workflow.
- For platform-specific artifacts, use the appropriate `build:*` script.
- Configure additional app metadata in `electron-builder.yml`.

## Useful paths

- `src/main` - Electron main process
- `src/preload` - Preload script
- `src/renderer/src` - React renderer code
- `electron.vite.config.mjs` - build config
- `electron-builder.yml` - packaging config
- `package.json` - scripts + dependencies
