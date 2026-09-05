# Mobile app framework: React Native with the Expo toolchain

status: accepted
date: 2026-09-05

Repos: pyobs-core, pyobs-web-client, pyobs-app (planned)

## Context and Problem Statement

The smartphone/tablet client for pyobs (issue #884; design
`specs/design/mobile-app-and-shared-ts-client-core.md`) needs a cross-platform framework for
Android and iOS that pairs with the shared TypeScript core of ADR 0017, covers tablets, and does
not foreclose a future desktop consumer. Candidates evaluated: React Native (Expo), Flutter,
Qt 6/QML (extending `pyobs-polaris`), and a native dual stack.

## Considered Options

* **React Native with the Expo toolchain** (chosen): TypeScript throughout — the only candidate
  that *shares* the ADR 0017 core with the Vue/TS `pyobs-web-client` instead of porting it. Real
  native apps (native widgets, native WebSocket, APNs/FCM push, Keychain/Keystore), not a
  WebView/browser-shell. Expo provides the managed workflow: built-in WebSocket,
  `expo-notifications`, `expo-secure-store`, `expo prebuild` + config plugins, EAS for cloud
  builds and store submission; tablets (universal iOS incl. iPadOS multitasking; Android
  tablets) from the same codebase.
* **Flutter**: first-class Windows/macOS/Linux *and* Android/iOS from one codebase — the best
  desktop story of the candidates. But it speaks Dart, which forfeits the TS-core sharing that
  drives ADR 0017: the protocol layer would be re-implemented in Dart.
* **Qt 6/QML + QXmpp (extend `pyobs-polaris` to mobile)**: maximal reuse of Polaris's
  schema-driven client and C++ comm layer; proven on mobile (QXmpp/Qt on Android, cf. Kaidan);
  keeps native Linux desktop. Costs: Qt mobile toolchain and binary size, LGPL/GPL-vs-commercial
  licensing, and no TS sharing with the web client.
* **Native dual stack (Smack + XMPPFramework)**: two full codebases; rejected by the
  single-codebase requirement.

## Decision Outcome

The mobile app is built with **React Native using the Expo toolchain**. Bare React Native only if
a required native module cannot be accommodated by Expo — not anticipated for the pyobs protocol
layer (ADR 0016's WebSocket transport needs no native socket code).

## Why

- **Shared TypeScript is the decisive factor.** RN is the only candidate that consumes the
  ADR 0017 core rather than porting it — the app's protocol layer is the same code
  `pyobs-web-client` runs.
- Real native apps, with native WebSocket, real push, and Keychain/Keystore — and Expo removes
  the two-native-project maintenance burden.
- Tablet support (universal iOS app, Android tablets) comes from the same codebase; adaptive
  layout is a design concern, not a platform fork (design doc, Tablet scope).

## Consequences

- The app's protocol layer is the shared core from ADR 0017, pre-tested by the web client's
  suite.
- **Desktop ambitions are not satisfied by RN today**: react-native-windows/macos are out-of-tree
  native projects outside Expo's managed workflow, and there is no viable native Linux target. A
  hard *native Linux desktop* requirement (e.g. eventually replacing `pyobs-polaris`) would
  reopen this ADR — Flutter is the one-codebase alternative. The realistic desktop route is
  `pyobs-web-client` (already mobile+desktop responsive per its CLAUDE.md), optionally wrapped in
  Tauri/Electron; see the design doc's open questions.
- Expo/React Native inside a workspace monorepo requires Metro configuration
  (`watchFolders`/`nodeModulesPaths`) for the shared package; FITS rendering stays per-platform
  (canvas vs native/Skia).
- Layout is adaptive by window-size breakpoints (compact vs expanded, ~600 dp), not
  device-specific; tablets are in scope from the start.
