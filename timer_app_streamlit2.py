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

# ------------------- 5-minute warning logic -------------------
def _warn_key(source: str, boss_name: str, spawn_dt: datetime) -> str:
    return f"{source}|{boss_name}|{spawn_dt.strftime('%Y-%m-%d %H:%M')}"

def send_5min_warnings(field_timers):
    st.session_state.setdefault("warn_sent", {})
    now = now_manila()

    for t in field_timers:
        spawn_dt = t.next_time
        remaining = (spawn_dt - now).total_seconds()
        if 0 < remaining <= WARNING_WINDOW_SECONDS:
            key = _warn_key("FIELD", t.name, spawn_dt)
            if not st.session_state.warn_sent.get(key, False):
                msg = (
                    f"⏳ **5-minute warning!**\n"
                    f"**{t.name}** spawns at **{spawn_dt.strftime('%I:%M %p')}** (Manila)\n"
                    f"Time left: {format_timedelta(spawn_dt - now)}"
                )
                if send_discord_message(msg):
                    st.session_state.warn_sent[key] = True

    for boss, times in weekly_boss_data:
        for sched in times:
            spawn_dt = get_next_weekly_spawn(sched)
            remaining = (spawn_dt - now).total_seconds()
            if 0 < remaining <= WARNING_WINDOW_SECONDS:
                key = _warn_key("WEEKLY", boss, spawn_dt)
                if not st.session_state.warn_sent.get(key, False):
                    msg = (
                        f"⏳ **5-minute warning!**\n"
                        f"**{boss}** spawns at **{spawn_dt.strftime('%I:%M %p')}** (Manila)\n"
                        f"Time left: {format_timedelta(spawn_dt - now)}"
                    )
                    if send_discord_message(msg):
                        st.session_state.warn_sent[key] = True

    if len(st.session_state.warn_sent) > 600:
        st.session_state.warn_sent = dict(list(st.session_state.warn_sent.items())[-500:])

# ------------------- Banner -------------------
def next_boss_banner_combined(field_timers):
    if not field_timers:
        st.warning("No timers loaded.")
        return

    now = now_manila()
    field_next = min(field_timers, key=lambda x: x.next_time)
    field_cd = field_next.next_time - now

    weekly_best_name = None
    weekly_best_time = None
    weekly_best_cd = None
    for boss, times in weekly_boss_data:
        for sched in times:
            spawn_dt = get_next_weekly_spawn(sched)
            cd = spawn_dt - now
            if weekly_best_cd is None or cd < weekly_best_cd:
                weekly_best_cd = cd
                weekly_best_name = boss
                weekly_best_time = spawn_dt

    chosen_name = field_next.name
    chosen_time = field_next.next_time
    chosen_cd = field_cd
    if weekly_best_cd is not None and weekly_best_cd < field_cd:
        chosen_name = weekly_best_name
        chosen_time = weekly_best_time
        chosen_cd = weekly_best_cd

    remaining = chosen_cd.total_seconds()
    if remaining <= 60:
        cd_color = "red"
    elif remaining <= 300:
        cd_color = "orange"
    else:
        cd_color = "limegreen"

    time_only = chosen_time.strftime("%I:%M %p")
    cd_str = format_timedelta(chosen_cd)

    st.markdown(
        f"""
        <style>
        .banner-container {{
            display: flex;
            justify-content: center;
            margin: 20px 0 5px 0;
        }}
        .boss-banner {{
            background: linear-gradient(90deg, #0f172a, #1d4ed8, #16a34a);
            padding: 14px 28px;
            border-radius: 999px;
            box-shadow: 0 16px 40px rgba(15, 23, 42, 0.75);
            color: #f9fafb;
            display: inline-flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
        }}
        .boss-banner-title {{
            font-size: 28px;
            font-weight: 800;
            margin: 0;
            letter-spacing: 0.03em;
        }}
        .boss-banner-row {{
            display: flex;
            align-items: center;
            gap: 14px;
            font-size: 18px;
        }}
        .banner-chip {{
            padding: 4px 12px;
            border-radius: 999px;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(148, 163, 184, 0.7);
        }}
        </style>

        <div class="banner-container">
            <div class="boss-banner">
                <h2 class="boss-banner-title">
                    Next Boss: <strong>{chosen_name}</strong>
                </h2>
                <div class="boss-banner-row">
                    <span class="banner-chip">
                        🕒 <strong>{time_only}</strong>
                    </span>
                    <span class="banner-chip" style="color:{cd_color}; border-color:{cd_color};">
                        ⏳ <strong>{cd_str}</strong>
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ------------------- (All other functions like display_boss_table_sorted_newstyle, display_weekly_boss_table_newstyle remain unchanged) -------------------

# ------------------- Streamlit Setup -------------------
st.set_page_config(page_title="Lord9 Santiago 7 Boss Timer", layout="wide")
st.title("🛡️ Lord9 Santiago 7 Boss Timer")

# ------------------- GLOBAL UNIFORM BUTTON STYLE -------------------
st.markdown("""
<style>
/* Make ALL buttons uniform */
div.stButton > button{
    width: 100% !important;
    border-radius: 12px !important;
    border: 1px solid #cbd5e1 !important;
    background: #f1f5f9 !important;
    color: #0f172a !important;
    font-weight: 600 !important;
    padding: 0.6rem 0.85rem !important;
    box-shadow: none !important;
    transition: background-color .12s ease, transform .08s ease;
}
div.stButton > button:hover{
    background: #e2e8f0 !important;
}
div.stButton > button:active{
    transform: translateY(1px);
}
</style>
""", unsafe_allow_html=True)

# ------------------- Session defaults -------------------
st.session_state.setdefault("auth", False)
st.session_state.setdefault("username", "")
st.session_state.setdefault("page", "world")  # world | login | manage | history | instakill

def goto(page_name: str):
    st.session_state.page = page_name
    st.rerun()

# ------------------- Auto-refresh ONLY on World page -------------------
if st.session_state.page == "world":
    st_autorefresh(interval=1000, key="timer_refresh")

# ------------------- Load timers -------------------
if "timers" not in st.session_state:
    st.session_state.timers = build_timers()
timers = st.session_state.timers

for t in timers:
    t.update_next()

if st.session_state.page == "world":
    send_5min_warnings(timers)

# ------------------- WORLD PAGE HEADER -------------------
if st.session_state.page == "world":
    left_btn, mid_banner, right_space = st.columns([2, 6, 2])

    with left_btn:
        if not st.session_state.auth:
            if st.button("🔐 Admin Login"):
                goto("login")
        else:
            if st.button("🛠️ Manage / Edit"):
                goto("manage")

    with mid_banner:
        next_boss_banner_combined(timers)
else:
    next_boss_banner_combined(timers)

st.divider()

# ------------------- WORLD PAGE CONTENT -------------------
if st.session_state.page == "world":
    st.subheader("🗡️ Field Boss Spawns (Sorted by Next Spawn)")

    col1, col2 = st.columns([2, 1])
    with col1:
        display_boss_table_sorted_newstyle(timers)
    with col2:
        st.subheader("📅 Weekly Boss Spawns (Auto-Sorted)")
        display_weekly_boss_table_newstyle()

# ------------------- LOGIN PAGE -------------------
elif st.session_state.page == "login":
    st.subheader("🔐 Login (Edit Access)")
    st.caption("Auto-refresh is paused here so the page won’t fold while you type.")

    with st.form("login_form_page"):
        username_in = st.text_input("Name", key="login_username_page")
        password_in = st.text_input("Password", type="password", key="login_password_page")
        login_clicked = st.form_submit_button("Login", use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("⬅️ Back", use_container_width=True):
            goto("world")

    if login_clicked:
        if password_in == ADMIN_PASSWORD and username_in.strip():
            st.session_state.auth = True
            st.session_state.username = username_in.strip()
            st.success(f"✅ Access granted for {st.session_state.username}")
            goto("manage")
        else:
            st.error("❌ Invalid name or password.")

# ------------------- MANAGE PAGE -------------------
elif st.session_state.page == "manage":
    if not st.session_state.auth:
        st.warning("You must login first.")
        if st.button("Go to Login", use_container_width=True):
            goto("login")
    else:
        # ---------- TOP NAV UPDATED ----------
        top1, top2, top3, top4, top5 = st.columns([1.2, 1.2, 1.2, 1.2, 2.0])

        with top1:
            if st.button("⏱️ Boss Tracker", use_container_width=True):
                goto("world")
        with top2:
            if st.button("💀 InstaKill", use_container_width=True):
                goto("instakill")
        with top3:
            if st.button("🛠️ Manage", use_container_width=True):
                goto("manage")
        with top4:
            if st.button("📜 History
