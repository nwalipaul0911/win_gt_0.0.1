# **Win GT** – Productivity App with Distraction Lock & Smart Scheduling

Win GT is a **Windows-only productivity tool** designed to help you stay focused by **locking the keyboard for pre-selected distracting applications** and **optimizing your work periods** based on your Google Calendar events.

It combines distraction control with intelligent scheduling, ensuring your workflow adapts dynamically to upcoming tasks and meetings.

---

## **Features**

### 🔒 Distraction App Keyboard Lock

* Select applications that often cause distractions (e.g., games, social media, entertainment).
* When these apps are active, Win GT locks your keyboard input, preventing unproductive activity.
* Runs quietly in the background with minimal system impact.

### 📅 Google Calendar Integration

* Connects to your Google Calendar via the **Calendar API**.
* Fetches upcoming events automatically in real-time.
* Uses event data to adjust your productivity periods dynamically.

### ⏱ Live Period Ordering for Optimal Productivity

* Automatically **orders work periods** based on how soon scheduled events will occur.
* Dynamically re-prioritizes tasks when calendar updates happen.
* Ensures you focus on what matters most **before important events**.

---

## **How It Works**

1. **Select Your Distraction Apps**
   Choose programs that you want the system to monitor and block keyboard input for when they are in focus.

2. **Authorize Google Calendar Access**
   Log in to your Google account to grant permission for reading your calendar events.

3. **Dynamic Period Scheduling**
   The app monitors your calendar and reorders your work periods automatically as event times approach.

4. **Background Operation**
   Win GT works silently in the background, giving you focus without interruptions.

---

## **Installation**

### Requirements

* Windows 10 or later
* Python 3.9+
* Google API credentials (for Calendar access)

### Steps

1. Clone this repository:

   ```bash
   git clone https://github.com/<your-username>/win_gt.git
   cd win_gt
   ```
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
3. Set up your Google Calendar API credentials:

   * Create a Google Cloud project.
   * Enable the Calendar API.
   * Download `credentials.json` into the project root.
4. Run the app:

   ```bash
   python main.py
   ```

---

## **Configuration**

* **Distraction Apps**: Add application names to the configuration file (e.g., `config.json`).
* **Calendar Sync Interval**: Configure how often the app fetches new events.
* **Period Length**: Adjust productivity period durations.

---

## **Example Use Case**

* You have a meeting in **30 minutes**.
  Win GT detects the event from your calendar and **pushes all relevant prep tasks to the top of your period list**.
* You accidentally open **YouTube**.
  The app instantly **locks your keyboard** to prevent wasting time.

---

## **Roadmap**

* 📊 Productivity analytics and usage reports
* 🖱 Mouse lock for distraction apps
* 🔔 Smart notifications for upcoming periods and events

---

## **License**

This project is licensed under the MIT License.
