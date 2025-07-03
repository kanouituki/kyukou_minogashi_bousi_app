# Kyukou Minogashi Bousi App

This repository contains a minimal set of Unity scripts that implement the core logic for a class cancellation notification app.

The app downloads cancellation information from a JSON API, stores it locally, and checks whether today's classes are canceled. If a cancellation is detected, the app monitors the user's location and sends a local notification when the user is more than 500 meters away from home.

## Directory Structure

- `Assets/Scripts/` - C# scripts used by the Unity project.
- `README.md` - This file.

## Getting Started

1. Create a new Unity project and copy the contents of this repository into the project directory.
2. Replace the `apiUrl` in `KyukouManager.cs` with your actual cancellation JSON API endpoint.
3. Add `KyukouManager` to a GameObject in your first scene so it runs on startup.
4. Build the project for Android or iOS. The scripts rely only on Unity standard APIs, so no extra packages are required.

## Notes

- The initial home location is saved on first launch using the device's current GPS position.
- Period strings (e.g., `2限`) are mapped to approximate start times in `GetClassTime`.
- Local notifications use platform-specific APIs through compiler directives.

