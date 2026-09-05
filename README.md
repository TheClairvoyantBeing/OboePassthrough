: OboePassthrough

Real‑Time Mic‑to‑Earphone Audio Passthrough on Android  
Built with Kotlin + C++ (Oboe) via JNI  
Features low‑latency stereo audio, simple noise‑gate filtering, and Start/Stop controls.

---

-> 🌟 Features

- Live microphone input → earphone output  
- Low latency using Oboe’s AAudio/OpenSL‑ES backend  
- Automatic stereo support (mono ↔ stereo)  
- Noise‑gate filter to suppress background hiss  
- Hardware volume buttons control playback level  
- Simple UI: Centered “Start” / “Stop” buttons  

---

-> 🛠️ Requirements

- Android Studio (2021.1 or later)  
- Android NDK (r21+), CMake & LLDB installed via SDK Manager  
- Min. Android API Level 23 (AAudio on API 27+, OpenSL fallback on 23–26)  
- A physical device (headphones recommended for best testing)  

---

-> 📂 Project Structure

app/
├── src/main/
│   ├── cpp/
│   │   ├── CMakeLists.txt
│   │   ├── native-lib.cpp
│   │   └── oboe/                ← Oboe submodule
│   ├── java/com/example/oboepassthrough/
│   │   └── MainActivity.kt
│   └── res/
│       └── layout/activity\_main.xml
├── build.gradle.kts            ← Module‑level
└── settings.gradle.kts

---

-> 🚀 Setup & Build

1. Clone this repo  

   git clone https://github.com/your‑username/OboePassthrough.git
   cd OboePassthrough/app/src/main/cpp

2. Fetch Oboe

   git clone https://github.com/google/oboe.git oboe
   
3. Open in Android Studio

   * File → Open… → select the top‑level "OboePassthrough" folder
   * Let Gradle sync

4. Verify CMakeLists.txt

   cmake_minimum_required(VERSION 3.10.2)
   project(OboePassthrough)

   add_subdirectory(oboe)

   add_library(native-lib SHARED native-lib.cpp)
   target_include_directories(native-lib PRIVATE oboe/include)
   target_link_libraries(native-lib oboe log)
   
5. Check "build.gradle.kts"

   android {
     defaultConfig {
       externalNativeBuild {
         cmake { cppFlags += "-std=c++17" }
       }
       ndk { abiFilters += listOf("armeabi-v7a","arm64-v8a") }
     }
     externalNativeBuild {
       cmake { path = file("src/main/cpp/CMakeLists.txt") }
     }
   }

6. Add microphone permission
   In "AndroidManifest.xml":

   <uses-permission android:name="android.permission.RECORD_AUDIO"/>

7. Clean & Rebuild

   * Build → Clean Project
   * Build → Rebuild Project

---

-> ▶️ Run & Test

1. Connect your Android device (headphones plugged in).
2. Run the app from Android Studio.
3. Grant microphone permission if prompted.
4. Tap Start Passthrough and speak into the mic.
5. You should hear your voice live through the earphones.
6. Tap Stop Passthrough to halt audio flow.

---

-> 🧩 How It Works

* Kotlin UI (`MainActivity.kt`) calls two JNI methods:

  * `startPassthrough()`
  * `stopPassthrough()`
* C++ layer (`native-lib.cpp`) uses Oboe to:

  1. Open an input stream (mic) and an output stream (earphones).
  2. In `onAudioReady()`, read microphone frames, apply a simple noise‑gate (`|sample| > threshold`), and write to the output buffer.
  3. Handle both mono and stereo channel counts automatically.

---

## Repository Standardization

This repository was standardized on 2026-09-05 under the ownership of [TheClairvoyantBeing](https://github.com/TheClairvoyantBeing).

### Changes applied

- Added a consistent `.gitignore` hygiene section covering IDE metadata (`.idea/`, `.vscode/`), Python caches, Node dependencies, build output, virtual environments, coverage output, `.env` files, and `reviews.md`.
- Ensured `requirements.txt` exists. Existing dependency declarations were preserved; repositories without detected Python dependencies contain a clearly marked placeholder.
- Standardized the repository license to the GNU Affero General Public License v3 (AGPLv3), with TheClairvoyantBeing as the copyright holder. AGPLv3 requires corresponding source to remain available when covered software is distributed or provided as a network service.
- This section records the repository-level maintenance changes; existing project-specific setup, usage, architecture, and development documentation remains above.
