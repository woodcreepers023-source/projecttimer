import streamlit as st
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import requests
import json
from pathlib import Path

# ------------------- Config -------------------
MANILA = ZoneInfo("Asia/Manila")

DATA_FILE = Path("boss_timers.json")
HISTORY_FILE = Path("boss_history.json")

DISCORD_WEBHOOK_URL = st.secrets.get("DISCORD_WEBHOOK_URL", "")
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "1")

WARNING_WINDOW_SECONDS = 5 * 60  # 5 minutes

# ------------------- Discord -------------------
def send_discord_message(message: str) -> bool:
    if not DISCORD_WEBHOOK_URL:
        return False
    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json={"content": message}, timeout=10)
        return 200 <= r.status_code < 300
    except Exception:
        return False

# ------------------- Helpers -------------------
def format_timedelta(td: timedelta) -> str:
    total_seconds = int(td.total_seconds())
    if total_seconds < 0:
        return "00:00:00"
    days, rem = divmod(total_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    if days > 0:
        return f"{days}d {hours:02}:{minutes:02}:{seconds:02}"
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def now_manila() -> datetime:
    return datetime.now(tz=MANILA)

# ------------------- Default Boss Data -------------------
default_boss_data = [
    ("Venatus", 600, "2025-09-19 12:31 PM"),
    ("Viorent", 600, "2025-09-19 12:32 PM"),
    ("Ego", 1260, "2025-09-19 04:32 PM"),
    ("Livera", 1440, "2025-09-19 04:36 PM"),
    ("Undomiel", 1440, "2025-09-19 04:42 PM"),
    ("Araneo", 1440, "2025-09-19 04:33 PM"),
    ("Lady Dalia", 1080, "2025-09-19 05:58 AM"),
    ("General Aquleus", 1740, "2025-09-18 09:45 PM"),
    ("Amentis", 1740, "2025-09-18 09:42 PM"),
    ("Baron Braudmore", 1920, "2025-09-19 12:37 AM"),
    ("Wannitas", 2880, "2025-09-19 04:46 PM"),
    ("Metus", 2880, "2025-09-18 06:53 AM"),
    ("Duplican", 2880, "2025-09-19 04:40 PM"),
    ("Shuliar", 2100, "2025-09-19 03:49 AM"),
    ("Gareth", 1920, "2025-09-19 12:38 AM"),
    ("Titore", 2220, "2025-09-19 04:36 PM"),
    ("Larba", 2100, "2025-09-19 03:55 AM"),
    ("Catena", 2100, "2025-09-19 04:12 AM"),
    ("Secreta", 3720, "2025-09-17 05:15 PM"),
    ("Ordo", 3720, "2025-09-17 05:07 PM"),
    ("Asta", 3720, "2025-09-17 04:59 PM"),
    ("Supore", 3720, "2025-09-20 07:15 AM"),
]

# ------------------- JSON Persistence -------------------
def load_boss_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return default_boss_data.copy()

def save_boss_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ------------------- Edit History -------------------
def log_edit(boss_name: str, old_time: str, new_time: str):
    history = []
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)

    edited_by = st.session_state.get("username", "Unknown")
    entry = {
        "boss": boss_name,
        "old_time": old_time,
        "new_time": new_time,
        "edited_at": now_manila().strftime("%Y-%m-%d %I:%M %p"),
        "edited_by": edited_by,
    }
    history.append(entry)

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)

# ------------------- Timer Class -------------------
class TimerEntry:
    def __init__(self, name: str, interval_minutes: int, last_time_str: str):
        self.name = name
        self.interval_minutes = int(interval_minutes)
        self.interval_seconds = self.interval_minutes * 60
        self.last_time = datetime.strptime(last_time_str, "%Y-%m-%d %I:%M %p").replace(tzinfo=MANILA)
        self.next_time = self.last_time + timedelta(seconds=self.interval_seconds)

    def update_next(self):
        now = now_manila()
        while self.next_time < now:
            self.last_time = self.next_time
            self.next_time = self.last_time + timedelta(seconds=self.interval_seconds)

    def countdown(self) -> timedelta:
        return self.next_time - now_manila()

def build_timers():
    return [TimerEntry(*row) for row in load_boss_data()]

# ------------------- Weekly Boss Data -------------------
weekly_boss_data = [
    ("Clemantis", ["Monday 11:30", "Thursday 19:00"]),
    ("Saphirus", ["Sunday 17:00", "Tuesday 11:30"]),
    ("Neutro", ["Tuesday 19:00", "Thursday 11:30"]),
    ("Thymele", ["Monday 19:00", "Wednesday 11:30"]),
    ("Milavy", ["Saturday 15:00"]),
    ("Ringor", ["Saturday 17:00"]),
    ("Roderick", ["Friday 19:00"]),
    ("Auraq", ["Friday 22:00", "Wednesday 21:00"]),
    ("Chaiflock", ["Saturday 22:00"]),
    ("Benji", ["Sunday 21:00"]),
    ("Tumier", ["Sunday 19:00"]),
    ("Icaruthia (Kransia)", ["Tuesday 21:00", "Friday 21:00"]),
    ("Motti (Kransia)", ["Wednesday 19:00", "Saturday 19:00"]),
    ("Nevaeh (Kransia)", ["Sunday 22:00"]),
]

def get_next_weekly_spawn(day_time: str) -> datetime:
    now = now_manila()
    day_time = " ".join(day_time.split())
    day, time_str = day_time.split(" ", 1)
    target_time = datetime.strptime(time_str, "%H:%M").time()

    weekday_map = {
        "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
        "Friday": 4, "Saturday": 5, "Sunday": 6,
    }
    target_weekday = weekday_map[day]

    days_ahead = (target_weekday - now.weekday()) % 7
    spawn_date = (now + timedelta(days=days_ahead)).date()
    spawn_dt = datetime.combine(spawn_date, target_time).replace(tzinfo=MANILA)

    if spawn_dt <= now:
        spawn_dt += timedelta(days=7)
    return spawn_dt

# ------------------- Streamlit Setup -------------------
st.set_page_config(page_title="Lord9 Santiago 7 Boss Timer", layout="wide")
st.title("🛡️ Lord9 Santiago 7 Boss Timer")

# ------------------- Session defaults -------------------
st.session_state.setdefault("auth", False)
st.session_state.setdefault("username", "")
st.session_state.setdefault("page", "world")

def goto(page_name: str):
    st.session_state.page = page_name
    st.rerun()

# ------------------- Load timers -------------------
if "timers" not in st.session_state:
    st.session_state.timers = build_timers()
timers = st.session_state.timers

for t in timers:
    t.update_next()

# ------------------- WORLD PAGE -------------------
if st.session_state.page == "world":
    st.subheader("🗡️ Field Boss Spawns")
    for t in sorted(timers, key=lambda x: x.next_time):
        st.write(f"{t.name} — Next: {t.next_time.strftime('%Y-%m-%d %I:%M %p')}")

# ------------------- LOGIN PAGE -------------------
elif st.session_state.page == "login":
    st.subheader("🔐 Login")
    username_in = st.text_input("Name")
    password_in = st.text_input("Password", type="password")
    if st.button("Login"):
        if password_in == ADMIN_PASSWORD and username_in.strip():
            st.session_state.auth = True
            st.session_state.username = username_in.strip()
            goto("manage")
        else:
            st.error("Invalid login")

# ------------------- MANAGE PAGE -------------------
elif st.session_state.page == "manage":
    if not st.session_state.auth:
        st.warning("Login first")
    else:
        nav1, nav2, nav3, nav4, nav5 = st.columns(5)

        with nav1:
            if st.button("⏱️ Boss Tracker"):
                goto("world")
        with nav2:
            if st.button("💀 InstaKill"):
                goto("instakill")
        with nav3:
            if st.button("🛠️ Manage"):
                goto("manage")
        with nav4:
            if st.button("📜 History"):
                goto("history")
        with nav5:
            if st.button("🚪 Logout"):
                st.session_state.auth = False
                st.session_state.username = ""
                goto("world")

        st.subheader("Manage Page")

# ------------------- HISTORY PAGE -------------------
elif st.session_state.page == "history":
    if not st.session_state.auth:
        st.warning("Login first")
    else:
        nav1, nav2, nav3, nav4, nav5 = st.columns(5)

        with nav1:
            if st.button("⏱️ Boss Tracker"):
                goto("world")
        with nav2:
            if st.button("💀 InstaKill"):
                goto("instakill")
        with nav3:
            if st.button("🛠️ Manage"):
                goto("manage")
        with nav4:
            if st.button("📜 History"):
                goto("history")
        with nav5:
            if st.button("🚪 Logout"):
                st.session_state.auth = False
                st.session_state.username = ""
                goto("world")

        st.subheader("History Page")

# ------------------- INSTAKILL PAGE -------------------
elif st.session_state.page == "instakill":
    if not st.session_state.auth:
        st.warning("Login first")
    else:
        nav1, nav2, nav3, nav4, nav5 = st.columns(5)

        with nav1:
            if st.button("⏱️ Boss Tracker"):
                goto("world")
        with nav2:
            if st.button("💀 InstaKill"):
                goto("instakill")
        with nav3:
            if st.button("🛠️ Manage"):
                goto("manage")
        with nav4:
            if st.button("📜 History"):
                goto("history")
        with nav5:
            if st.button("🚪 Logout"):
                st.session_state.auth = False
                st.session_state.username = ""
                goto("world")

        st.subheader("💀 InstaKill Page")
