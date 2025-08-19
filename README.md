# GazeTime 👁️⌨️

**GazeTime** is a productivity-focused, Windows-only CLI application that uses your webcam to detect whether you're looking at the screen. It blocks keystrokes in specific applications if you're distracted, encourages screen focus, and tracks your focus sessions.

---

## ⚙️ Features

* ✅ Real-time gaze detection using webcam
* ⏱️ Customizable focus session durations
* 🔔 Notifications before session ends
* 🚫 Blocks keyboard input in selected apps when you're not looking
* 📝 Logs completed sessions to a file (`session_log.txt`)
* 🪟 Designed for Windows desktop environments
* 💻 Runs via a lightweight command-line interface (CLI) with Administrative privileges

---

## 📸 Demo

> Coming soon.

---

## 🛠️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/nwalipaul0911/gazetime.git
cd gaze_lock
```

### 2. (Optional) Create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Usage

### Step 1: Configure `config.json`

Customize your session with:

```json
{
  "focus_apps": ["notepad.exe", "chrome.exe"],
  "session_duration": 1800,
  "warn_before": 60,
  "keyboard_lock": true
}
```

* `focus_apps`: List of Windows processes to monitor
* `session_duration`: Focus time in seconds (e.g., 1800 = 30 minutes)
* `warn_before`: When to notify before session ends (seconds)
* `keyboard_lock`: Whether to block input when you're not looking

### Step 2: Run the app

```bash
py main.py
```

You will be prompted after each session to either **continue (Y)** or **quit (N)**.

> 💡 Run from a terminal with **administrator privileges** for keyboard blocking to work properly.

---

## 📋 Requirements

* Windows OS
* Python 3.9+
* Webcam

---

## 📦 Dependencies

* `keyboard`
* `opencv-python`
* `plyer` (for notifications)
* `pywin32` (for detecting the active window)

All dependencies are listed in `requirements.txt`.

---

## 🧪 Example Log

After each completed session, a log entry is added to `session_log.txt`:

```
[2025-05-24 15:23:10] Focus session completed (duration: 1800 seconds)
```

---

## 🚧 Limitations

* Only tested on Windows
* Webcam must be enabled and uncovered
* Keyboard blocking may not work on system-protected apps
* No built-in UI (CLI only)

---

## 🤝 Contributing

This is a personal project, but contributions are welcome! Fork and submit a pull request.

---

## 📄 License

MIT License — see [LICENSE](https://github.com/nwalipaul0911/gaze_lock/blob/master/LICENSE) for details.

---

## 🙋‍♂️ Author

Built with focus 👁️⌨️ by **Nwali Paul**

