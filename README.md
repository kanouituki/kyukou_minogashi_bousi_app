# Kyukou Minogashi Bousi App

This repository contains a Unity project built on the **GameCanvas** framework. The current implementation focuses on geolocation features that allow a user to record their position and measure the distance from that point.

## Overview

- The project imports GameCanvas packages and assets.
- `Assets/Game.cs` starts the geolocation service, stores coordinates with `gc.Save`, and displays the distance to the saved point.
- Earlier commits experimented with a class cancellation notification feature, but those scripts were removed when the GameCanvas template was introduced.

## Usage

1. Install Unity 2022.3.24f1 (or later) via UnityHub with the Android/iOS modules.
2. Clone this repository and open it with Unity.
3. Open the **Game** scene and press Play to run the sample.

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details. Third‑party notices are available in [NOTICE](NOTICE).
