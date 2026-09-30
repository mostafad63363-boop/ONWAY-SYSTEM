import streamlit as st
import sqlite3
import pandas as pd
import json
import math
import hashlib
import hmac
import secrets
import io
import os
import re
import time
import zipfile
import html as htmllib
from contextlib import contextmanager
from datetime import datetime, date, timedelta
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Africa/Cairo")
except Exception:
    TZ = None

APP_NAME = "ONWAY Operations Cockpit"
DB_PATH = Path(os.environ.get("ONWAY_DB", "onway_delivery.db"))
NO_UI = os.environ.get("ONWAY_NO_UI") == "1"

st.set_page_config(page_title=APP_NAME, page_icon="🧡", layout="wide", initial_sidebar_state="collapsed")

# =========================================================
# الهوية البصرية
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&display=swap');
:root{
 --bg:#080A0D; --surface:#0F1217; --surface2:#141922; --text:#F6F7F9; --muted:#9AA4B2; --soft:#C8CED6; --line:#242B35;
 --brand:#FF5A00; --brand2:#FF7A33; --brandSoft:rgba(255,90,0,.13);
 --good:#00C27A; --goodSoft:rgba(0,194,122,.13); --warn:#FFB020; --warnSoft:rgba(255,176,32,.13);
 --danger:#FF4D4D; --dangerSoft:rgba(255,77,77,.13); --info:#4DA3FF; --infoSoft:rgba(77,163,255,.13);
 --shadow:0 12px 34px rgba(0,0,0,.24); --shadowBrand:0 12px 30px rgba(255,90,0,.18); --r:18px;
}
html,body,[class*="css"]{font-family:'Cairo',sans-serif!important;direction:rtl;text-align:right}
body{background:var(--bg)!important;color:var(--text)!important}
*,*:before,*:after{box-sizing:border-box}
[data-testid="stAppViewContainer"]{background:radial-gradient(circle at 15% 0%,rgba(255,90,0,.07),transparent 28%),linear-gradient(180deg,#080A0D 0%,#0A0D11 100%)!important}
[data-testid="stHeader"]{background:rgba(8,10,13,.70)!important;backdrop-filter:blur(12px)}
[data-testid="stDecoration"],#MainMenu,footer{display:none!important}
.block-container{max-width:1500px;padding:.65rem .8rem 5rem;margin:0 auto}
[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"]{display:none!important}
.app-topbar{display:flex;align-items:center;justify-content:space-between;gap:12px;background:rgba(15,18,23,.94);border:1px solid var(--line);border-radius:var(--r);padding:10px 12px;margin-bottom:11px;box-shadow:var(--shadow)}
.app-brand{display:flex;align-items:center;gap:10px;color:#fff;font-size:.98rem;font-weight:900}
.app-brand-mark{width:40px;height:40px;border-radius:13px;display:grid;place-items:center;background:var(--brand);color:#fff;box-shadow:var(--shadowBrand);font-size:1.12rem}
.user-chip{display:flex;align-items:center;gap:8px;background:#12161D;border:1px solid #2A313C;border-radius:999px;padding:6px 10px;color:var(--soft);font-size:.72rem;font-weight:800}
.user-dot{width:8px;height:8px;border-radius:50%;background:var(--good);box-shadow:0 0 0 4px rgba(0,194,122,.10)}
.onway-hero{background:linear-gradient(135deg,#11151B 0%,#0E1116 60%,#17110D 100%);border:1px solid var(--line);border-right:4px solid var(--brand);border-radius:var(--r);padding:16px 18px;margin-bottom:12px;box-shadow:var(--shadow)}
.onway-hero h1{margin:0;color:#fff;font-size:1.42rem;font-weight:900;line-height:1.2}
.onway-hero p{margin:.4rem 0 0;color:var(--muted);font-size:.76rem;line-height:1.7}
.metric-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:9px;margin-bottom:12px}
.metric{position:relative;overflow:hidden;background:linear-gradient(180deg,#11151B,#0E1116);border:1px solid var(--line);border-radius:15px;padding:13px 12px;box-shadow:var(--shadow);min-height:87px}
.metric:before{content:"";position:absolute;right:0;top:0;width:4px;height:100%;background:var(--brand)}
.metric.good:before{background:var(--good)}.metric.warn:before{background:var(--warn)}.metric.info:before{background:var(--info)}.metric.danger:before{background:var(--danger)}
.metric .v{font-size:1.28rem;font-weight:900;color:#fff;line-height:1.15}.metric .l{font-size:.68rem;font-weight:800;color:#D2D7DE;margin-top:5px}.metric .s{font-size:.58rem;color:var(--muted);margin-top:2px}
.card-title,.section-title{font-size:.92rem;font-weight:900;color:#fff;margin-bottom:4px}.card-sub,.section-sub{font-size:.66rem;color:var(--muted);line-height:1.65}
.status-pill{display:inline-flex;align-items:center;gap:4px;border-radius:999px;padding:.27rem .62rem;font-size:.63rem;font-weight:900}
.status-green{background:var(--goodSoft);color:#6DE8BA}.status-blue{background:var(--infoSoft);color:#8FC6FF}.status-amber{background:var(--warnSoft);color:#FFD06B}.status-red{background:var(--dangerSoft);color:#FF9E9E}.status-soft{background:#171C24;color:#C8CED6}
.stButton>button,.stDownloadButton>button,.stLinkButton>a{min-height:46px!important;border-radius:13px!important;border:1px solid #2A313C!important;font-weight:800!important;font-size:.81rem!important;background:#141922!important;color:#F6F7F9!important;box-shadow:none!important;transition:.14s ease!important}
.stButton>button:hover,.stDownloadButton>button:hover,.stLinkButton>a:hover{transform:translateY(-1px);border-color:#4A5564!important}
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"]{background:linear-gradient(180deg,var(--brand2),var(--brand))!important;color:#fff!important;border-color:var(--brand)!important;box-shadow:var(--shadowBrand)!important}
.stButton>button:disabled{background:#11151B!important;color:#677181!important;border-color:#202631!important}
[data-testid="stPopover"]>div>button,[data-testid="stPopoverButton"]{min-height:50px!important;border-radius:14px!important;font-weight:900!important;background:#141922!important;border:1px solid #333B48!important;color:#fff!important}
[data-testid="stPopoverBody"]{background:#0F1217!important;border:1px solid var(--line)!important;border-radius:16px!important;max-height:80vh;overflow:auto;min-width:min(340px,92vw)}
.stTextInput input,.stNumberInput input,.stTextArea textarea,.stDateInput input,.stTimeInput input{min-height:47px!important;border-radius:12px!important;border:1px solid #2A313C!important;background:#11151B!important;color:#F6F7F9!important;font-size:15px!important}
[data-baseweb="select"]>div{min-height:47px!important;border-radius:12px!important;border-color:#2A313C!important;background:#11151B!important;color:#F6F7F9!important}[data-baseweb="select"] *{color:#F6F7F9!important}
label{font-size:.71rem!important;font-weight:800!important;color:#CDD3DB!important}
[data-testid="stForm"]{border:1px solid var(--line)!important;border-radius:var(--r)!important;padding:12px!important;background:#0F1217!important}
[data-testid="stExpander"]{border:1px solid var(--line)!important;border-radius:14px!important;background:#0F1217!important;overflow:hidden}[data-testid="stExpander"] summary{color:#F6F7F9!important;font-weight:800!important}
.stAlert{border-radius:13px!important}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:13px;overflow:hidden}
.highlight{background:linear-gradient(135deg,rgba(255,90,0,.13),rgba(255,90,0,.03));border:1px solid rgba(255,90,0,.28);border-right:4px solid var(--brand);border-radius:14px;padding:12px;color:#fff;margin-bottom:10px}
.gps-panel{background:linear-gradient(135deg,rgba(0,194,122,.12),rgba(15,18,23,.95));border:1px solid rgba(0,194,122,.35);border-radius:15px;padding:11px 13px;margin-bottom:10px}
.gps-title{font-size:.88rem;font-weight:900;color:#70E7B7}.gps-sub{font-size:.65rem;color:#ADB6C2;line-height:1.75}
.cockpit-alert{padding:10px 12px;border-radius:13px;margin-bottom:7px;border:1px solid var(--line);background:#11151B}.cockpit-alert b{color:#fff}.cockpit-alert span{color:var(--muted);font-size:.66rem}
.rider-order{background:linear-gradient(160deg,#171B22,#0E1116);border:1px solid rgba(255,90,0,.35);border-radius:20px;padding:16px;margin-bottom:10px;box-shadow:var(--shadowBrand)}
.rider-order .no{font-size:1.15rem;font-weight:900;color:#fff}.rider-order .row{display:flex;gap:8px;align-items:flex-start;margin-top:9px;color:#DCE2E9;font-size:.82rem;line-height:1.7}
.rider-order .ico{width:30px;height:30px;border-radius:10px;display:grid;place-items:center;background:var(--brandSoft);flex:none}
.rider-order .earn{margin-top:11px;padding:8px 10px;border-radius:12px;background:var(--goodSoft);color:#6DE8BA;font-weight:900;font-size:.8rem;text-align:center}
.rider-action button{min-height:72px!important;font-size:1.08rem!important;border-radius:18px!important}
@media(max-width:1100px){.metric-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:700px){.block-container{padding:.35rem .42rem 4.8rem}.app-brand{font-size:.79rem}.app-brand-mark{width:34px;height:34px;border-radius:10px}.user-chip{font-size:.58rem;padding:5px 7px;max-width:47%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.onway-hero{padding:13px;border-radius:14px}.onway-hero h1{font-size:1.12rem}.onway-hero p{font-size:.64rem}.metric-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}.metric{min-height:76px;padding:9px}.metric .v{font-size:1.02rem}.metric .l{font-size:.59rem}.metric .s{font-size:.50rem}.stButton>button,.stDownloadButton>button,.stLinkButton>a{min-height:50px!important}.stTextInput input,.stNumberInput input,.stTextArea textarea,[data-baseweb="select"]>div{min-height:51px!important;font-size:16px!important}}
</style>
""", unsafe_allow_html=True)

if not hasattr(st, "fragment"):
    def _fragment_fallback(*args, **kwargs):
        if args and callable(args[0]):
            return args[0]
        return lambda f: f
    st.fragment = _fragment_fallback


# =========================================================
# الوقت — بتوقيت القاهرة دائماً (حتى لو السيرفر UTC)
# =========================================================
def now_dt():
    return datetime.now(TZ).replace(tzinfo=None) if TZ else datetime.now()


def today_d():
    return now_dt().date()


def now_iso(): return now_dt().strftime("%Y-%m-%d %H:%M:%S")
def today_str(): return today_d().isoformat()
def month_key(d=None): return (d or today_d()).strftime("%Y-%m")
def uid(prefix): return f"{prefix}-{now_dt().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
def parse_ts(raw): return datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
def esc(v): return htmllib.escape(str(v if v is not None else ""))
def app_name(): return get_setting("ui_brand", APP_NAME) or APP_NAME


def month_bounds(period):
    d = datetime.strptime(period, "%Y-%m").date()
    nxt = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
    return d.isoformat(), nxt.isoformat()


# =========================================================
# قاعدة البيانات
# =========================================================
SCHEMA = {
    "settings": ["key TEXT PRIMARY KEY", "value TEXT NOT NULL"],
    "users": ["id TEXT PRIMARY KEY", "name TEXT NOT NULL", "email TEXT UNIQUE NOT NULL", "role TEXT NOT NULL", "ref_id TEXT", "pin_hash TEXT NOT NULL", "active INTEGER NOT NULL DEFAULT 1", "created_at TEXT NOT NULL"],
    "restaurants": ["id TEXT PRIMARY KEY", "name TEXT NOT NULL", "phone TEXT", "billing_mode TEXT NOT NULL DEFAULT 'كاش'", "active INTEGER NOT NULL DEFAULT 1", "created_at TEXT NOT NULL"],
    "branches": ["id TEXT PRIMARY KEY", "restaurant_id TEXT NOT NULL", "name TEXT NOT NULL", "address TEXT", "lat REAL", "lng REAL", "active INTEGER NOT NULL DEFAULT 1", "created_at TEXT NOT NULL"],
    "riders": ["id TEXT PRIMARY KEY", "name TEXT NOT NULL", "phone TEXT", "salary REAL NOT NULL DEFAULT 6000", "status TEXT NOT NULL DEFAULT 'متاح'", "active_orders INTEGER NOT NULL DEFAULT 0", "last_lat REAL", "last_lng REAL", "gps_accuracy REAL", "heading REAL", "speed REAL", "last_gps_at TEXT", "created_at TEXT NOT NULL"],
    "orders": ["id TEXT PRIMARY KEY", "order_no TEXT UNIQUE NOT NULL", "restaurant_id TEXT NOT NULL", "branch_id TEXT NOT NULL", "delivery_address TEXT NOT NULL", "delivery_lat REAL", "delivery_lng REAL", "distance_km REAL NOT NULL DEFAULT 0", "eta_minutes INTEGER NOT NULL DEFAULT 0", "billing_mode TEXT NOT NULL", "rider_id TEXT", "status TEXT NOT NULL", "delivery_fee REAL NOT NULL DEFAULT 0", "rider_commission REAL NOT NULL DEFAULT 0", "reward REAL NOT NULL DEFAULT 0", "discount REAL NOT NULL DEFAULT 0", "cash_collected REAL NOT NULL DEFAULT 0", "notes TEXT", "created_by TEXT NOT NULL", "created_at TEXT NOT NULL", "accepted_at TEXT", "picked_up_at TEXT", "delivered_at TEXT", "cancelled_at TEXT"],
    "attendance": ["id TEXT PRIMARY KEY", "rider_id TEXT NOT NULL", "work_date TEXT NOT NULL", "clock_in TEXT", "clock_out TEXT", "break_minutes INTEGER NOT NULL DEFAULT 0", "status TEXT NOT NULL DEFAULT 'حاضر'", "reason TEXT", "created_at TEXT NOT NULL", "UNIQUE(rider_id, work_date)"],
    "ledger": ["id INTEGER PRIMARY KEY AUTOINCREMENT", "txn_no TEXT UNIQUE NOT NULL", "txn_type TEXT NOT NULL", "account_type TEXT NOT NULL", "account_id TEXT", "amount REAL NOT NULL", "direction TEXT NOT NULL", "reference_id TEXT", "description TEXT", "created_by TEXT NOT NULL", "created_at TEXT NOT NULL"],
    "settlements": ["id TEXT PRIMARY KEY", "kind TEXT NOT NULL", "party_id TEXT NOT NULL", "period_start TEXT NOT NULL", "period_end TEXT NOT NULL", "gross REAL NOT NULL DEFAULT 0", "commissions REAL NOT NULL DEFAULT 0", "rewards REAL NOT NULL DEFAULT 0", "discounts REAL NOT NULL DEFAULT 0", "cash_due REAL NOT NULL DEFAULT 0", "paid REAL NOT NULL DEFAULT 0", "created_by TEXT NOT NULL", "created_at TEXT NOT NULL"],
    "settlement_items": ["id TEXT PRIMARY KEY", "settlement_id TEXT NOT NULL", "order_id TEXT NOT NULL", "amount REAL NOT NULL"],
    "gps_log": ["id INTEGER PRIMARY KEY AUTOINCREMENT", "rider_id TEXT NOT NULL", "lat REAL NOT NULL", "lng REAL NOT NULL", "accuracy REAL", "heading REAL", "speed REAL", "recorded_at TEXT NOT NULL"],
    "audit_log": ["id INTEGER PRIMARY KEY AUTOINCREMENT", "actor_id TEXT", "action TEXT NOT NULL", "entity TEXT NOT NULL", "entity_id TEXT", "before_json TEXT", "after_json TEXT", "created_at TEXT NOT NULL"],
    "payroll_adjustments": ["id TEXT PRIMARY KEY", "rider_id TEXT NOT NULL", "period TEXT NOT NULL", "type TEXT NOT NULL", "amount REAL NOT NULL", "description TEXT", "created_by TEXT NOT NULL", "created_at TEXT NOT NULL"],
    "payroll_payments": ["id TEXT PRIMARY KEY", "rider_id TEXT NOT NULL", "period TEXT NOT NULL", "amount REAL NOT NULL", "method TEXT NOT NULL", "reference TEXT", "notes TEXT", "paid_at TEXT NOT NULL", "created_by TEXT NOT NULL"],
    "sessions": ["token_hash TEXT PRIMARY KEY", "user_id TEXT NOT NULL", "created_at TEXT NOT NULL", "expires_at TEXT NOT NULL"],
    "ai_commands": ["id INTEGER PRIMARY KEY AUTOINCREMENT", "actor_id TEXT", "command TEXT", "plan_json TEXT", "result TEXT", "created_at TEXT NOT NULL"],
}

DEFAULTS = {
    "salary_basic": "6000", "working_days": "26", "excused_leave_days": "1", "unexcused_leave_days": "1.25",
    "daily_work_hours": "8", "commission_base_km": "3", "commission_base": "10", "commission_extra_per_km": "5",
    "gps_fresh_seconds": "30", "order_overdue_grace_minutes": "15",
    "fee_base": "30", "fee_base_km": "3", "fee_extra_km": "5", "cash_limit": "1500",
}

# أنظمة قبض الطيار
PAY_MODES = {
    "MONTHLY": "راتب شهري + عمولة حسب المسافة",
    "DISTANCE": "عمولة حسب المسافة فقط (بدون راتب)",
    "COMPANY_CUT": "حصة ثابتة للشركة على كل أوردر (الطيار يأخذ الباقي)",
}


@contextmanager
def get_conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=5000")
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


def ensure_column(table, column, col_type):
    with get_conn() as c:
        cols = [r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()]
        if column not in cols:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")


def setup_db():
    with get_conn() as c:
        for table, cols in SCHEMA.items():
            c.execute(f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(cols)})")
        for k, v in DEFAULTS.items():
            c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES (?,?)", (k, v))
        c.execute("DROP INDEX IF EXISTS uq_settlement_order")
    for t, col, typ in [
        ("attendance", "break_minutes", "INTEGER NOT NULL DEFAULT 0"),
        ("riders", "pay_mode", "TEXT NOT NULL DEFAULT 'MONTHLY'"),
        ("riders", "comm_base_km", "REAL"), ("riders", "comm_base", "REAL"),
        ("riders", "comm_extra_km", "REAL"), ("riders", "company_cut", "REAL"),
        ("orders", "customer_phone", "TEXT"), ("orders", "track_token", "TEXT"), ("orders", "customer_name", "TEXT"), ("orders", "comm_settled", "INTEGER NOT NULL DEFAULT 0"), ("orders", "comm_settlement_id", "TEXT"),
        ("settlements", "voided", "INTEGER NOT NULL DEFAULT 0"),
    ]:
        ensure_column(t, col, typ)
    with get_conn() as c:
        if (c.execute("SELECT value FROM settings WHERE key='legacy_ledger_reclass_done'").fetchone() or ["0"])[0] != "1":
            c.execute("UPDATE ledger SET direction='استحقاق' WHERE txn_type='إيراد خدمة توصيل' AND direction='داخل'")
            c.execute("INSERT INTO settings(key,value) VALUES ('legacy_ledger_reclass_done','1') ON CONFLICT(key) DO UPDATE SET value='1'")
        c.execute("DELETE FROM gps_log WHERE recorded_at<?", ((now_dt() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S"),))
        c.execute("DELETE FROM sessions WHERE expires_at<?", (now_iso(),))
        if (c.execute("SELECT value FROM settings WHERE key='comm_unify_done'").fetchone() or ["0"])[0] != "1":
            c.execute("""UPDATE orders SET comm_settled=1, comm_settlement_id=(SELECT si.settlement_id FROM settlement_items si JOIN settlements s ON s.id=si.settlement_id
                         WHERE si.order_id=orders.id AND s.kind IN ('طيار_كاش','تصحيح_طيار') AND COALESCE(s.voided,0)=0 ORDER BY (s.kind='طيار_كاش') DESC LIMIT 1)
                         WHERE id IN (SELECT si.order_id FROM settlement_items si JOIN settlements s ON s.id=si.settlement_id WHERE s.kind IN ('طيار_كاش','تصحيح_طيار') AND COALESCE(s.voided,0)=0)""")
            c.execute("INSERT INTO settings(key,value) VALUES ('comm_unify_done','1') ON CONFLICT(key) DO UPDATE SET value='1'")
        for (oid,) in c.execute("SELECT id FROM orders WHERE track_token IS NULL").fetchall():
            c.execute("UPDATE orders SET track_token=? WHERE id=?", (secrets.token_urlsafe(8), oid))
    auto_backup()


def get_setting(key, default=None):
    with get_conn() as c:
        r = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return r[0] if r else default


def set_setting(key, value):
    with get_conn() as c:
        c.execute("INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))


def df(sql, params=()):
    with get_conn() as c:
        return pd.read_sql_query(sql, c, params=params)


def one(sql, params=()):
    with get_conn() as c:
        r = c.execute(sql, params).fetchone()
    return dict(r) if r else None


def audit(actor_id, action, entity, entity_id=None, before=None, after=None):
    with get_conn() as c:
        c.execute("INSERT INTO audit_log(actor_id,action,entity,entity_id,before_json,after_json,created_at) VALUES (?,?,?,?,?,?,?)",
                  (actor_id, action, entity, entity_id,
                   json.dumps(before, ensure_ascii=False, default=str) if before is not None else None,
                   json.dumps(after, ensure_ascii=False, default=str) if after is not None else None, now_iso()))


def hash_pin(pin, salt=None):
    salt = salt or secrets.token_hex(16)
    return f"{salt}${hashlib.pbkdf2_hmac('sha256', pin.encode(), salt.encode(), 180_000).hex()}"


def verify_pin(pin, stored):
    try:
        salt, digest = stored.split("$", 1)
        return hmac.compare_digest(hashlib.pbkdf2_hmac("sha256", pin.encode(), salt.encode(), 180_000).hex(), digest)
    except Exception:
        return False


# ---------- جلسات الجهاز (تسجيل دخول محفوظ) ----------
def create_session(user_id, days=90):
    token = secrets.token_urlsafe(32)
    h = hashlib.sha256(token.encode()).hexdigest()
    with get_conn() as c:
        c.execute("INSERT INTO sessions(token_hash,user_id,created_at,expires_at) VALUES (?,?,?,?)",
                  (h, user_id, now_iso(), (now_dt() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")))
    return token


def user_from_token(token):
    if not token:
        return None
    h = hashlib.sha256(str(token).encode()).hexdigest()
    return one("SELECT u.id,u.name,u.email,u.role,u.ref_id FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>? AND u.active=1", (h, now_iso()))


def drop_session(token):
    if token:
        with get_conn() as c:
            c.execute("DELETE FROM sessions WHERE token_hash=?", (hashlib.sha256(str(token).encode()).hexdigest(),))


def drop_user_sessions(user_id):
    with get_conn() as c:
        c.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))


# ---------- عمولات الطيار حسب نظام القبض ----------
def _num(v, default=None):
    try:
        if v is None:
            return default
        f = float(v)
        return default if math.isnan(f) else f
    except Exception:
        return default


def rider_row(rid):
    return one("SELECT * FROM riders WHERE id=?", (rid,)) if rid else None


def rider_terms(rider):
    r = dict(rider) if rider is not None else {}
    mode = r.get("pay_mode") if r.get("pay_mode") in PAY_MODES else "MONTHLY"
    return {
        "mode": mode,
        "base_km": _num(r.get("comm_base_km"), _num(get_setting("commission_base_km", 3), 3.0)),
        "base": _num(r.get("comm_base"), _num(get_setting("commission_base", 10), 10.0)),
        "extra": _num(r.get("comm_extra_km"), _num(get_setting("commission_extra_per_km", 5), 5.0)),
        "cut": _num(r.get("company_cut"), 0.0),
    }


def commission_for_order(distance, fee, rider=None):
    t = rider_terms(rider)
    if t["mode"] == "COMPANY_CUT":
        return round(max(0.0, float(fee or 0) - t["cut"]), 2)
    d = max(0.0, float(distance or 0))
    return round(t["base"] if d <= t["base_km"] else t["base"] + (d - t["base_km"]) * t["extra"], 2)


def haversine_km(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2) or any(_num(x) is None for x in (lat1, lon1, lat2, lon2)):
        return 9999.0
    r = 6371.0
    p1 = math.radians(float(lat1)); p2 = math.radians(float(lat2))
    dp = math.radians(float(lat2) - float(lat1)); dl = math.radians(float(lon2) - float(lon1))
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def gps_fresh(rider):
    raw = rider.get("last_gps_at") if isinstance(rider, dict) else None
    if not isinstance(raw, str) or not raw:
        return False
    try:
        return (now_dt() - parse_ts(raw)).total_seconds() <= float(get_setting("gps_fresh_seconds", 30))
    except Exception:
        return False


def status_class(status):
    if status == "تم التسليم": return "status-green"
    if status == "ملغى": return "status-red"
    if status in ("تم التعيين", "تم القبول", "تم الاستلام", "في الطريق"): return "status-blue"
    return "status-amber"


def badge(text, kind=None):
    if kind is None:
        kind = status_class(text).replace("status-", "")
    cls = {"green": "status-green", "blue": "status-blue", "amber": "status-amber", "red": "status-red", "soft": "status-soft"}.get(kind, "status-soft")
    return f'<span class="status-pill {cls}">{esc(text)}</span>'


def role_label(role):
    return {"OWNER": "المالك", "DISPATCHER": "الديسباتشر", "ACCOUNTANT": "الحسابات", "RIDER": "الطيار", "RESTAURANT": "المطعم"}.get(role, role or "مستخدم")


def transitions(status):
    return {"جديد": ["تم التعيين", "ملغى"], "تم التعيين": ["تم القبول", "ملغى"], "تم القبول": ["تم الاستلام", "ملغى"],
            "تم الاستلام": ["في الطريق"], "في الطريق": ["تم التسليم"], "تم التسليم": [], "ملغى": []}.get(status, [])


def order_active(status): return status not in ("تم التسليم", "ملغى")


def available_riders(): return df("SELECT * FROM riders WHERE status!='غير نشط' ORDER BY active_orders,name")
def all_restaurants(): return df("SELECT * FROM restaurants ORDER BY name")
def active_restaurants(): return df("SELECT * FROM restaurants WHERE active=1 ORDER BY name")


def branches_for(rid, active_only=True):
    q = "SELECT * FROM branches WHERE restaurant_id=?" + (" AND active=1" if active_only else "") + " ORDER BY name"
    return df(q, (rid,))


def ranked_riders(pickup_lat=None, pickup_lng=None):
    r = available_riders()
    if r.empty:
        return r
    scores = []
    fresh_s = float(get_setting("gps_fresh_seconds", 30))
    for _, row in r.iterrows():
        age = 9999
        raw = row.get("last_gps_at")
        if isinstance(raw, str) and raw:
            try: age = max(0, (now_dt() - parse_ts(raw)).total_seconds())
            except Exception: pass
        dist = haversine_km(row.get("last_lat"), row.get("last_lng"), pickup_lat, pickup_lng)
        scores.append(float(row.get("active_orders") or 0) * 12 + min(dist, 20) * 2 + (10 if age > fresh_s else age / 60))
    r = r.copy(); r["score"] = scores
    return r.sort_values(["score", "active_orders", "name"]).reset_index(drop=True)


def actor_is_owner(actor):
    if not actor:
        return False
    if actor.get("role") == "OWNER":
        return True
    base = st.session_state.get("user") or {}
    return base.get("role") == "OWNER" and base.get("id") == actor.get("id")


def need_owner(actor, msg):
    if not actor_is_owner(actor):
        raise PermissionError(msg)


# =========================================================
# CRUD
# =========================================================
def create_restaurant(data, actor):
    need_owner(actor, "إضافة المطاعم صلاحية المالك فقط.")
    if not data.get("name", "").strip(): raise ValueError("اسم المطعم مطلوب.")
    rid = uid("RST")
    with get_conn() as c:
        c.execute("INSERT INTO restaurants(id,name,phone,billing_mode,active,created_at) VALUES (?,?,?,?,1,?)", (rid, data["name"].strip(), data.get("phone", "").strip(), data.get("billing_mode", "كاش"), now_iso()))
    audit(actor["id"], "create", "restaurant", rid, after=data | {"id": rid}); return rid


def create_branch(data, actor):
    need_owner(actor, "إضافة الفروع صلاحية المالك فقط.")
    if not data.get("name", "").strip(): raise ValueError("اسم الفرع مطلوب.")
    if data.get("lat") is None or data.get("lng") is None: raise ValueError("اختَر موقع الفرع على الخريطة أولاً.")
    bid = uid("BRN")
    with get_conn() as c:
        c.execute("INSERT INTO branches(id,restaurant_id,name,address,lat,lng,active,created_at) VALUES (?,?,?,?,?,?,1,?)", (bid, data["restaurant_id"], data["name"].strip(), data.get("address", "").strip(), float(data["lat"]), float(data["lng"]), now_iso()))
    audit(actor["id"], "create", "branch", bid, after=data | {"id": bid}); return bid


def _pay_fields(data):
    mode = data.get("pay_mode", "MONTHLY")
    if mode not in PAY_MODES: raise ValueError("نظام القبض غير صحيح.")
    if mode == "COMPANY_CUT" and _num(data.get("company_cut")) is None: raise ValueError("حدد حصة الشركة الثابتة لكل أوردر.")
    return mode, _num(data.get("comm_base_km")), _num(data.get("comm_base")), _num(data.get("comm_extra_km")), _num(data.get("company_cut"))


def recompute_active_commissions(rider_id):
    rider = rider_row(rider_id)
    with get_conn() as c:
        for o in c.execute("SELECT id,distance_km,delivery_fee FROM orders WHERE rider_id=? AND status NOT IN ('تم التسليم','ملغى')", (rider_id,)).fetchall():
            c.execute("UPDATE orders SET rider_commission=? WHERE id=?", (commission_for_order(o["distance_km"], o["delivery_fee"], rider), o["id"]))


def create_rider(data, actor):
    need_owner(actor, "إضافة الطيارين صلاحية المالك فقط.")
    if not data.get("name", "").strip(): raise ValueError("اسم الطيار مطلوب.")
    mode, bk, b, ex, cut = _pay_fields(data)
    rid = uid("RYD")
    with get_conn() as c:
        c.execute("INSERT INTO riders(id,name,phone,salary,status,created_at,pay_mode,comm_base_km,comm_base,comm_extra_km,company_cut) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                  (rid, data["name"].strip(), data.get("phone", "").strip(), float(_num(data.get("salary"), _num(get_setting("salary_basic", 6000), 6000.0))), "متاح", now_iso(), mode, bk, b, ex, cut))
    audit(actor["id"], "create", "rider", rid, after=data | {"id": rid}); return rid


def update_rider(rider_id, data, actor):
    need_owner(actor, "تعديل بيانات الطيارين صلاحية المالك فقط.")
    old = rider_row(rider_id)
    if not old: raise ValueError("الطيار غير موجود.")
    mode, bk, b, ex, cut = _pay_fields(data)
    with get_conn() as c:
        c.execute("UPDATE riders SET phone=?,salary=?,pay_mode=?,comm_base_km=?,comm_base=?,comm_extra_km=?,company_cut=? WHERE id=?",
                  (data.get("phone", "").strip(), float(data.get("salary") or 0), mode, bk, b, ex, cut, rider_id))
    recompute_active_commissions(rider_id)
    audit(actor["id"], "update", "rider", rider_id, before=old, after=rider_row(rider_id))


def create_user(data, actor):
    need_owner(actor, "إدارة المستخدمين صلاحية المالك فقط.")
    email = data.get("email", "").strip().lower(); pin = data.get("pin", "").strip()
    if not data.get("name", "").strip() or "@" not in email or not pin.isdigit() or len(pin) < 4:
        raise ValueError("الاسم والبريد وPIN (4 إلى 8 أرقام) مطلوبة.")
    if data["role"] in ("RIDER", "RESTAURANT") and not data.get("ref_id"): raise ValueError("اربط الحساب بالطيار/المطعم.")
    if one("SELECT 1 FROM users WHERE lower(email)=?", (email,)): raise ValueError("البريد مستخدم بالفعل.")
    u = uid("USR")
    with get_conn() as c:
        c.execute("INSERT INTO users(id,name,email,role,ref_id,pin_hash,active,created_at) VALUES (?,?,?,?,?,?,1,?)", (u, data["name"].strip(), email, data["role"], data.get("ref_id"), hash_pin(pin), now_iso()))
    audit(actor["id"], "create", "user", u, after={k: v for k, v in data.items() if k != "pin"} | {"id": u}); return u


def update_user(user_id, data, actor):
    need_owner(actor, "إدارة المستخدمين صلاحية المالك فقط.")
    old = one("SELECT * FROM users WHERE id=?", (user_id,))
    if not old: raise ValueError("المستخدم غير موجود.")
    email = data.get("email", "").strip().lower()
    if not data.get("name", "").strip() or "@" not in email: raise ValueError("الاسم والبريد مطلوبان.")
    if one("SELECT 1 FROM users WHERE lower(email)=? AND id!=?", (email, user_id)): raise ValueError("البريد مستخدم بالفعل.")
    role = data["role"]
    if old["role"] == "OWNER" and role != "OWNER": raise ValueError("لا يمكن تغيير دور المالك.")
    if role in ("RIDER", "RESTAURANT") and not data.get("ref_id"): raise ValueError("اربط الحساب بالطيار/المطعم.")
    pin = (data.get("pin") or "").strip()
    if pin and (not pin.isdigit() or len(pin) < 4): raise ValueError("PIN يجب أن يكون 4 إلى 8 أرقام.")
    with get_conn() as c:
        c.execute("UPDATE users SET name=?,email=?,role=?,ref_id=? WHERE id=?", (data["name"].strip(), email, role, data.get("ref_id"), user_id))
        if pin: c.execute("UPDATE users SET pin_hash=? WHERE id=?", (hash_pin(pin), user_id))
    if pin or role != old["role"] or data.get("ref_id") != old.get("ref_id"): drop_user_sessions(user_id)
    audit(actor["id"], "update", "user", user_id, before={k: v for k, v in old.items() if k != "pin_hash"}, after={"name": data["name"], "email": email, "role": role, "ref_id": data.get("ref_id"), "pin_changed": bool(pin)})


def update_restaurant(rid, phone, billing_mode, actor):
    need_owner(actor, "تعديل المطاعم صلاحية المالك فقط.")
    old = one("SELECT * FROM restaurants WHERE id=?", (rid,))
    with get_conn() as c: c.execute("UPDATE restaurants SET phone=?,billing_mode=? WHERE id=?", (phone.strip(), billing_mode, rid))
    audit(actor["id"], "update", "restaurant", rid, before=old, after=one("SELECT * FROM restaurants WHERE id=?", (rid,)))


def set_active(entity, entity_id, active, actor):
    need_owner(actor, "هذه الصلاحية للمالك فقط.")
    table = {"rider": "riders", "restaurant": "restaurants", "branch": "branches", "user": "users"}.get(entity)
    if not table: raise ValueError("نوع السجل غير معروف.")
    old = one(f"SELECT * FROM {table} WHERE id=?", (entity_id,))
    if not old: raise ValueError("السجل غير موجود.")
    if not active:
        if entity == "rider" and int(old.get("active_orders") or 0) > 0: raise ValueError("لا يمكن تعطيل طيار لديه طلبات نشطة.")
        if entity == "restaurant" and one("SELECT 1 FROM orders WHERE restaurant_id=? AND status NOT IN ('تم التسليم','ملغى')", (entity_id,)): raise ValueError("لا يمكن تعطيل مطعم لديه طلبات نشطة.")
        if entity == "branch" and one("SELECT 1 FROM orders WHERE branch_id=? AND status NOT IN ('تم التسليم','ملغى')", (entity_id,)): raise ValueError("لا يمكن تعطيل فرع لديه طلبات نشطة.")
    with get_conn() as c:
        if entity == "rider": c.execute("UPDATE riders SET status=? WHERE id=?", ("متاح" if active else "غير نشط", entity_id))
        else: c.execute(f"UPDATE {table} SET active=? WHERE id=?", (1 if active else 0, entity_id))
    if entity == "user" and not active: drop_user_sessions(entity_id)
    audit(actor["id"], "activate" if active else "deactivate", entity, entity_id, before=old, after=one(f"SELECT * FROM {table} WHERE id=?", (entity_id,)))


def reset_user_pin(user_id, actor):
    need_owner(actor, "إعادة تعيين PIN صلاحية المالك فقط.")
    if not one("SELECT 1 FROM users WHERE id=?", (user_id,)): raise ValueError("المستخدم غير موجود.")
    pin = ''.join(secrets.choice('0123456789') for _ in range(6))
    with get_conn() as c: c.execute("UPDATE users SET pin_hash=? WHERE id=?", (hash_pin(pin), user_id))
    drop_user_sessions(user_id)
    audit(actor["id"], "reset_pin", "user", user_id, after={"pin_reset": True}); return pin


def validate_pin_value(pin, label="PIN"):
    pin = str(pin or "").strip()
    if not pin.isdigit() or not 4 <= len(pin) <= 8:
        raise ValueError(f"{label} يجب أن يكون من 4 إلى 8 أرقام.")
    return pin


def change_own_pin(current_pin, new_pin, actor):
    """تغيير PIN للمستخدم نفسه بعد التحقق من PIN الحالي. لا تكشف القيمة المخزنة."""
    if not actor or not actor.get("id"):
        raise PermissionError("لا يوجد مستخدم مسجل حالياً.")
    current_pin = validate_pin_value(current_pin, "PIN الحالي")
    new_pin = validate_pin_value(new_pin, "PIN الجديد")
    if current_pin == new_pin:
        raise ValueError("PIN الجديد يجب أن يختلف عن PIN الحالي.")
    u = one("SELECT * FROM users WHERE id=? AND active=1", (actor["id"],))
    if not u:
        raise ValueError("الحساب غير موجود أو غير نشط.")
    if not verify_pin(current_pin, u["pin_hash"]):
        raise ValueError("PIN الحالي غير صحيح.")
    with get_conn() as c:
        c.execute("UPDATE users SET pin_hash=? WHERE id=?", (hash_pin(new_pin), actor["id"]))
    # أبقِ جلسة هذا الجهاز فعالة؛ يتم إبطال الجلسات الأخرى فقط.
    with get_conn() as c:
        token = st.session_state.get("_token")
        if token:
            h = hashlib.sha256(str(token).encode()).hexdigest()
            c.execute("DELETE FROM sessions WHERE user_id=? AND token_hash!=?", (actor["id"], h))
        else:
            c.execute("DELETE FROM sessions WHERE user_id=?", (actor["id"],))
    audit(actor["id"], "change_own_pin", "user", actor["id"], after={"pin_changed": True})
    return True


def owner_set_user_pin(user_id, new_pin, actor):
    """تعيين PIN محدد لمستخدم بواسطة المالك فقط."""
    need_owner(actor, "تعيين PIN لمستخدم آخر صلاحية المالك فقط.")
    new_pin = validate_pin_value(new_pin, "PIN الجديد")
    u = one("SELECT id,name,role,active FROM users WHERE id=?", (user_id,))
    if not u:
        raise ValueError("المستخدم غير موجود.")
    if u["id"] == actor.get("id"):
        raise ValueError("استخدم تغيير PIN الخاص بك بدلاً من تعيين PIN لنفس الحساب.")
    with get_conn() as c:
        c.execute("UPDATE users SET pin_hash=? WHERE id=?", (hash_pin(new_pin), user_id))
    drop_user_sessions(user_id)
    audit(actor["id"], "set_pin", "user", user_id, after={"pin_set": True})
    return True


# =========================================================
# الطلبات
# =========================================================
def next_order_no():
    n = one("SELECT COUNT(*) n FROM orders WHERE substr(created_at,1,10)=?", (today_str(),))["n"] + 1
    while True:
        no = f"ON-{today_d().strftime('%y%m%d')}-{n:03d}"
        if not one("SELECT 1 FROM orders WHERE order_no=?", (no,)): return no
        n += 1


def create_order(data, actor):
    if not actor_is_owner(actor) and actor.get("role") != "DISPATCHER": raise PermissionError("إنشاء الطلبات صلاحية المالك أو الديسباتشر فقط.")
    if not str(data.get("order_no", "")).strip(): raise ValueError("رقم الطلب مطلوب.")
    if not str(data.get("delivery_address", "")).strip(): raise ValueError("عنوان التسليم مطلوب.")
    if data.get("delivery_lat") is None or data.get("delivery_lng") is None: raise ValueError("اختَر موقع التسليم على الخريطة قبل إنشاء الطلب.")
    oid = uid("ORD")
    with get_conn() as c:
        if c.execute("SELECT 1 FROM orders WHERE order_no=?", (data["order_no"].strip(),)).fetchone(): raise ValueError("رقم الطلب موجود بالفعل.")
        if not c.execute("SELECT 1 FROM branches WHERE id=? AND restaurant_id=? AND active=1", (data["branch_id"], data["restaurant_id"])).fetchone(): raise ValueError("الفرع غير تابع للمطعم المختار أو غير نشط.")
        rest = c.execute("SELECT billing_mode FROM restaurants WHERE id=? AND active=1", (data["restaurant_id"],)).fetchone()
        if not rest: raise ValueError("المطعم غير نشط.")
        billing = data.get("billing_mode") or rest[0]
        if billing not in ("كاش", "آجل"): raise ValueError("طريقة التحصيل غير صحيحة.")
        dist = float(data.get("distance_km") or 0); fee = float(data.get("delivery_fee") or 0)
        rider_id = data.get("rider_id"); rider = None
        if rider_id:
            rider = c.execute("SELECT * FROM riders WHERE id=?", (rider_id,)).fetchone()
            if not rider or rider["status"] == "غير نشط": raise ValueError("الطيار غير متاح.")
        comm = commission_for_order(dist, fee, dict(rider) if rider else None)
        cash = fee if billing == "كاش" else 0.0
        c.execute("INSERT INTO orders(id,order_no,restaurant_id,branch_id,delivery_address,delivery_lat,delivery_lng,distance_km,eta_minutes,billing_mode,rider_id,status,delivery_fee,rider_commission,reward,discount,cash_collected,notes,created_by,created_at,customer_phone,customer_name,track_token) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (oid, data["order_no"].strip(), data["restaurant_id"], data["branch_id"], data["delivery_address"].strip(), data.get("delivery_lat"), data.get("delivery_lng"), dist, int(data.get("eta_minutes") or 0), billing, rider_id, "تم التعيين" if rider_id else "جديد", fee, comm, float(data.get("reward") or 0), float(data.get("discount") or 0), cash, data.get("notes", "").strip(), actor["id"], now_iso(), data.get("customer_phone", "").strip(), data.get("customer_name", "").strip(), secrets.token_urlsafe(8)))
        if rider_id: c.execute("UPDATE riders SET active_orders=active_orders+1,status='في مهمة' WHERE id=?", (rider_id,))
    audit(actor["id"], "create", "order", oid, after=data | {"order_id": oid, "rider_commission": comm})
    return oid


def assign_rider(order_id, rider_id, actor):
    if not actor_is_owner(actor) and actor.get("role") != "DISPATCHER": raise PermissionError("تعيين الطيارين صلاحية المالك أو الديسباتشر فقط.")
    with get_conn() as c:
        oldr = c.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not oldr: raise ValueError("الطلب غير موجود.")
        old = dict(oldr)
        if old["status"] in ("تم التسليم", "ملغى"): raise ValueError("لا يمكن تعيين طلب مغلق.")
        if old["status"] in ("تم الاستلام", "في الطريق") and old["rider_id"] != rider_id: raise ValueError("الطلب خرج مع الطيار؛ لا يمكن تغييره الآن.")
        if old["rider_id"] == rider_id: return
        rider = None
        if rider_id:
            rider = c.execute("SELECT * FROM riders WHERE id=?", (rider_id,)).fetchone()
            if not rider or rider["status"] == "غير نشط": raise ValueError("الطيار غير متاح.")
        if old["rider_id"]:
            c.execute("UPDATE riders SET active_orders=MAX(0,active_orders-1) WHERE id=?", (old["rider_id"],))
            c.execute("UPDATE riders SET status=CASE WHEN active_orders=0 THEN 'متاح' ELSE status END WHERE id=?", (old["rider_id"],))
        comm = commission_for_order(old["distance_km"], old["delivery_fee"], dict(rider) if rider else None)
        if rider_id:
            c.execute("UPDATE riders SET active_orders=active_orders+1,status='في مهمة' WHERE id=?", (rider_id,))
            c.execute("UPDATE orders SET rider_id=?,rider_commission=?,status='تم التعيين' WHERE id=?", (rider_id, comm, order_id))
        else:
            c.execute("UPDATE orders SET rider_id=NULL,rider_commission=?,status='جديد',accepted_at=NULL WHERE id=?", (comm, order_id))
        new = dict(c.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone())
    audit(actor["id"], "assign_rider", "order", order_id, before=old, after=new)


def change_order_status(order_id, new_status, actor):
    with get_conn() as c:
        r = c.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not r: raise ValueError("الطلب غير موجود.")
        old = dict(r)
        role = actor["role"]
        if role == "RESTAURANT":
            if old["restaurant_id"] != actor.get("ref_id"): raise ValueError("لا تملك هذا الطلب.")
            if new_status != "ملغى" or old["status"] not in ("جديد", "تم التعيين", "تم القبول"): raise ValueError("المطعم يستطيع إلغاء الطلب قبل الاستلام فقط.")
        elif role == "RIDER":
            if old["rider_id"] != actor.get("ref_id"): raise ValueError("الطلب غير مخصص لك.")
            if new_status == "ملغى": raise ValueError("الإلغاء من الإدارة فقط.")
        elif role not in ("OWNER", "DISPATCHER"):
            raise PermissionError("لا تملك صلاحية تغيير حالة الطلب.")
        if new_status not in transitions(old["status"]): raise ValueError(f"الانتقال من {old['status']} إلى {new_status} غير مسموح.")
        stamp = now_iso(); cols = ["status=?"]; vals = [new_status]
        col = {"تم القبول": "accepted_at", "تم الاستلام": "picked_up_at", "تم التسليم": "delivered_at", "ملغى": "cancelled_at"}.get(new_status)
        if col: cols.append(f"{col}=?"); vals.append(stamp)
        vals.append(order_id); c.execute(f"UPDATE orders SET {', '.join(cols)} WHERE id=?", vals)
        if new_status in ("تم التسليم", "ملغى") and old["rider_id"]:
            c.execute("UPDATE riders SET active_orders=MAX(0,active_orders-1) WHERE id=?", (old["rider_id"],))
            c.execute("UPDATE riders SET status=CASE WHEN active_orders=0 THEN 'متاح' ELSE status END WHERE id=?", (old["rider_id"],))
        if new_status == "تم التسليم":
            c.execute("INSERT INTO ledger(txn_no,txn_type,account_type,account_id,amount,direction,reference_id,description,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                      (uid("TXN"), "إيراد خدمة توصيل", "إيراد_مستحق", old["restaurant_id"], float(old["delivery_fee"]), "استحقاق", order_id, "إثبات استحقاق خدمة التوصيل", actor["id"], stamp))
        new = dict(c.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone())
    audit(actor["id"], "status_change", "order", order_id, before=old, after=new)


def update_order(order_id, data, actor):
    """تعديل طلب نشط (المالك/الديسباتشر)."""
    if actor["role"] not in ("OWNER", "DISPATCHER"): raise PermissionError("تعديل الطلبات للمالك أو الديسباتشر فقط.")
    old = one("SELECT * FROM orders WHERE id=?", (order_id,))
    if not old: raise ValueError("الطلب غير موجود.")
    if not order_active(old["status"]): raise ValueError("الطلب مغلق — استخدم «تعديل حسابات الطلب» (للمالك).")
    fee = float(data["delivery_fee"]); dist = float(data["distance_km"]); billing = data["billing_mode"]
    if billing not in ("كاش", "آجل"): raise ValueError("طريقة التحصيل غير صحيحة.")
    comm = data.get("rider_commission")
    comm = commission_for_order(dist, fee, rider_row(old["rider_id"])) if comm is None else float(comm)
    with get_conn() as c:
        c.execute("UPDATE orders SET delivery_address=?,delivery_lat=?,delivery_lng=?,distance_km=?,eta_minutes=?,notes=?,delivery_fee=?,billing_mode=?,rider_commission=?,cash_collected=?,customer_phone=?,customer_name=?,reward=?,discount=? WHERE id=?",
                  (data["delivery_address"], data.get("delivery_lat"), data.get("delivery_lng"), dist, int(data["eta_minutes"]), data.get("notes", ""), fee, billing, comm, fee if billing == "كاش" else 0.0, data.get("customer_phone", ""), data.get("customer_name", ""), float(data.get("reward") or 0), float(data.get("discount") or 0), order_id))
    audit(actor["id"], "update", "order", order_id, before=old, after=one("SELECT * FROM orders WHERE id=?", (order_id,)))


def owner_edit_closed_order(order_id, data, actor):
    """المالك يعدّل حسابات طلب مكتمل حتى بعد التصفية — مع قيد تصحيحي شفاف بالفرق فقط."""
    need_owner(actor, "تعديل حسابات الطلبات المكتملة صلاحية المالك فقط.")
    old = one("SELECT * FROM orders WHERE id=?", (order_id,))
    if not old or old["status"] != "تم التسليم": raise ValueError("هذه الأداة للطلبات المسلّمة فقط.")
    fee = float(data["delivery_fee"]); comm = float(data["rider_commission"]); rew = float(data.get("reward") or 0); dis = float(data.get("discount") or 0)
    dist = float(data.get("distance_km") if data.get("distance_km") is not None else old["distance_km"]); billing = data["billing_mode"]
    if min(fee, comm, rew, dis) < 0: raise ValueError("لا يمكن إدخال قيم سالبة.")
    if billing not in ("كاش", "آجل"): raise ValueError("طريقة التحصيل غير صحيحة.")
    rider_settled = bool(old.get("comm_settled"))
    rest_settled = bool(one("SELECT 1 FROM settlement_items si JOIN settlements s ON s.id=si.settlement_id WHERE si.order_id=? AND s.kind='مطعم' AND COALESCE(s.voided,0)=0", (order_id,)))
    if billing != old["billing_mode"] and (rider_settled or rest_settled): raise ValueError("لا يمكن تغيير طريقة التحصيل لطلب مسوّى — ألغِ التسوية أولاً ثم عدّل.")
    old_cash = float(old["cash_collected"]); new_cash = fee if billing == "كاش" else 0.0
    stamp = now_iso()
    with get_conn() as c:
        c.execute("UPDATE orders SET delivery_fee=?,rider_commission=?,reward=?,discount=?,billing_mode=?,distance_km=?,cash_collected=?,customer_phone=COALESCE(?,customer_phone) WHERE id=?",
                  (fee, comm, rew, dis, billing, dist, new_cash, data.get("customer_phone"), order_id))
        if abs(fee - float(old["delivery_fee"])) > 0.001:
            c.execute("INSERT INTO ledger(txn_no,txn_type,account_type,account_id,amount,direction,reference_id,description,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                      (uid("TXN"), "تصحيح إيراد خدمة", "إيراد_مستحق", old["restaurant_id"], fee - float(old["delivery_fee"]), "استحقاق", order_id, f"تصحيح طلب {old['order_no']}", actor["id"], stamp))
        if rider_settled:
            old_net = old_cash - float(old["rider_commission"]) - float(old["reward"]) + float(old["discount"])
            new_net = new_cash - comm - rew + dis
            d_net = round(new_net - old_net, 2); d_cash = round(new_cash - old_cash, 2)
            if abs(d_net) > 0.001 or abs(d_cash) > 0.001:
                sid = uid("RFIX")
                c.execute("INSERT INTO settlements(id,kind,party_id,period_start,period_end,gross,commissions,rewards,discounts,cash_due,paid,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                          (sid, "تصحيح_طيار", old["rider_id"], today_str(), today_str(), d_cash, comm - float(old["rider_commission"]), rew - float(old["reward"]), dis - float(old["discount"]), d_net, d_net, actor["id"], stamp))
                c.execute("INSERT INTO settlement_items(id,settlement_id,order_id,amount) VALUES (?,?,?,?)", (uid("SETI"), sid, order_id, d_cash))
                if abs(d_net) > 0.001:
                    c.execute("INSERT INTO ledger(txn_no,txn_type,account_type,account_id,amount,direction,reference_id,description,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                              (uid("TXN"), "تصحيح تصفية طيار", "طيار", old["rider_id"], abs(d_net), "داخل" if d_net > 0 else "خارج", sid, f"تصحيح طلب {old['order_no']}", actor["id"], stamp))
    audit(actor["id"], "owner_edit_closed", "order", order_id, before=old, after=one("SELECT * FROM orders WHERE id=?", (order_id,)))
    return rider_settled, rest_settled


# =========================================================
# الحضور / المرتبات
# =========================================================
def attendance_hours(row):
    if not row or not row.get("clock_in") or not row.get("clock_out"): return 0.0
    try:
        start = parse_ts(row["clock_in"]); end = parse_ts(row["clock_out"])
        if end < start: end += timedelta(days=1)
        return round(max(0, (end - start).total_seconds() / 60 - float(row.get("break_minutes") or 0)) / 60, 2)
    except Exception:
        return 0.0


def attendance_for_month(rider_id, period):
    s, e = month_bounds(period)
    return df("SELECT * FROM attendance WHERE rider_id=? AND work_date>=? AND work_date<? ORDER BY work_date", (rider_id, s, e))


def upsert_attendance(data, actor):
    rid = data["rider_id"]; wd = data["work_date"]
    old = one("SELECT * FROM attendance WHERE rider_id=? AND work_date=?", (rid, wd))
    if actor["role"] == "RIDER" and actor.get("ref_id") != rid: raise PermissionError("غير مسموح.")
    with get_conn() as c:
        if old:
            c.execute("UPDATE attendance SET clock_in=?,clock_out=?,break_minutes=?,status=?,reason=? WHERE id=?", (data.get("clock_in") or None, data.get("clock_out") or None, int(data.get("break_minutes") or 0), data["status"], data.get("reason", ""), old["id"]))
            aid = old["id"]
        else:
            aid = uid("ATT")
            c.execute("INSERT INTO attendance(id,rider_id,work_date,clock_in,clock_out,break_minutes,status,reason,created_at) VALUES (?,?,?,?,?,?,?,?,?)", (aid, rid, wd, data.get("clock_in") or None, data.get("clock_out") or None, int(data.get("break_minutes") or 0), data["status"], data.get("reason", ""), now_iso()))
    audit(actor["id"], "upsert", "attendance", aid, before=old, after=one("SELECT * FROM attendance WHERE id=?", (aid,)))


def payroll_summary(rider_id, period):
    """إقفال الشهر = الراتب − خصم الإجازات ± تسويات. العمولات في «حساب الطيار» منفصلة تماماً."""
    rider = rider_row(rider_id)
    if not rider: raise ValueError("الطيار غير موجود.")
    terms = rider_terms(rider); monthly = terms["mode"] == "MONTHLY"
    start, end = month_bounds(period)
    att = attendance_for_month(rider_id, period)
    hours = round(sum(attendance_hours(x) for x in att.to_dict("records")), 2) if not att.empty else 0.0
    present = int((att["status"] == "حاضر").sum()) if not att.empty else 0
    excused = int((att["status"] == "إجازة بعذر").sum()) if not att.empty else 0
    unexcused = int((att["status"] == "إجازة بدون عذر").sum()) if not att.empty else 0
    wd_days = float(get_setting("working_days", 26))
    daily = float(rider["salary"]) / wd_days
    leave_ded = (excused * float(get_setting("excused_leave_days", 1)) + unexcused * float(get_setting("unexcused_leave_days", 1.25))) * daily if monthly else 0.0
    cnt = one("SELECT COUNT(*) n, COALESCE(SUM(CASE WHEN comm_settled=1 THEN 1 ELSE 0 END),0) s FROM orders WHERE rider_id=? AND status='تم التسليم' AND delivered_at>=? AND delivered_at<?", (rider_id, start + " 00:00:00", end + " 00:00:00"))
    adj = df("SELECT type,COALESCE(SUM(amount),0) amount FROM payroll_adjustments WHERE rider_id=? AND period=? GROUP BY type", (rider_id, period))
    add = float(adj.loc[adj["type"] == "إضافة", "amount"].sum()) if not adj.empty else 0.0
    deduct = float(adj.loc[adj["type"].isin(["خصم", "سلفة"]), "amount"].sum()) if not adj.empty else 0.0
    paid = float(df("SELECT COALESCE(SUM(amount),0) x FROM payroll_payments WHERE rider_id=? AND period=?", (rider_id, period))["x"][0])
    basic = float(rider["salary"]) if monthly else 0.0
    net = max(0.0, basic - leave_ded + add - deduct)
    return {"rider": rider, "period": period, "mode": terms["mode"], "mode_label": PAY_MODES[terms["mode"]], "present": present, "excused": excused, "unexcused": unexcused,
            "hours": hours, "expected_hours": wd_days * float(get_setting("daily_work_hours", 8)), "basic": basic, "daily_rate": daily, "leave_deduction": leave_ded,
            "commissions": 0.0, "rewards": 0.0, "discounts": 0.0, "adjust_add": add, "adjust_deduct": deduct, "net": net, "paid": paid,
            "remaining": max(0, net - paid), "orders_count": int(cnt["n"]), "settled_count": int(cnt["s"])}


def add_payroll_adjustment(data, actor):
    if actor["role"] not in ("OWNER", "ACCOUNTANT"): raise PermissionError("غير مسموح.")
    amount = float(data["amount"])
    if amount <= 0: raise ValueError("المبلغ يجب أن يكون أكبر من صفر.")
    aid = uid("PADJ")
    with get_conn() as c: c.execute("INSERT INTO payroll_adjustments(id,rider_id,period,type,amount,description,created_by,created_at) VALUES (?,?,?,?,?,?,?,?)", (aid, data["rider_id"], data["period"], data["type"], amount, data.get("description", ""), actor["id"], now_iso()))
    audit(actor["id"], "create", "payroll_adjustment", aid, after=data | {"id": aid})


def delete_payroll_adjustment(aid, actor):
    need_owner(actor, "حذف التسويات صلاحية المالك فقط.")
    old = one("SELECT * FROM payroll_adjustments WHERE id=?", (aid,))
    if not old: raise ValueError("غير موجود.")
    with get_conn() as c: c.execute("DELETE FROM payroll_adjustments WHERE id=?", (aid,))
    audit(actor["id"], "delete", "payroll_adjustment", aid, before=old)


def record_payroll_payment(data, actor):
    if actor["role"] not in ("OWNER", "ACCOUNTANT"): raise PermissionError("غير مسموح.")
    p = payroll_summary(data["rider_id"], data["period"]); amount = float(data["amount"])
    if amount <= 0 or amount > p["remaining"] + 0.01: raise ValueError(f"المبلغ يتجاوز المستحق المتبقي ({p['remaining']:.2f} ج).")
    pid = uid("PAY"); stamp = now_iso()
    with get_conn() as c:
        c.execute("INSERT INTO payroll_payments(id,rider_id,period,amount,method,reference,notes,paid_at,created_by) VALUES (?,?,?,?,?,?,?,?,?)", (pid, data["rider_id"], data["period"], amount, data["method"], data.get("reference", ""), data.get("notes", ""), stamp, actor["id"]))
        c.execute("INSERT INTO ledger(txn_no,txn_type,account_type,account_id,amount,direction,reference_id,description,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)", (uid("TXN"), "صرف راتب شهرى", "طيار", data["rider_id"], amount, "خارج", pid, f"راتب {data['period']}", actor["id"], stamp))
    audit(actor["id"], "pay", "payroll_payment", pid, after=data | {"id": pid, "amount": amount}); return pid


def void_payroll_payment(pid, actor):
    need_owner(actor, "إلغاء دفعات المرتبات صلاحية المالك فقط.")
    old = one("SELECT * FROM payroll_payments WHERE id=?", (pid,))
    if not old: raise ValueError("الدفعة غير موجودة.")
    with get_conn() as c:
        c.execute("DELETE FROM payroll_payments WHERE id=?", (pid,))
        c.execute("INSERT INTO ledger(txn_no,txn_type,account_type,account_id,amount,direction,reference_id,description,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)", (uid("TXN"), "عكس صرف راتب", "طيار", old["rider_id"], old["amount"], "داخل", pid, f"إلغاء دفعة راتب {old['period']}", actor["id"], now_iso()))
    audit(actor["id"], "void", "payroll_payment", pid, before=old)


# =========================================================
# التصفية والخزينة
# =========================================================
def rider_unsettled_orders(rider_id, start, end):
    """كل طلبات الطيار المسلّمة التي لم تُسوَّ عمولتها (كاش وآجل معاً)."""
    return df("""SELECT o.*,r.name restaurant,b.name branch,
                 MAX(0,o.cash_collected-COALESCE((SELECT SUM(si.amount) FROM settlement_items si WHERE si.order_id=o.id),0)) remaining_cash
                 FROM orders o JOIN restaurants r ON r.id=o.restaurant_id JOIN branches b ON b.id=o.branch_id
                 WHERE o.rider_id=? AND o.status='تم التسليم' AND COALESCE(o.comm_settled,0)=0 AND o.delivered_at>=? AND o.delivered_at<?
                 ORDER BY o.delivered_at""", (rider_id, start + " 00:00:00", end + " 00:00:00"))


def create_rider_settlement(rider_id, start, end, actor):
    """تصفية حساب الطيار: عمولات الكاش + الآجل + مكافآت − خصومات − الكاش الذي معه، في قيد واحد."""
    need_owner(actor, "تصفية حساب الطيارين صلاحية المالك فقط.")
    os_ = rider_unsettled_orders(rider_id, start, end)
    if os_.empty: raise ValueError("لا توجد طلبات غير مسوّاة في الفترة.")
    gross = float(os_["remaining_cash"].sum()); commissions = float(os_["rider_commission"].sum()); rewards = float(os_["reward"].sum()); discounts = float(os_["discount"].sum())
    due = round(gross - commissions - rewards + discounts, 2)
    sid = uid("RSTL"); stamp = now_iso()
    with get_conn() as c:
        c.execute("INSERT INTO settlements(id,kind,party_id,period_start,period_end,gross,commissions,rewards,discounts,cash_due,paid,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (sid, "حساب_طيار", rider_id, start, end, gross, commissions, rewards, discounts, due, due, actor["id"], stamp))
        for row in os_.to_dict("records"):
            if float(row["remaining_cash"]) > 0.01:
                c.execute("INSERT INTO settlement_items(id,settlement_id,order_id,amount) VALUES (?,?,?,?)", (uid("SETI"), sid, row["id"], float(row["remaining_cash"])))
            c.execute("UPDATE orders SET comm_settled=1,comm_settlement_id=? WHERE id=?", (sid, row["id"]))
        if due != 0:
            c.execute("INSERT INTO ledger(txn_no,txn_type,account_type,account_id,amount,direction,reference_id,description,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)", (uid("TXN"), "تصفية حساب طيار", "طيار", rider_id, abs(due), "داخل" if due > 0 else "خارج", sid, f"تصفية {start} إلى {end}", actor["id"], stamp))
    audit(actor["id"], "settle", "rider_account_settlement", sid, after={"gross": gross, "commissions": commissions, "rewards": rewards, "discounts": discounts, "net": due, "orders": int(len(os_))})
    return sid, due, len(os_)


def restaurant_unsettled_orders(rid, start, end):
    return df("""SELECT o.*,b.name branch,
                 o.delivery_fee-COALESCE((SELECT SUM(si.amount) FROM settlement_items si WHERE si.order_id=o.id),0) remaining_due
                 FROM orders o JOIN branches b ON b.id=o.branch_id
                 WHERE o.restaurant_id=? AND o.status='تم التسليم' AND o.billing_mode='آجل' AND o.delivered_at>=? AND o.delivered_at<?
                 AND o.delivery_fee-COALESCE((SELECT SUM(si.amount) FROM settlement_items si WHERE si.order_id=o.id),0)>0.01""", (rid, start + " 00:00:00", end + " 00:00:00"))


def create_restaurant_settlement(rid, start, end, paid, actor):
    if actor["role"] not in ("OWNER", "ACCOUNTANT"): raise PermissionError("تحصيل المطاعم للمالك أو الحسابات فقط.")
    os_ = restaurant_unsettled_orders(rid, start, end)
    if os_.empty: raise ValueError("لا توجد مديونية آجل غير مسددة في الفترة.")
    due = float(os_["remaining_due"].sum()); paid = float(paid)
    if paid <= 0 or paid > due + 0.01: raise ValueError(f"الدفعة يجب أن تكون بين 0 و{due:.2f} ج.")
    sid = uid("RSET"); stamp = now_iso()
    with get_conn() as c:
        c.execute("INSERT INTO settlements(id,kind,party_id,period_start,period_end,gross,paid,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?)", (sid, "مطعم", rid, start, end, due, paid, actor["id"], stamp))
        rem = paid
        for row in os_.sort_values("delivered_at").to_dict("records"):
            alloc = min(rem, float(row["remaining_due"]))
            if alloc <= 0: break
            c.execute("INSERT INTO settlement_items(id,settlement_id,order_id,amount) VALUES (?,?,?,?)", (uid("SETI"), sid, row["id"], alloc)); rem -= alloc
        c.execute("INSERT INTO ledger(txn_no,txn_type,account_type,account_id,amount,direction,reference_id,description,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)", (uid("TXN"), "تحصيل مطعم آجل", "مطعم", rid, paid, "داخل", sid, "تحصيل مديونية مطعم آجل", actor["id"], stamp))
    audit(actor["id"], "settle", "restaurant_settlement", sid, after={"due": due, "paid": paid, "orders": int(len(os_))})
    return sid, due, paid


def _void_one(c, s, actor, stamp):
    for r in c.execute("SELECT * FROM ledger WHERE reference_id=? AND direction IN ('داخل','خارج')", (s["id"],)).fetchall():
        c.execute("INSERT INTO ledger(txn_no,txn_type,account_type,account_id,amount,direction,reference_id,description,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                  (uid("TXN"), "عكس " + r["txn_type"], r["account_type"], r["account_id"], r["amount"], "خارج" if r["direction"] == "داخل" else "داخل", s["id"], "إلغاء تسوية", actor["id"], stamp))
    c.execute("DELETE FROM settlement_items WHERE settlement_id=?", (s["id"],))
    c.execute("UPDATE settlements SET voided=1 WHERE id=?", (s["id"],))


def void_settlement(sid, actor):
    """إلغاء تسوية بالكامل: تعود الطلبات غير مسوّاة ويُسجَّل قيد عكسي (ومعه قيود التصحيح المرتبطة)."""
    need_owner(actor, "إلغاء التسويات صلاحية المالك فقط.")
    s = one("SELECT * FROM settlements WHERE id=?", (sid,))
    if not s: raise ValueError("التسوية غير موجودة.")
    if s.get("voided"): raise ValueError("التسوية ملغاة بالفعل.")
    if s["kind"] == "تصحيح_طيار": raise ValueError("قيود التصحيح تُلغى مع التسوية الأصلية.")
    stamp = now_iso()
    with get_conn() as c:
        oids = {r[0] for r in c.execute("SELECT order_id FROM settlement_items WHERE settlement_id=?", (sid,)).fetchall()}
        oids |= {r[0] for r in c.execute("SELECT id FROM orders WHERE comm_settlement_id=?", (sid,)).fetchall()}
        _void_one(c, s, actor, stamp)
        if s["kind"] in ("طيار_كاش", "حساب_طيار") and oids:
            q = ",".join("?" * len(oids)); ids = list(oids)
            for fx in c.execute(f"SELECT DISTINCT s.* FROM settlements s JOIN settlement_items si ON si.settlement_id=s.id WHERE s.kind='تصحيح_طيار' AND COALESCE(s.voided,0)=0 AND si.order_id IN ({q})", ids).fetchall():
                _void_one(c, dict(fx), actor, stamp)
            c.execute(f"UPDATE orders SET comm_settled=0,comm_settlement_id=NULL WHERE id IN ({q})", ids)
    audit(actor["id"], "void", "settlement", sid, before=s)


def treasury_balance():
    return float(df("SELECT COALESCE(SUM(CASE WHEN direction='داخل' THEN amount WHEN direction='خارج' THEN -amount ELSE 0 END),0) x FROM ledger")["x"][0])


def cash_receipts_today():
    return float(df("SELECT COALESCE(SUM(amount),0) x FROM ledger WHERE direction='داخل' AND substr(created_at,1,10)=?", (today_str(),))["x"][0])


# =========================================================
# تطويرات V11: تسعير تلقائي، نسخ احتياطي، كاش الطيارين، كشوف، تتبع العميل، تصدير Excel
# =========================================================
def auto_backup():
    """نسخة احتياطية يومية تلقائية (آخر 14 يوماً) بجوار قاعدة البيانات."""
    try:
        d = DB_PATH.resolve().parent / "backups"; d.mkdir(exist_ok=True)
        f = d / f"onway_{today_str()}.db"
        if f.exists(): return
        src = sqlite3.connect(DB_PATH); dst = sqlite3.connect(f); src.backup(dst); dst.close(); src.close()
        for old in sorted(d.glob("onway_*.db"))[:-14]: old.unlink()
    except Exception:
        pass


def suggested_fee(distance):
    """رسوم التوصيل المقترحة من المسافة: أساسية حتى X كم + سعر لكل كم زائد."""
    base = _num(get_setting("fee_base", 30), 30.0); bkm = _num(get_setting("fee_base_km", 3), 3.0); ex = _num(get_setting("fee_extra_km", 5), 5.0)
    d = max(0.0, float(distance or 0))
    return round(base if d <= bkm else base + math.ceil(d - bkm) * ex, 2)


def riders_cash_holding():
    """الكاش الذي مع كل طيار ولم يُورَّد (صافي بعد عمولته)."""
    return df("""SELECT ry.id,ry.name,COUNT(*) n,SUM(rem) gross,SUM(rem-x.rider_commission-x.reward+x.discount) net
                 FROM (SELECT o.rider_id,o.rider_commission,o.reward,o.discount,
                              o.cash_collected-COALESCE((SELECT SUM(si.amount) FROM settlement_items si WHERE si.order_id=o.id),0) rem
                       FROM orders o WHERE o.status='تم التسليم' AND o.billing_mode='كاش') x
                 JOIN riders ry ON ry.id=x.rider_id WHERE rem>0.01 GROUP BY ry.id ORDER BY net DESC""")


def restaurant_statement(rid, start, end):
    return df("""SELECT o.order_no,o.delivered_at,b.name branch,o.billing_mode,o.delivery_fee,
                 COALESCE((SELECT SUM(si.amount) FROM settlement_items si WHERE si.order_id=o.id),0) settled
                 FROM orders o JOIN branches b ON b.id=o.branch_id
                 WHERE o.restaurant_id=? AND o.status='تم التسليم' AND o.delivered_at>=? AND o.delivered_at<? ORDER BY o.delivered_at""",
              (rid, start + " 00:00:00", end + " 00:00:00"))


def on_time_rate(orders):
    if orders is None or orders.empty: return 0.0
    grace = int(float(get_setting("order_overdue_grace_minutes", 15))); ok = tot = 0
    for _, o in orders.iterrows():
        if not o.get("eta_minutes"): continue
        try:
            tot += 1
            if parse_ts(o["delivered_at"]) <= parse_ts(o["created_at"]) + timedelta(minutes=int(o["eta_minutes"]) + grace): ok += 1
        except Exception: pass
    return round(ok / tot * 100, 1) if tot else 0.0


def to_xlsx(sheets):
    try:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            for name, frame in sheets.items(): frame.to_excel(w, sheet_name=name[:30], index=False)
        return buf.getvalue()
    except Exception:
        return None


def export_button(label, sheets, filename):
    data = to_xlsx(sheets)
    if data: st.download_button(label, data=data, file_name=filename + ".xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    else: st.download_button(label + " (CSV)", data=next(iter(sheets.values())).to_csv(index=False, encoding="utf-8-sig"), file_name=filename + ".csv", mime="text/csv", use_container_width=True)


# =========================================================
# المكونات: الخريطة + الصوت + حفظ الجهاز
# =========================================================
MAP_COMPONENT = None
NOTIFY_COMPONENT = None
DEVICE_COMPONENT = None
SHELL_COMPONENT = None
VOICE_COMPONENT = None
try:
    from streamlit.components.v2 import component as _component

    MAP_HTML = """
    <div id='owroot' dir='rtl'>
      <div id='owsearchbar'>
        <input id='owsearch' autocomplete='off' placeholder='ابحث عن شارع، مطعم، منطقة أو وجهة…' />
        <button id='owmic' aria-label='بحث صوتي'>🎤</button>
        <button id='owsearchbtn'>بحث</button>
      </div>
      <div id='owmap'></div>
      <div id='owstatus'></div>
      <button id='owgps' type='button'>📍 تشغيل موقعي</button>
      <div id='owcontrols'>
        <button id='owfit' type='button' title='ملاءمة الخريطة'>⌖</button>
        <button id='owshare' type='button' title='مشاركة الوجهة'>↗</button>
        <button id='owfull' type='button' title='شاشة كاملة'>⛶</button>
      </div>
      <div id='owbadge'></div>
    </div>
    """
    MAP_CSS = """
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@500;600;700;800;900&display=swap');
    *{box-sizing:border-box}
    #owroot{position:relative;width:100%;height:clamp(460px,70svh,800px);min-height:460px;overflow:hidden;border:1px solid #28303a;border-radius:18px;background:#101318;font-family:Cairo,Arial,sans-serif;isolation:isolate}
    #owmap{position:absolute;inset:0;width:100%;height:100%;background:#20242b}
    .leaflet-container{font-family:Cairo,Arial,sans-serif!important;background:#20242b}
    .leaflet-popup-content{direction:rtl;line-height:1.75;font-size:12px}
    #owsearchbar{position:absolute;top:10px;left:50%;transform:translateX(-50%);z-index:1200;width:min(94%,570px);display:flex;gap:6px;padding:7px;background:rgba(14,17,22,.96);border:1px solid #39414d;border-radius:999px;box-shadow:0 10px 30px rgba(0,0,0,.30)}
    #owsearch{flex:1;min-width:0;border:0;outline:0;background:transparent;color:#fff;font:700 13px Cairo,Arial;padding:8px 10px}
    #owsearch::placeholder{color:#8792a2}
    #owsearchbar button{border:0;color:#fff;border-radius:999px;padding:9px 12px;font:900 12px Cairo,Arial;cursor:pointer;touch-action:manipulation}
    #owmic{background:#00B368}#owsearchbtn{background:#FF5A00}
    #owstatus{display:none;position:absolute;top:68px;right:50%;transform:translateX(50%);z-index:1250;background:rgba(14,17,22,.97);color:#fff;padding:8px 13px;border-radius:999px;font:800 11px Cairo;box-shadow:0 8px 20px rgba(0,0,0,.28)}
    #owgps{display:none;position:absolute;top:66px;right:12px;z-index:1250;border:1px solid #2d3744;background:#007AFF;color:#fff;border-radius:999px;padding:10px 13px;font:900 11px Cairo;box-shadow:0 6px 17px rgba(0,0,0,.25);cursor:pointer;touch-action:manipulation}
    #owgps.on{background:#00B368}#owgps.warn{background:#FFB020;color:#151515}
    #owcontrols{position:absolute;bottom:15px;left:15px;z-index:1200;display:flex;gap:7px}
    #owcontrols button{width:44px;height:44px;border:1px solid #3a424e;background:rgba(14,17,22,.94);color:#fff;border-radius:13px;font-size:18px;cursor:pointer;touch-action:manipulation}
    #owbadge{display:none;position:absolute;bottom:16px;right:16px;z-index:1200;background:rgba(14,17,22,.94);color:#dfe6ee;border:1px solid #3a424e;padding:8px 10px;border-radius:999px;font:800 10px Cairo}
    .owpin{display:flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:50%;border:2px solid #fff;box-shadow:0 4px 15px rgba(0,0,0,.35);font-size:18px}
    .owpin.rider{box-shadow:0 0 0 5px rgba(0,194,122,.12),0 4px 15px rgba(0,0,0,.35)}
    @media(max-width:650px){#owroot{height:calc(100svh - 320px);min-height:420px;border-radius:14px}#owsearchbar{width:95%;top:8px}#owsearch{font-size:15px}.leaflet-control-zoom{margin-bottom:74px!important}.leaflet-control-attribution{font-size:8px!important}}
    """
    MAP_JS = r"""
    export default function(component){
      const {data,setTriggerValue,parentElement}=component;
      const root=parentElement;if(!root)return;
      const mapEl=root.querySelector('#owmap'),searchEl=root.querySelector('#owsearch'),searchBtn=root.querySelector('#owsearchbtn'),micBtn=root.querySelector('#owmic'),gpsBtn=root.querySelector('#owgps'),statusEl=root.querySelector('#owstatus'),badge=root.querySelector('#owbadge');
      const cfg=data||{};
      const esc=v=>String(v==null?'':v).replace(/[<>&"']/g,ch=>({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;',"'":'&#39;'}[ch]));
      const showStatus=t=>{statusEl.textContent=t;statusEl.style.display='block';clearTimeout(root.__owStatusTimer);root.__owStatusTimer=setTimeout(()=>statusEl.style.display='none',2600)};
      const setBadge=(t,kind)=>{badge.textContent=t;badge.style.display='block';badge.style.borderColor=kind==='ok'?'#2a614e':kind==='warn'?'#6b541e':'#3a424e';badge.style.color=kind==='ok'?'#8df0c8':kind==='warn'?'#ffd36e':'#dbe1e8'};
      const loadScriptFrom=src=>new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=src;s.async=true;s.onload=resolve;s.onerror=()=>reject(new Error('leaflet load failed'));document.head.appendChild(s)});
      const loadScript=async()=>{if(window.L)return;const urls=['https://unpkg.com/leaflet@1.9.4/dist/leaflet.js','https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js'];let last;for(const u of urls){try{await loadScriptFrom(u);return}catch(e){last=e}}throw last||new Error('leaflet load failed')};
      const loadCss=()=>{if(document.getElementById('onway-leaflet-css'))return;const l=document.createElement('link');l.id='onway-leaflet-css';l.rel='stylesheet';l.href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';l.onerror=()=>{if(!document.getElementById('onway-leaflet-css-fb')){const f=document.createElement('link');f.id='onway-leaflet-css-fb';f.rel='stylesheet';f.href='https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css';document.head.appendChild(f)}};document.head.appendChild(l)};
      const distanceM=(a,b)=>{const R=6371000,p1=a[0]*Math.PI/180,p2=b[0]*Math.PI/180,dp=(b[0]-a[0])*Math.PI/180,dl=(b[1]-a[1])*Math.PI/180,q=Math.sin(dp/2)**2+Math.cos(p1)*Math.cos(p2)*Math.sin(dl/2)**2;return 2*R*Math.asin(Math.sqrt(q))};
      const fire=(name,payload)=>{try{setTriggerValue(name,JSON.stringify(payload))}catch(e){}};
      (async()=>{
        loadCss();
        try{await loadScript()}catch(e){showStatus('تعذر تحميل محرك الخريطة الآن');setBadge('🟠 تحقق من الإنترنت','warn');return;}
        let map=mapEl.__onwayMap;
        if(!map){
          const center=cfg.center||[31.2001,29.9187];
          map=L.map(mapEl,{zoomControl:false,preferCanvas:true,fadeAnimation:false,zoomAnimation:false,markerZoomAnimation:false,tap:true}).setView(center,Number(cfg.zoom||12));
          mapEl.__onwayMap=map;mapEl.__layer=L.layerGroup().addTo(map);mapEl.__route=L.layerGroup().addTo(map);mapEl.__me=L.layerGroup().addTo(map);
          mapEl.__routeKey='';mapEl.__fitKey='';mapEl.__userMoved=false;mapEl.__routeOrigin=null;mapEl.__routeTarget=null;mapEl.__routeFetchedAt=0;
          L.control.zoom({position:'bottomleft'}).addTo(map);
          L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,detectRetina:true,crossOrigin:true,attribution:'© OpenStreetMap • ONWAY'}).addTo(map);
          [60,450,1200].forEach(t=>setTimeout(()=>map.invalidateSize(false),t));
          window.addEventListener('resize',()=>map.invalidateSize(false),{passive:true});
          if(window.ResizeObserver){mapEl.__ro=new ResizeObserver(()=>map.invalidateSize(false));mapEl.__ro.observe(mapEl);}
          map.on('dragstart',()=>{mapEl.__userMoved=true});map.on('zoomstart',()=>{mapEl.__userMoved=true});
        }
        map.invalidateSize(false);
        mapEl.__cfg=cfg;
        mapEl.__layer.clearLayers();
        const bounds=[];
        for(const p of (cfg.points||[])){
          if(p.lat==null||p.lng==null||Number.isNaN(Number(p.lat))||Number.isNaN(Number(p.lng)))continue;
          const color=p.kind==='rider'?(p.online?'#00B368':'#7F8A97'):p.kind==='self'?'#007AFF':p.kind==='branch'?'#FF5A00':'#FF4D4D';
          const cls=p.kind==='rider'?'owpin rider':'owpin';
          const icon=L.divIcon({className:'',html:`<div class='${cls}' style='background:${color}'>${esc(p.icon||'📍')}</div>`,iconSize:[36,36],iconAnchor:[18,18]});
          const m=L.marker([Number(p.lat),Number(p.lng)],{icon,keyboard:false}).addTo(mapEl.__layer);
          let html=`<b>${esc(p.title||'')}</b>`;if(p.meta)html+=`<br>${esc(p.meta)}`;if(p.kind==='rider'&&p.accuracy!=null)html+=`<br>دقة GPS: ${esc(Number(p.accuracy).toFixed(1))} م`;
          m.bindPopup(`<div style='direction:rtl;font-family:Cairo,Arial;min-width:170px'>${html}</div>`);m.on('click',()=>fire('marker_click',{id:p.id,kind:p.kind}));bounds.push([Number(p.lat),Number(p.lng)]);
        }
        const route=cfg.route;
        if(route&&route.from&&route.to){
          const from=[Number(route.from[0]),Number(route.from[1])],to=[Number(route.to[0]),Number(route.to[1])];
          const targetKey=JSON.stringify(to);
          const moved=mapEl.__routeOrigin?distanceM(mapEl.__routeOrigin,from):999999;
          const needFetch=!mapEl.__routeOrigin||mapEl.__routeTarget!==targetKey||moved>150||(Date.now()-Number(mapEl.__routeFetchedAt||0)>30000);
          if(needFetch&&!mapEl.__routeLoading){
            mapEl.__routeLoading=true;
            const url=`https://router.project-osrm.org/route/v1/driving/${from[1]},${from[0]};${to[1]},${to[0]}?overview=full&geometries=geojson&steps=false`;
            fetch(url).then(r=>r.json()).then(d=>{
              mapEl.__routeLoading=false;
              if(d.routes&&d.routes[0]){
                const rt=d.routes[0],coords=rt.geometry.coordinates.map(c=>[c[1],c[0]]);
                mapEl.__route.clearLayers();L.polyline(coords,{color:'#FF5A00',weight:6,opacity:.9,lineCap:'round',lineJoin:'round'}).addTo(mapEl.__route);
                const fresh=mapEl.__routeTarget!==targetKey;
                mapEl.__routeOrigin=from;mapEl.__routeTarget=targetKey;mapEl.__routeFetchedAt=Date.now();
                fire('route_meta',{distance_m:rt.distance,duration_s:rt.duration});
                if((fresh||!mapEl.__fitKey)&&!mapEl.__userMoved){map.fitBounds(coords,{padding:[46,46],maxZoom:16});mapEl.__fitKey=targetKey;}
              } else {showStatus('لم يتم العثور على خط سير مناسب');}
            }).catch(()=>{mapEl.__routeLoading=false;showStatus('تعذر حساب خط السير حالياً')});
          }
        }else{
          mapEl.__route.clearLayers();mapEl.__routeOrigin=null;mapEl.__routeTarget=null;mapEl.__routeFetchedAt=0;mapEl.__fitKey='';
          if(bounds.length&&!cfg.preserveView&&!mapEl.__userMoved){map.fitBounds(bounds,{padding:[42,42],maxZoom:Number(cfg.zoom||14)});}
        }
        if(cfg.selected&&cfg.selected.lat!=null){
          const k=JSON.stringify([cfg.selected.lat,cfg.selected.lng,cfg.selected.title||'']);
          if(mapEl.__selectedKey!==k){mapEl.__selectedKey=k;map.setView([Number(cfg.selected.lat),Number(cfg.selected.lng)],Math.max(16,Number(cfg.zoom||12)));}
          L.circleMarker([Number(cfg.selected.lat),Number(cfg.selected.lng)],{radius:10,color:'#FF5A00',weight:3,fillColor:'#FF5A00',fillOpacity:.20}).addTo(mapEl.__layer);
        }
        if(!mapEl.__clickBound){
          mapEl.__clickBound=true;
          map.on('click',e=>{const c=mapEl.__cfg||{};if(!c.clickable)return;const lat=Number(e.latlng.lat.toFixed(6)),lng=Number(e.latlng.lng.toFixed(6));showStatus('جاري تحديد العنوان…');
            fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}&zoom=18&accept-language=ar`).then(r=>r.json()).then(d=>{fire('map_click',{lat,lng,address:(d&&d.display_name)||''});showStatus('تم تحديد الموقع ✅')}).catch(()=>{fire('map_click',{lat,lng,address:''});showStatus('تم تحديد النقطة')})});
        }
        const doSearch=()=>{const q=(searchEl.value||'').trim();if(!q)return;showStatus('جاري البحث…');
          fetch(`https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&accept-language=ar&q=${encodeURIComponent(q+', Alexandria, Egypt')}`).then(r=>r.json()).then(d=>{if(!d||!d.length){showStatus('لم يتم العثور على المكان');return}const x=d[0];fire('search_result',{lat:Number(x.lat),lng:Number(x.lon),address:x.display_name||q,title:q});showStatus('تم العثور على المكان ✅')}).catch(()=>showStatus('تعذر الاتصال بخدمة البحث'))};
        searchBtn.onclick=doSearch;searchEl.onkeydown=e=>{if(e.key==='Enter')doSearch()};
        micBtn.onclick=()=>{const SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR){showStatus('البحث الصوتي غير مدعوم');return}const sr=new SR();sr.lang='ar-EG';sr.interimResults=false;sr.onstart=()=>showStatus('تحدث الآن…');sr.onresult=e=>{searchEl.value=e.results[0][0].transcript;doSearch()};sr.onerror=()=>showStatus('تعذر قراءة الصوت');sr.start()};

        // ---------- GPS دقيق: أعلى دقة + رفض القراءات الضعيفة + تنعيم + كشف القفزات ----------
        const gs=mapEl.__gps||(mapEl.__gps={sm:null,n:0,lastRaw:null,lastSent:0,lastSentPos:null});
        const geolocate=()=>{
          if(!navigator.geolocation){setBadge('🟠 GPS غير متاح','warn');return}
          gpsBtn.classList.remove('warn');gpsBtn.textContent='⏳ تحديد الموقع…';setBadge('⏳ جاري الحصول على GPS');
          const push=pos=>{
            const c=pos.coords,ts=Date.now();
            let lat=c.latitude,lng=c.longitude;const acc=c.accuracy==null?999:c.accuracy;gs.n++;
            if(acc>80&&gs.sm&&gs.n>3)return;                       // قراءة ضعيفة بعد وجود قراءة جيدة
            if(gs.lastRaw){const dt=(ts-gs.lastRaw.ts)/1000,dd=distanceM([gs.lastRaw.lat,gs.lastRaw.lng],[lat,lng]);if(dt>0&&dd/dt>50&&acc>25)return}  // قفزة مستحيلة
            gs.lastRaw={lat,lng,ts};
            if(gs.sm){
              const moved=distanceM([gs.sm.lat,gs.sm.lng],[lat,lng]);
              const still=(c.speed==null||c.speed<1);
              if(still&&moved<Math.max(4,acc*.5)){lat=gs.sm.lat;lng=gs.sm.lng}   // منع اهتزاز النقطة أثناء الوقوف
              else{const a=Math.min(1,Math.max(.4,30/Math.max(acc,5)));lat=gs.sm.lat+(lat-gs.sm.lat)*a;lng=gs.sm.lng+(lng-gs.sm.lng)*a}
            }
            gs.sm={lat,lng};
            const accR=Number(acc.toFixed(1)),heading=c.heading==null||Number.isNaN(c.heading)?null:Number(c.heading.toFixed(1)),speed=c.speed==null?null:Number(c.speed.toFixed(1));
            mapEl.__me.clearLayers();
            L.marker([lat,lng],{icon:L.divIcon({className:'',html:`<div class='owpin' style='background:#007AFF'>🚴</div>`,iconSize:[36,36],iconAnchor:[18,18]})}).addTo(mapEl.__me).bindPopup('📍 موقعي الآن');
            if(acc<=15)L.circle([lat,lng],{radius:acc,color:'#007AFF',weight:1,fillOpacity:.08}).addTo(mapEl.__me);
            setBadge(`${acc<=25?'🟢':'🟡'} GPS • دقة ${accR} م`,acc<=25?'ok':'warn');
            gpsBtn.classList.add('on');gpsBtn.textContent=acc<=25?'🟢 GPS دقيق':'🟡 GPS';
            if(cfg.center_on_gps&&!mapEl.__firstGpsCenter){map.setView([lat,lng],16);mapEl.__firstGpsCenter=true}
            const movedSent=gs.lastSentPos?distanceM(gs.lastSentPos,[lat,lng]):999999;
            if(ts-gs.lastSent>=5000||movedSent>=12){gs.lastSent=ts;gs.lastSentPos=[lat,lng];fire('gps',{lat:Number(lat.toFixed(6)),lng:Number(lng.toFixed(6)),accuracy:accR,heading,speed,ts})}
          };
          const fail=e=>{const msg=e&&e.code===1?'تم رفض إذن الموقع':e&&e.code===2?'الموقع غير متاح':e&&e.code===3?'انتهت مهلة GPS':'تعذر تحديد الموقع';gpsBtn.classList.remove('on');gpsBtn.classList.add('warn');gpsBtn.textContent='📍 السماح بالموقع';setBadge('🟠 '+msg,'warn');fire('gps_status',{code:(e&&e.code)||0,message:msg})};
          const opts={enableHighAccuracy:true,maximumAge:0,timeout:20000};
          navigator.geolocation.getCurrentPosition(push,fail,opts);
          if(!mapEl.__watch){mapEl.__watch=navigator.geolocation.watchPosition(push,fail,opts)}
        };
        if(cfg.geolocation){gpsBtn.style.display='block';gpsBtn.onclick=geolocate;if(cfg.auto_request_gps&&!mapEl.__autoRequested){mapEl.__autoRequested=true;setTimeout(geolocate,400)}}else{gpsBtn.style.display='none'}
        root.querySelector('#owfit').onclick=()=>{mapEl.__userMoved=false;if(bounds.length)map.fitBounds(bounds,{padding:[42,42],maxZoom:15});else map.setView(cfg.center||[31.2001,29.9187],Number(cfg.zoom||12))};
        root.querySelector('#owfull').onclick=()=>{if(!document.fullscreenElement&&root.requestFullscreen)root.requestFullscreen().catch(()=>{});else if(document.exitFullscreen)document.exitFullscreen()};
        root.querySelector('#owshare').onclick=()=>{const s=cfg.selected||(cfg.route&&{lat:cfg.route.to[0],lng:cfg.route.to[1]});if(!s||s.lat==null){showStatus('حدد وجهة أولاً');return}const url=`https://www.google.com/maps/dir/?api=1&destination=${s.lat},${s.lng}`;if(navigator.share)navigator.share({title:'ONWAY',text:'وجهة ONWAY',url}).catch(()=>{});else if(navigator.clipboard)navigator.clipboard.writeText(url).then(()=>showStatus('تم نسخ رابط الملاحة'))};
        setTimeout(()=>map.invalidateSize(false),30);
      })();
      return ()=>{};
    }
    """
    MAP_COMPONENT = _component("onway_operational_map_v10", html=MAP_HTML, css=MAP_CSS, js=MAP_JS, isolate_styles=False)

    # صوت تنبيه مميز: يُفتح بأول لمسة على الصفحة (شرط المتصفحات) ثم يعمل تلقائياً
    NOTIFY_JS = r"""
    export default function(component){
      const {data}=component;
      if(!window.__owAudio){
        window.__owAudio={ctx:null};
        const unlock=()=>{try{const C=window.AudioContext||window.webkitAudioContext;if(!C)return;if(!window.__owAudio.ctx)window.__owAudio.ctx=new C();if(window.__owAudio.ctx.state==='suspended')window.__owAudio.ctx.resume()}catch(e){}};
        ['click','touchstart','keydown','pointerdown'].forEach(ev=>document.addEventListener(ev,unlock,{passive:true}));
      }
      const token=String((data&&data.token)||'');
      if(!data||!data.enabled||window.__onwayNotifyToken===token)return ()=>{};
      window.__onwayNotifyToken=token;
      try{
        const A=window.__owAudio;if(!A.ctx){const C=window.AudioContext||window.webkitAudioContext;if(!C)return ()=>{};A.ctx=new C()}
        const ctx=A.ctx;if(ctx.state==='suspended')ctx.resume();
        const kinds={new_order:{notes:[988,1319,988,1319,1760],dur:.17,rep:3,vib:[300,120,300,120,500]},status:{notes:[784,1047,1319],dur:.16,rep:1,vib:[200,100,200]}};
        const k=kinds[data.kind]||kinds.status;let t=ctx.currentTime+.05;
        const master=ctx.createGain();master.gain.value=.9;master.connect(ctx.destination);
        for(let r=0;r<k.rep;r++){
          for(const f of k.notes){
            [['triangle',f,.55],['square',f/2,.10]].forEach(([type,fr,vol])=>{
              const o=ctx.createOscillator(),g=ctx.createGain();o.type=type;o.frequency.value=fr;
              g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(vol,t+.015);g.gain.exponentialRampToValueAtTime(.0001,t+k.dur);
              o.connect(g);g.connect(master);o.start(t);o.stop(t+k.dur+.02);
            });
            t+=k.dur+.03;
          }
          t+=.28;
        }
        if(navigator.vibrate)navigator.vibrate(k.vib);
      }catch(e){}
      return ()=>{};
    }
    """
    NOTIFY_COMPONENT = _component("onway_notify_v2", html="<span id='ownotify' aria-hidden='true'></span>", css="#ownotify{display:none!important}", js=NOTIFY_JS, isolate_styles=False)

    DEVICE_JS = r"""
    export default function(component){
      const d=component.data||{};
      try{
        if(d.action==='set'&&d.token){
          document.cookie='onway_token='+d.token+'; max-age=7776000; path=/; SameSite=Lax'+(location.protocol==='https:'?'; Secure':'');
        }
        if(d.action==='clear'){document.cookie='onway_token=; max-age=0; path=/; SameSite=Lax'}
      }catch(e){}
      return ()=>{};
    }
    """
    DEVICE_COMPONENT = _component("onway_device_v1", html="<span id='owdevice' aria-hidden='true'></span>", css="#owdevice{display:none!important}", js=DEVICE_JS, isolate_styles=False)

    # غلاف التطبيق: يجعل الصفحة تتصرف كتطبيق موبايل (أيقونة، شاشة كاملة، زر تثبيت)
    SHELL_JS = r"""
    export default function(component){
      const d=component.data||{};const root=component.parentElement;const head=document.head;
      const meta=(n,c)=>{let m=document.querySelector('meta[name="'+n+'"]');if(!m){m=document.createElement('meta');m.name=n;head.appendChild(m)}m.content=c};
      meta('theme-color','#080A0D');meta('apple-mobile-web-app-capable','yes');meta('mobile-web-app-capable','yes');meta('apple-mobile-web-app-status-bar-style','black-translucent');meta('apple-mobile-web-app-title',d.name||'ONWAY');meta('format-detection','telephone=no');
      const vp=document.querySelector('meta[name="viewport"]');if(vp&&vp.content.indexOf('viewport-fit')<0)vp.content+=',viewport-fit=cover';
      const svg="<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 512 512'><rect width='512' height='512' rx='112' fill='"+(d.accent||'#FF5A00')+"'/><text x='256' y='330' font-size='230' font-family='Arial' font-weight='900' fill='white' text-anchor='middle'>ON</text></svg>";
      const icon='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg);
      const link=(rel,href,extra)=>{let l=document.querySelector('link[rel="'+rel+'"][data-onway]');if(!l){l=document.createElement('link');l.rel=rel;l.setAttribute('data-onway','1');head.appendChild(l)}l.href=href;if(extra)Object.keys(extra).forEach(k=>l.setAttribute(k,extra[k]))};
      link('icon',icon);link('apple-touch-icon',icon);
      try{const mf={name:d.name||'ONWAY',short_name:'ONWAY',start_url:location.pathname,scope:location.pathname,display:'standalone',orientation:'portrait',background_color:'#080A0D',theme_color:'#080A0D',dir:'rtl',lang:'ar',icons:[{src:icon,sizes:'any',type:'image/svg+xml',purpose:'any maskable'}]};
        if(!window.__owManifest||window.__owManifestName!==mf.name){window.__owManifestName=mf.name;window.__owManifest=URL.createObjectURL(new Blob([JSON.stringify(mf)],{type:'application/manifest+json'}));link('manifest',window.__owManifest)}}catch(e){}
      if(!document.getElementById('onway-shell-css')){const s=document.createElement('style');s.id='onway-shell-css';s.textContent='html,body{overscroll-behavior-y:contain;-webkit-tap-highlight-color:transparent}button,a{touch-action:manipulation}';head.appendChild(s)}
      const btn=root&&root.querySelector('#owinstall');if(!btn)return ()=>{};
      const standalone=window.matchMedia&&window.matchMedia('(display-mode: standalone)').matches||window.navigator.standalone;
      if(!window.__owInstallBound){window.__owInstallBound=true;window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();window.__owInstall=e;const b=document.getElementById('owinstall');if(b)b.style.display='block'})}
      if(!standalone){btn.style.display='block'}
      btn.onclick=async()=>{if(window.__owInstall){window.__owInstall.prompt();try{await window.__owInstall.userChoice}catch(e){}window.__owInstall=null;btn.style.display='none'}else{alert('لتثبيت التطبيق على الموبايل:\nآيفون: زر المشاركة ثم «إضافة إلى الشاشة الرئيسية».\nأندرويد (كروم): القائمة ⋮ ثم «تثبيت التطبيق» أو «إضافة إلى الشاشة الرئيسية».')}};
      return ()=>{};
    }
    """
    SHELL_COMPONENT = _component("onway_shell_v1", html="<button id='owinstall' type='button'>📲 تثبيت التطبيق</button>", css="#owinstall{display:none;position:fixed;top:64px;left:10px;z-index:9998;border:1px solid rgba(255,255,255,.14);background:rgba(14,17,22,.94);color:#fff;border-radius:999px;padding:8px 12px;font:800 11px Cairo,Arial;box-shadow:0 8px 22px rgba(0,0,0,.35);cursor:pointer}", js=SHELL_JS, isolate_styles=False)

    # مكوّن الصوت: ميكروفون للأوامر + نطق النتيجة
    VOICE_HTML = "<div id='owvoice'><button id='owvbtn' type='button'><span id='owvico'>🎙️</span><span id='owvtxt'>اضغط وتكلّم</span></button><div id='owvout'></div></div>"
    VOICE_CSS = """
    #owvoice{display:flex;flex-direction:column;align-items:center;gap:8px;margin:4px 0 12px;font-family:Cairo,Arial,sans-serif}
    #owvbtn{width:100%;max-width:520px;display:flex;align-items:center;justify-content:center;gap:10px;border:1px solid rgba(255,90,0,.5);background:linear-gradient(180deg,#FF7A33,#FF5A00);color:#fff;border-radius:22px;padding:18px 14px;font:900 17px Cairo,Arial;box-shadow:0 12px 30px rgba(255,90,0,.25);cursor:pointer;touch-action:manipulation}
    #owvbtn.on{background:linear-gradient(180deg,#00D488,#00A868);border-color:#00C27A;animation:owp 1.1s infinite}
    #owvico{font-size:26px}#owvout{color:#cfd6df;font:700 13px Cairo,Arial;min-height:20px;text-align:center;direction:rtl}
    @keyframes owp{0%{box-shadow:0 0 0 0 rgba(0,194,122,.5)}100%{box-shadow:0 0 0 22px rgba(0,194,122,0)}}
    """
    VOICE_JS = r"""
    export default function(component){
      const {data,setTriggerValue,parentElement}=component;const root=parentElement;if(!root)return ()=>{};
      const btn=root.querySelector('#owvbtn'),txt=root.querySelector('#owvtxt'),out=root.querySelector('#owvout');
      const d=data||{};
      if(d.speak&&d.token&&window.__owSpoken!==d.token){window.__owSpoken=d.token;try{if(window.speechSynthesis){const u=new SpeechSynthesisUtterance(String(d.speak));u.lang='ar-EG';u.rate=1;window.speechSynthesis.cancel();window.speechSynthesis.speak(u)}}catch(e){}}
      const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
      if(!SR){txt.textContent='المتصفح لا يدعم الصوت — اكتب الأمر';btn.disabled=true;return ()=>{}}
      btn.onclick=()=>{
        try{const sr=new SR();sr.lang='ar-EG';sr.interimResults=true;sr.maxAlternatives=1;sr.continuous=false;let final='';
          sr.onstart=()=>{btn.classList.add('on');txt.textContent='أسمعك… تكلّم الآن';out.textContent=''};
          sr.onresult=e=>{let t='';for(let i=e.resultIndex;i<e.results.length;i++){t+=e.results[i][0].transcript;if(e.results[i].isFinal)final=t}out.textContent=t};
          sr.onerror=e=>{btn.classList.remove('on');txt.textContent='اضغط وتكلّم';out.textContent=e.error==='not-allowed'?'اسمح للميكروفون من إعدادات المتصفح':'تعذر التقاط الصوت، حاول مرة أخرى'};
          sr.onend=()=>{btn.classList.remove('on');txt.textContent='اضغط وتكلّم';if(final.trim()){setTriggerValue('speech',JSON.stringify({text:final.trim(),ts:Date.now()}))}};
          sr.start();
        }catch(e){out.textContent='تعذر تشغيل الميكروفون'}
      };
      return ()=>{};
    }
    """
    VOICE_COMPONENT = _component("onway_voice_v1", html=VOICE_HTML, css=VOICE_CSS, js=VOICE_JS, isolate_styles=False)
except Exception:
    MAP_COMPONENT = None
    NOTIFY_COMPONENT = None
    DEVICE_COMPONENT = None
    SHELL_COMPONENT = None
    VOICE_COMPONENT = None


def mount_map(points=None, center=None, zoom=12, clickable=False, geolocation=False, route=None, key="map", selected=None, height=None, preserve_view=False, center_on_gps=False):
    cfg = {"points": points or [], "center": center or [31.2001, 29.9187], "zoom": zoom, "clickable": bool(clickable), "geolocation": bool(geolocation),
           "auto_request_gps": bool(geolocation and key.startswith("live_map_RIDER")), "center_on_gps": bool(center_on_gps), "route": route, "selected": selected, "preserveView": bool(preserve_view)}
    if MAP_COMPONENT:
        return MAP_COMPONENT(key=key, data=cfg)
    pts = [{"lat": p.get("lat"), "lon": p.get("lng")} for p in (points or []) if p.get("lat") is not None and p.get("lng") is not None]
    if pts:
        st.map(pd.DataFrame(pts), latitude="lat", longitude="lon", zoom=zoom, height=int(height or 520))
    else:
        st.info("الخريطة التفاعلية تحتاج نسخة Streamlit حديثة (1.46 أو أحدث).")
    return None


def geocode_address(query):
    query = query.strip()
    if not query: return None
    try:
        url = "https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&accept-language=ar&q=" + quote(query + ", Alexandria, Egypt")
        with urlopen(Request(url, headers={"User-Agent": "ONWAY-Delivery/10.0 (operations app)"}), timeout=8) as r:
            data = json.loads(r.read().decode("utf-8"))
        if data:
            return {"lat": round(float(data[0]["lat"]), 6), "lng": round(float(data[0]["lon"]), 6), "address": data[0].get("display_name", query)}
    except Exception:
        return None
    return None


# =========================================================
# وضع العمل + الجلسة + الدخول
# =========================================================
def _is_real_rider():
    return (st.session_state.get("user") or {}).get("role") == "RIDER"


def effective_user():
    base = st.session_state.get("user", {})
    if not base or base.get("role") != "OWNER": return base
    mode = st.session_state.get("workspace_role", "OWNER")
    out = dict(base); out["role"] = mode
    if mode == "RIDER":
        riders = df("SELECT id FROM riders WHERE status!='غير نشط' ORDER BY name")
        ids = riders["id"].tolist() if not riders.empty else []
        sel = st.session_state.get("workspace_rider_id")
        if sel not in ids: sel = ids[0] if ids else None
        st.session_state["workspace_rider_id"] = sel; out["ref_id"] = sel
    else:
        out["ref_id"] = base.get("ref_id")
    return out


def _on_workspace_rider_change():
    sel = st.session_state.get("workspace_rider_select")
    if sel is not None: st.session_state["workspace_rider_id"] = sel


def read_device_token():
    try:
        t = st.context.cookies.get("onway_token")
        if t: return t
    except Exception:
        pass
    try:
        t = st.query_params.get("t")
        return t if isinstance(t, str) else None
    except Exception:
        return None


def sync_device_cookie(action, token=None):
    if DEVICE_COMPONENT is not None:
        DEVICE_COMPONENT(key="device_cookie", data={"action": action, "token": token or ""})


def logout():
    drop_session(st.session_state.get("_token"))
    st.session_state.clear()
    st.session_state["_clear_cookie"] = True
    try: st.query_params.clear()
    except Exception: pass
    st.rerun()


def header(title, subtitle=""):
    user = effective_user() or {}
    st.markdown(f'<div class="app-topbar"><div class="app-brand"><div class="app-brand-mark">🧡</div><div>{esc(app_name())}</div></div><div class="user-chip"><span class="user-dot"></span>{esc(user.get("name", "زائر"))} • {role_label(user.get("role"))}</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="onway-hero"><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div>', unsafe_allow_html=True)


def metric_grid(items):
    st.markdown('<div class="metric-grid">' + ''.join(f'<div class="metric {kind or ""}"><div class="v">{esc(value)}</div><div class="l">{esc(label)}</div><div class="s">{esc(sub)}</div></div>' for label, value, sub, kind in items) + '</div>', unsafe_allow_html=True)


def create_owner():
    st.markdown(f'<div class="onway-hero"><h1>🧡 {APP_NAME}</h1><p>تهيئة المالك الأول — مرة واحدة فقط.</p></div>', unsafe_allow_html=True)
    with st.form("first_owner"):
        a, b = st.columns(2); name = a.text_input("اسم المالك"); email = b.text_input("البريد الإلكتروني").strip().lower()
        c, d = st.columns(2); p1 = c.text_input("PIN الدخول", type="password", max_chars=8); p2 = d.text_input("تأكيد PIN", type="password", max_chars=8)
        if st.form_submit_button("بدء النظام", type="primary", use_container_width=True):
            if not name or "@" not in email: st.error("اكتب الاسم والبريد بشكل صحيح.")
            elif not p1.isdigit() or len(p1) < 4 or p1 != p2: st.error("PIN يجب أن يكون أرقاماً من 4 إلى 8 أرقام ومتطابقاً.")
            else:
                u = uid("USR")
                with get_conn() as c2: c2.execute("INSERT INTO users(id,name,email,role,ref_id,pin_hash,active,created_at) VALUES (?,?,?,?,?,?,1,?)", (u, name.strip(), email, "OWNER", None, hash_pin(p1), now_iso()))
                audit(u, "create", "user", u, after={"name": name, "email": email, "role": "OWNER"})
                st.session_state.user = {"id": u, "name": name, "email": email, "role": "OWNER", "ref_id": None}; st.rerun()


def login():
    if df("SELECT id FROM users WHERE active=1").empty:
        create_owner(); return
    header("تسجيل الدخول", "ادخل مرة واحدة وسيبقى الحساب محفوظاً على هذا الجهاز حتى تسجل الخروج.")
    with st.form("login"):
        e = st.text_input("البريد الإلكتروني").strip().lower(); p = st.text_input("PIN", type="password", max_chars=8)
        remember = st.checkbox("تذكرني على هذا الجهاز", value=True)
        if st.form_submit_button("دخول", type="primary", use_container_width=True):
            wait = st.session_state.get("login_locked_until", 0) - time.time()
            if wait > 0:
                st.error(f"محاولات كثيرة. انتظر {int(wait)} ثانية."); return
            u = one("SELECT * FROM users WHERE lower(email)=? AND active=1", (e,))
            if u and verify_pin(p, u["pin_hash"]):
                st.session_state.user = {"id": u["id"], "name": u["name"], "email": u["email"], "role": u["role"], "ref_id": u["ref_id"]}
                st.session_state["workspace_role"] = u["role"]
                st.session_state.pop("_clear_cookie", None); st.session_state["login_fails"] = 0
                st.session_state.page = "rider" if u["role"] == "RIDER" else "dashboard"
                if remember:
                    tok = create_session(u["id"]); st.session_state["_token"] = tok
                    if DEVICE_COMPONENT is None:
                        try: st.query_params["t"] = tok
                        except Exception: pass
                audit(u["id"], "login", "user", u["id"]); st.rerun()
            else:
                n = st.session_state.get("login_fails", 0) + 1; st.session_state["login_fails"] = n
                if n >= 5: st.session_state["login_locked_until"] = time.time() + 60; st.session_state["login_fails"] = 0
                st.error("بيانات الدخول غير صحيحة.")


# =========================================================
# القائمة الرئيسية (بدل الأزرار الظاهرة في الصفحة)
# =========================================================
def _nav_menu_base(user):
    role = user["role"]
    if role == "OWNER": return [("🏠 الرئيسية", "dashboard"), ("📦 الطلبات", "orders"), ("🗺️ الخريطة الحية", "map"), ("🧭 مركز الملاحة", "navigation"), ("🚴 الطيارون", "riders"), ("💳 حساب الطيار", "rider_wallet"), ("🏪 المطاعم والفروع", "restaurants"), ("⏱️ الحضور والساعات", "attendance"), ("💰 القبض والمرتبات", "payroll"), ("🧾 التسويات والخزينة", "settlements"), ("📊 التحليل والأداء", "analysis"), ("👥 المستخدمون", "users"), ("🔐 أمان الحساب", "security"), ("⚙️ الإعدادات والأدوات", "tools"), ("🎙️ المساعد الذكي", "assistant")]
    if role == "DISPATCHER": return [("🏠 الرئيسية", "dashboard"), ("📦 الطلبات", "orders"), ("🗺️ الخريطة الحية", "map"), ("🚴 الطيارون", "riders"), ("🏪 المطاعم والفروع", "restaurants"), ("🔐 أمان الحساب", "security")]
    if role == "ACCOUNTANT": return [("🏠 الرئيسية", "dashboard"), ("📦 الطلبات", "orders"), ("🗺️ الخريطة الحية", "map"), ("⏱️ الحضور والساعات", "attendance"), ("💰 القبض والمرتبات", "payroll"), ("🧾 التسويات والخزينة", "settlements"), ("📊 التحليل والأداء", "analysis"), ("🔐 أمان الحساب", "security"), ("⚙️ الأدوات", "tools")]
    if role == "RIDER": return [("🛵 مهمتي الآن", "rider"), ("📦 طلباتي", "orders"), ("💳 حسابي المالي", "rider_wallet"), ("⏱️ الحضور والساعات", "attendance"), ("🔐 أمان الحساب", "security")]
    return [("🏠 الرئيسية", "dashboard"), ("📦 طلبات المطعم", "orders"), ("🗺️ خريطة المطعم", "map")]


def nav_menu(user):
    m = _nav_menu_base(user)
    if user["role"] == "OWNER": return m
    hidden = {x for x in (get_setting("hidden_pages", "") or "").split(",") if x}
    return [x for x in m if x[1] not in hidden] or m[:1]


def goto(page, **flags):
    st.session_state.page = page
    for k, v in flags.items(): st.session_state[k] = v
    st.rerun()


def menu_bar(user):
    base = st.session_state.user
    menu = nav_menu(user)
    current = st.session_state.get("page", menu[0][1])
    if current not in [m[1] for m in menu]: current = menu[0][1]; st.session_state.page = current
    curlabel = next(l for l, k in menu if k == current)
    quick = user["role"] in ("OWNER", "DISPATCHER")
    cols = st.columns([3, 2] if quick else [1], gap="small")
    with cols[0].popover(f"☰  {curlabel}", use_container_width=True):
        st.caption("القائمة الرئيسية")
        for label, key in menu:
            if st.button(label, key=f"nav_{key}", type="primary" if current == key else "secondary", use_container_width=True): goto(key)
        st.divider()
        if base["role"] == "OWNER":
            st.caption("🔄 مساحة العمل (بدون تسجيل خروج)")
            cur = st.session_state.get("workspace_role", "OWNER")
            for code, label in [("OWNER", "👑 المالك"), ("DISPATCHER", "🎯 الديسباتشر"), ("RIDER", "🚴 الطيار"), ("ACCOUNTANT", "💰 الحسابات")]:
                if st.button(label, key=f"workspace_{code}", type="primary" if cur == code else "secondary", use_container_width=True):
                    st.session_state["workspace_role"] = code; goto("rider" if code == "RIDER" else "dashboard")
            if cur == "RIDER":
                riders = df("SELECT id,name FROM riders WHERE status!='غير نشط' ORDER BY name")
                if riders.empty: st.warning("لا يوجد طيارون نشطون.")
                else:
                    ids = riders["id"].tolist(); idx = ids.index(st.session_state.get("workspace_rider_id")) if st.session_state.get("workspace_rider_id") in ids else 0
                    st.selectbox("واجهة أي طيار؟", riders["name"].tolist(), index=idx, key="workspace_rider_select", on_change=_on_workspace_rider_change)
            st.divider()
        snd = st.session_state.get("sound_enabled", True)
        if st.button("🔔 صوت التنبيهات: مفعّل" if snd else "🔕 صوت التنبيهات: متوقف", key="menu_sound", use_container_width=True):
            st.session_state.sound_enabled = not snd; st.rerun()
        if st.button("🔊 تجربة الصوت", key="menu_sound_test", use_container_width=True):
            st.session_state["_test_sound"] = True
        if st.button("🚪 تسجيل الخروج", key="menu_logout", use_container_width=True): logout()
    if quick:
        with cols[1].popover("⚡ إجراءات", use_container_width=True):
            if st.button("＋ طلب جديد", key="q_order", type="primary", use_container_width=True): goto("orders", open_new_order=True)
            if st.button("🗺️ الخريطة الحية", key="q_map", use_container_width=True): goto("map")
            if actor_is_owner(user):
                if st.button("🧭 الملاحة", key="q_nav", use_container_width=True): goto("navigation")
                if st.button("＋ مطعم", key="q_rest", use_container_width=True): goto("restaurants", quick_add_restaurant=True)
                if st.button("＋ فرع", key="q_branch", use_container_width=True): goto("restaurants", quick_add_branch=True)
                if st.button("＋ طيار", key="q_rider", use_container_width=True): goto("riders", quick_add_rider=True)
    if st.session_state.pop("_test_sound", False):
        st.session_state["_sound_nonce"] = st.session_state.get("_sound_nonce", 0) + 1
        notify_user(user, "new_order", suffix=f"test{st.session_state['_sound_nonce']}", force=True)


# =========================================================
# التنبيهات الصوتية الحية
# =========================================================
def notify_user(user, kind="status", suffix="", force=False):
    if NOTIFY_COMPONENT is None or not (force or st.session_state.get("sound_enabled", True)):
        return
    NOTIFY_COMPONENT(key=f"notify_{user['id']}_{suffix or 'live'}", data={"enabled": True, "kind": kind, "token": f"{kind}|{time.time()}"})


@st.fragment(run_every="3s")
def live_notifications_fragment(user):
    role = user.get("role")
    if role not in ("OWNER", "DISPATCHER", "RIDER"): return
    key = f"live_notify_{user['id']}_{role}"
    if role == "RIDER":
        row = one("SELECT COUNT(*) n, COALESCE(GROUP_CONCAT(id||status),'') sig FROM orders WHERE rider_id=? AND status NOT IN ('تم التسليم','ملغى')", (user.get("ref_id"),)) or {"n": 0, "sig": ""}
        snap = f"{row['n']}|{row['sig']}"; prev = st.session_state.get(key); st.session_state[key] = snap
        if prev is not None and snap != prev and int(row["n"]) >= int(prev.split("|")[0]):
            st.toast("🔔 تم توجيه/تحديث طلب لك", icon="🧡"); notify_user(user, "new_order")
    else:
        row = one("SELECT COUNT(*) n, COALESCE(SUM(CASE WHEN status='جديد' THEN 1 ELSE 0 END),0) fresh, COALESCE(MAX(COALESCE(delivered_at,picked_up_at,accepted_at,created_at)),'') stamp FROM orders WHERE created_at>=?", ((now_dt() - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),)) or {"n": 0, "fresh": 0, "stamp": ""}
        snap = f"{row['n']}|{row['fresh']}|{row['stamp']}"; prev = st.session_state.get(key); st.session_state[key] = snap
        if prev is not None and snap != prev:
            if int(row["n"]) > int(prev.split("|")[0]): st.toast("🔔 يوجد طلب جديد يحتاج تدخلاً", icon="🧡"); notify_user(user, "new_order")
            elif row["stamp"] != prev.split("|", 2)[-1]: st.toast("🔔 تم تحديث حالة طلب", icon="🧡"); notify_user(user, "status")


# =========================================================
# الخرائط الحية
# =========================================================
def map_points_for(user):
    points = []
    def order_pts(q, params=()):
        for _, o in df(q, params).iterrows():
            points.append({"id": o["id"], "kind": "order", "icon": "📦", "lat": o["delivery_lat"], "lng": o["delivery_lng"], "online": True, "title": o["order_no"], "meta": f"{o['status']} • {o['delivery_address']}"})
    base_q = "SELECT id,order_no,status,delivery_address,delivery_lat,delivery_lng FROM orders WHERE status NOT IN ('تم التسليم','ملغى') AND delivery_lat IS NOT NULL AND delivery_lng IS NOT NULL"
    if user["role"] in ("OWNER", "DISPATCHER", "ACCOUNTANT"):
        for _, r in df("SELECT id,name,status,active_orders,last_lat,last_lng,gps_accuracy,last_gps_at FROM riders WHERE status!='غير نشط' AND last_lat IS NOT NULL AND last_lng IS NOT NULL").iterrows():
            points.append({"id": r["id"], "kind": "rider", "icon": "🚴", "lat": r["last_lat"], "lng": r["last_lng"], "online": gps_fresh(r.to_dict()), "accuracy": None if pd.isna(r["gps_accuracy"]) else r["gps_accuracy"], "title": r["name"], "meta": f"{r['status']} • {int(r['active_orders'])} طلبات • {r['last_gps_at'] or 'لا يوجد'}"})
        order_pts(base_q)
    elif user["role"] == "RIDER":
        r = one("SELECT * FROM riders WHERE id=?", (user["ref_id"],))
        if r and r["last_lat"] is not None: points.append({"id": "self", "kind": "self", "icon": "🚴", "lat": r["last_lat"], "lng": r["last_lng"], "online": gps_fresh(r), "title": "موقعي", "meta": f"دقة {r['gps_accuracy'] or '—'} م"})
        order_pts(base_q + " AND rider_id=?", (user["ref_id"],))
    elif user["role"] == "RESTAURANT":
        for _, b in branches_for(user["ref_id"], False).iterrows():
            if b["lat"] is not None: points.append({"id": b["id"], "kind": "branch", "icon": "🏪", "lat": b["lat"], "lng": b["lng"], "online": True, "title": b["name"], "meta": b["address"] or "فرع المطعم"})
        order_pts(base_q + " AND restaurant_id=?", (user["ref_id"],))
    return points


def _payload(result, name):
    v = getattr(result, name, None)
    if not v: return None
    try: return json.loads(v)
    except Exception: return None


@st.fragment(run_every="5s")
def live_map_fragment(user, navigation=False, route=None):
    points = map_points_for(user)
    result = mount_map(points, center=[31.2001, 29.9187], zoom=12, clickable=navigation, geolocation=(navigation or _is_real_rider()), route=route,
                       key="live_map_navigation" if navigation else f"live_map_{user['role']}", selected=st.session_state.get("map_selection") if navigation else None)
    if not result: return
    for name in ("map_click", "search_result"):
        p = _payload(result, name)
        if p and navigation:
            st.session_state.map_selection = p
            try: st.rerun(scope="fragment")
            except Exception: st.rerun()
    gps = _payload(result, "gps")
    if gps:
        acc = _num(gps.get("accuracy"))
        if user["role"] == "RIDER" and _is_real_rider() and (acc is None or acc <= 120):
            if gps.get("ts") != st.session_state.get("last_gps_ts"):
                st.session_state.last_gps_ts = gps.get("ts")
                rid = user["ref_id"]; lat = float(gps["lat"]); lng = float(gps["lng"]); stamp = now_iso()
                with get_conn() as c:
                    c.execute("UPDATE riders SET last_lat=?,last_lng=?,gps_accuracy=?,heading=?,speed=?,last_gps_at=? WHERE id=?", (lat, lng, acc, gps.get("heading"), gps.get("speed"), stamp, rid))
                    c.execute("INSERT INTO gps_log(rider_id,lat,lng,accuracy,heading,speed,recorded_at) VALUES (?,?,?,?,?,?,?)", (rid, lat, lng, acc, gps.get("heading"), gps.get("speed"), stamp))
        elif navigation:
            st.session_state.navigation_origin = gps
    rm = _payload(result, "route_meta")
    if rm: st.session_state.route_meta = rm
    gst = _payload(result, "gps_status")
    if gst:
        st.session_state.gps_status = gst
        if gst.get("code") == 1 and _is_real_rider():
            st.warning("📍 إذن الموقع مرفوض. اسمح للموقع من إعدادات المتصفح ثم اضغط «السماح بالموقع» — بدونه لن تستطيع الإدارة رؤية موقعك.")


def render_live_map(user):
    header("الخريطة الحية", "الأسطول والطلبات النشطة أمامك • 🟢 GPS حديث • ⚪ GPS قديم • 📦 طلب نشط")
    live_map_fragment(user)


def render_navigation_center(user):
    header("مركز الملاحة", "اختر أي وجهة من الطلبات أو الفروع أو الطيارين أو انقر على الخريطة مباشرة.")
    st.session_state.setdefault("map_selection", {})
    target_type = st.selectbox("مصدر الوجهة", ["من الخريطة", "طلب", "فرع", "طيار"], key="nav_type")
    target = None
    if target_type == "طلب":
        o = df("SELECT id,order_no,delivery_address,delivery_lat,delivery_lng FROM orders WHERE delivery_lat IS NOT NULL ORDER BY created_at DESC LIMIT 300")
        if not o.empty:
            sel = st.selectbox("الطلب", o["order_no"].tolist()); x = o[o["order_no"] == sel].iloc[0]
            target = {"lat": x["delivery_lat"], "lng": x["delivery_lng"], "address": x["delivery_address"], "title": sel}
    elif target_type == "فرع":
        b = df("SELECT b.*,r.name restaurant FROM branches b JOIN restaurants r ON r.id=b.restaurant_id WHERE b.lat IS NOT NULL ORDER BY r.name,b.name")
        if not b.empty:
            names = [f"{x['restaurant']} — {x['name']}" for _, x in b.iterrows()]; sel = st.selectbox("الفرع", names); x = b.iloc[names.index(sel)]
            target = {"lat": x["lat"], "lng": x["lng"], "address": x["address"], "title": sel}
    elif target_type == "طيار":
        r = df("SELECT id,name,last_lat,last_lng,status FROM riders WHERE last_lat IS NOT NULL ORDER BY name")
        if not r.empty:
            sel = st.selectbox("الطيار", r["name"].tolist()); x = r[r["name"] == sel].iloc[0]
            target = {"lat": x["last_lat"], "lng": x["last_lng"], "address": f"موقع الطيار — {x['status']}", "title": x["name"]}
    else:
        q = st.text_input("بحث عن أي وجهة", placeholder="اكتب شارعاً أو منطقة أو مكاناً")
        if st.button("تحديد من البحث", use_container_width=True):
            g = geocode_address(q)
            if g: st.session_state.map_selection = g; st.success("تم تحديد الوجهة.")
            else: st.error("لم يتم العثور على الوجهة.")
    if target: st.session_state.map_selection = target
    live_map_fragment(user, navigation=True)
    sel = st.session_state.get("map_selection") or {}
    if sel.get("lat") is not None:
        st.success(f"الوجهة الحالية: {sel.get('title') or 'نقطة محددة'} — {sel.get('address', '')}")
        origin = st.session_state.get("navigation_origin")
        url = f"https://www.google.com/maps/dir/?api=1&destination={sel['lat']},{sel['lng']}" + (f"&origin={origin['lat']},{origin['lng']}" if origin and origin.get("lat") is not None else "")
        st.link_button("🧭 ابدأ الملاحة", url, use_container_width=True)
        if st.button("مسح الوجهة", use_container_width=True): st.session_state.map_selection = {}; st.rerun()


# =========================================================
# مظهر عصري + شريط تنقل سفلي كتطبيق الموبايل
# =========================================================
THEME_CSS = """
:root{--brand:__ACC__;--brand2:__ACC2__;--brandSoft:rgba(__RGB__,.14);--shadowBrand:0 12px 30px rgba(__RGB__,.24)}
html{scroll-behavior:smooth}
@keyframes owFade{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.block-container>div>div{animation:owFade .28s ease both}
[data-testid="stAppViewContainer"]{background:radial-gradient(1200px 500px at 85% -10%,rgba(__RGB__,.10),transparent 60%),radial-gradient(900px 400px at 0% 0%,rgba(77,163,255,.05),transparent 55%),#080A0D!important}
.app-topbar{position:sticky;top:6px;z-index:50;backdrop-filter:blur(18px);background:rgba(15,18,23,.82)!important}
.onway-hero{position:relative;overflow:hidden;border-radius:22px!important}
.onway-hero:after{content:"";position:absolute;left:-40px;top:-40px;width:150px;height:150px;background:radial-gradient(circle,rgba(__RGB__,.22),transparent 70%)}
.metric{border-radius:18px!important;transition:transform .16s ease,border-color .16s ease;backdrop-filter:blur(6px)}
.metric:hover{transform:translateY(-2px);border-color:rgba(__RGB__,.4)!important}
.metric .v{letter-spacing:-.2px}
.stButton>button,.stDownloadButton>button,.stLinkButton>a{border-radius:15px!important;letter-spacing:.1px}
.stButton>button:active{transform:scale(.97)!important}
[data-testid="stExpander"],[data-testid="stForm"],[data-testid="stVerticalBlockBorderWrapper"]{border-radius:18px!important}
[data-testid="stVerticalBlockBorderWrapper"]{border-color:#242B35!important;background:linear-gradient(180deg,rgba(17,21,27,.9),rgba(12,15,19,.9))}
.rider-order{border-radius:24px!important}
.status-pill{letter-spacing:.2px}
.block-container{padding-bottom:7rem!important}
.st-key-bottom_nav{position:fixed;bottom:0;left:0;right:0;z-index:999;background:rgba(9,12,16,.9);backdrop-filter:blur(22px) saturate(1.4);border-top:1px solid #242B35;padding:6px 8px calc(6px + env(safe-area-inset-bottom))}
.st-key-bottom_nav [data-testid="stHorizontalBlock"]{flex-direction:row!important;flex-wrap:nowrap!important;gap:4px!important}
.st-key-bottom_nav [data-testid="stColumn"],.st-key-bottom_nav [data-testid="column"]{min-width:0!important;flex:1 1 0!important;width:auto!important}
.st-key-bottom_nav button{min-height:54px!important;padding:2px 3px!important;font-size:.66rem!important;line-height:1.35!important;white-space:normal!important;border-radius:16px!important;background:transparent!important;border:1px solid transparent!important;color:#9AA4B2!important;box-shadow:none!important}
.st-key-bottom_nav button[kind="primary"]{background:var(--brandSoft)!important;border-color:rgba(__RGB__,.35)!important;color:var(--brand2)!important;box-shadow:none!important}
@media(min-width:900px){.st-key-bottom_nav{left:50%;right:auto;transform:translateX(-50%);width:600px;bottom:14px;border:1px solid #2A313C;border-radius:24px;box-shadow:0 18px 50px rgba(0,0,0,.5)}}
"""


def _hex_rgb(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def _lighten(h, f=.22): return "#%02X%02X%02X" % tuple(int(c + (255 - c) * f) for c in _hex_rgb(h))


def accent():
    a = get_setting("ui_accent", "#FF5A00") or "#FF5A00"
    return a if re.fullmatch(r"#[0-9a-fA-F]{6}", a) else "#FF5A00"


def inject_theme():
    a = accent(); r, g, b = _hex_rgb(a)
    st.markdown("<style>" + THEME_CSS.replace("__ACC2__", _lighten(a)).replace("__ACC__", a).replace("__RGB__", f"{r},{g},{b}") + "</style>", unsafe_allow_html=True)
    if SHELL_COMPONENT is not None: SHELL_COMPONENT(key="app_shell", data={"accent": a, "name": app_name()})


def bottom_nav(user):
    role = user["role"]; cur = st.session_state.get("page")
    if role == "RIDER": items = [("🛵", "مهمتي", "rider"), ("📦", "طلباتي", "orders"), ("💳", "حسابي", "rider_wallet"), ("⏱️", "الحضور", "attendance")]
    elif role == "RESTAURANT": items = [("🏠", "الرئيسية", "dashboard"), ("📦", "الطلبات", "orders"), ("🗺️", "الخريطة", "map")]
    else: items = [("🏠", "الرئيسية", "dashboard"), ("📦", "الطلبات", "orders"), ("🗺️", "الخريطة", "map"), ("🚴", "الطيارون", "riders"), ("🎙️", "المساعد", "assistant")]
    allowed = {k for _, k in nav_menu(user)}; items = [i for i in items if i[2] in allowed]
    if len(items) < 2: return
    with st.container(key="bottom_nav"):
        for col, (ic, lb, k) in zip(st.columns(len(items), gap="small"), items):
            if col.button(f"{ic} {lb}", key=f"bn_{k}", type="primary" if cur == k else "secondary", use_container_width=True): goto(k)


# =========================================================
# لوحة التحكم
# =========================================================
ACTIVE_STATUSES = ["جديد", "تم التعيين", "تم القبول", "تم الاستلام", "في الطريق"]
ORDER_COLS = {"order_no": "الطلب", "restaurant": "المطعم", "branch": "الفرع", "status": "الحالة", "billing_mode": "التحصيل", "rider": "الطيار", "delivery_address": "العنوان", "distance_km": "كم", "delivery_fee": "الخدمة", "rider_commission": "عمولة الطيار", "created_at": "الوقت"}


def dashboard_data():
    o = df("SELECT * FROM orders WHERE substr(created_at,1,10)=?", (today_str(),))
    done_mask = o["status"] == "تم التسليم" if not o.empty else None
    overdue = 0
    grace = int(float(get_setting("order_overdue_grace_minutes", 15)))
    if not o.empty:
        for row in o[o["status"].isin(ACTIVE_STATUSES[1:])].to_dict("records"):
            try:
                if row.get("eta_minutes") and now_dt() > parse_ts(row["created_at"]) + timedelta(minutes=int(row["eta_minutes"]) + grace): overdue += 1
            except Exception: pass
    credit_due = float(df("SELECT COALESCE(SUM(o.delivery_fee-COALESCE((SELECT SUM(si.amount) FROM settlement_items si WHERE si.order_id=o.id),0)),0) x FROM orders o WHERE o.billing_mode='آجل' AND o.status='تم التسليم'")["x"][0])
    return {"total": len(o), "cash": int((o["billing_mode"] == "كاش").sum()) if not o.empty else 0, "credit": int((o["billing_mode"] == "آجل").sum()) if not o.empty else 0,
            "done": int(done_mask.sum()) if not o.empty else 0, "service": float(o.loc[done_mask, "delivery_fee"].sum()) if not o.empty else 0.0,
            "commissions": float(o.loc[done_mask, "rider_commission"].sum()) if not o.empty else 0.0,
            "active": int(o["status"].isin(ACTIVE_STATUSES).sum()) if not o.empty else 0, "overdue": overdue, "credit_due": credit_due, "treasury": treasury_balance()}


def render_dashboard(user):
    if user["role"] == "RIDER": return render_rider(user)
    if user["role"] == "RESTAURANT":
        rs = df("SELECT * FROM orders WHERE restaurant_id=? ORDER BY created_at DESC LIMIT 100", (user["ref_id"],))
        header("لوحة المطعم", "حالة الطلبات والحساب في مساحة بسيطة.")
        active = int(rs["status"].isin(ACTIVE_STATUSES).sum()) if not rs.empty else 0
        due = float(df("SELECT COALESCE(SUM(o.delivery_fee-COALESCE((SELECT SUM(si.amount) FROM settlement_items si WHERE si.order_id=o.id),0)),0) x FROM orders o WHERE o.restaurant_id=? AND o.billing_mode='آجل' AND o.status='تم التسليم'", (user["ref_id"],))["x"][0])
        metric_grid([("إجمالي الطلبات", len(rs), "آخر السجلات", "info"), ("قيد التنفيذ", active, "نشطة", "info"), ("تم التسليم", int((rs["status"] == "تم التسليم").sum()) if not rs.empty else 0, "مكتملة", "good"), ("آجل مستحق", f"{due:,.2f} ج", "جاهز للتسوية", "warn")])
        live_map_fragment(user)
        if not rs.empty: st.dataframe(rs[["order_no", "status", "billing_mode", "delivery_address", "delivery_fee", "created_at"]].rename(columns={"order_no": "الطلب", "status": "الحالة", "billing_mode": "التحصيل", "delivery_address": "العنوان", "delivery_fee": "خدمة التوصيل", "created_at": "الوقت"}), use_container_width=True, hide_index=True)
        return
    d = dashboard_data()
    header("غرفة العمليات", "هذه الشاشة تقول لك أين تحتاج أن تتدخل الآن.")
    metric_grid([("طلبات اليوم", d["total"], f"كاش {d['cash']} • آجل {d['credit']}", "info"), ("قيد التنفيذ", d["active"], "في الميدان", "info"), ("تحتاج تدخل", d["overdue"], "متأخرة", "danger" if d["overdue"] else "good"),
                 ("تم التسليم", d["done"], f"رسوم خدمة {d['service']:,.0f} ج", "good"), ("آجل مستحق", f"{d['credit_due']:,.0f} ج", "يحتاج تحصيل", "warn"), ("الخزينة", f"{d['treasury']:,.0f} ج", f"دخل اليوم {cash_receipts_today():,.0f} ج", "good")])
    if d["overdue"]:
        st.markdown(f'<div class="cockpit-alert" style="border-color:rgba(255,77,77,.35);background:rgba(255,77,77,.07)"><b>🔴 {d["overdue"]} طلب يحتاج تدخلك الآن</b><br><span>افتح الطلبات لتغيير الطيار ومعالجة التأخير.</span></div>', unsafe_allow_html=True)
    hold = riders_cash_holding(); limit = float(get_setting("cash_limit", 1500))
    if not hold.empty:
        over = hold[hold["net"] >= limit]
        for _, h in over.iterrows():
            st.markdown(f'<div class="cockpit-alert" style="border-color:rgba(255,176,32,.4);background:rgba(255,176,32,.07)"><b>💵 {esc(h["name"])} معه كاش {h["net"]:,.0f} ج لم يُورَّد</b><br><span>{int(h["n"])} طلب — تجاوز حد التنبيه ({limit:,.0f} ج). صفِّ حسابه من التسويات.</span></div>', unsafe_allow_html=True)
    left, right = st.columns([1.55, 1], gap="small")
    with left:
        st.markdown('<div class="section-title">🗺️ الخريطة الحية</div><div class="section-sub">موقع الطيارين والطلبات النشطة • يتحدث كل 5 ثوانٍ</div>', unsafe_allow_html=True)
        live_map_fragment(user)
    with right:
        st.markdown('<div class="section-title">⚡ حالة الأسطول</div>', unsafe_allow_html=True)
        rs = df("SELECT name,status,active_orders,last_gps_at FROM riders WHERE status!='غير نشط' ORDER BY active_orders DESC,name")
        if rs.empty: st.info("لا يوجد طيارون نشطون.")
        for _, r in rs.head(10).iterrows():
            fresh = gps_fresh(r.to_dict()); last = r["last_gps_at"] if isinstance(r["last_gps_at"], str) else "لم يسجل موقعاً"
            st.markdown(f'<div class="cockpit-alert"><b>🚴 {esc(r["name"])}</b> &nbsp; {badge(r["status"], "green" if r["status"] == "متاح" else "blue")}<br><span>{"🟢 GPS" if fresh else "⚪ GPS قديم"} • {int(r["active_orders"])} طلبات • {esc(last)}</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📦 الطلبات النشطة</div>', unsafe_allow_html=True)
    o = df("SELECT o.order_no,r.name restaurant,b.name branch,o.status,o.billing_mode,COALESCE(ry.name,'—') rider,o.delivery_address,o.distance_km,o.delivery_fee,o.rider_commission,o.created_at FROM orders o JOIN restaurants r ON r.id=o.restaurant_id JOIN branches b ON b.id=o.branch_id LEFT JOIN riders ry ON ry.id=o.rider_id WHERE o.status NOT IN ('تم التسليم','ملغى') ORDER BY o.created_at DESC LIMIT 60")
    if o.empty: st.success("✅ لا توجد طلبات مفتوحة الآن.")
    else: st.dataframe(o.rename(columns=ORDER_COLS), use_container_width=True, hide_index=True)


# =========================================================
# الطلبات
# =========================================================
def render_new_order_form(user):
    rs = active_restaurants()
    if rs.empty: st.warning("أضف مطعماً نشطاً أولاً."); return
    rn = st.selectbox("المطعم", rs["name"].tolist(), key="ord_rest"); rrow = rs[rs["name"] == rn].iloc[0]; rid = rrow["id"]
    bs = branches_for(rid)
    if bs.empty: st.warning("أضف فرعاً نشطاً لهذا المطعم أولاً."); return
    bn = st.selectbox("الفرع", bs["name"].tolist(), key="ord_branch"); br = bs[bs["name"] == bn].iloc[0].to_dict()
    point = st.session_state.setdefault("order_point", {})
    center = [float(br["lat"]), float(br["lng"])]
    route = {"from": center, "to": [point["lat"], point["lng"]]} if point.get("lat") is not None else None
    st.caption("📍 اضغط على الخريطة (أو ابحث) لتحديد موقع العميل — تُحسب المسافة والمسار تلقائياً.")
    res = mount_map(points=[{"id": br["id"], "kind": "branch", "icon": "🏪", "lat": br["lat"], "lng": br["lng"], "online": True, "title": bn, "meta": br.get("address") or ""}], center=center, zoom=14, clickable=True, route=route, key="new_order_map")
    click = _payload(res, "map_click") or _payload(res, "search_result") if res else None
    rm = _payload(res, "route_meta") if res else None
    if rm: st.session_state["order_distance"] = round(rm["distance_m"] / 1000, 2)
    if click and click != st.session_state.get("_last_click"):
        st.session_state["_last_click"] = click; st.session_state.order_point = click; st.rerun()
    point = st.session_state.order_point
    st.session_state.setdefault("new_order_no", next_order_no())
    a, b = st.columns(2); order_no = a.text_input("رقم الطلب", key="new_order_no"); address = b.text_input("عنوان التسليم", value=point.get("address", ""))
    a, b = st.columns(2); cname = a.text_input("اسم العميل (اختياري)"); cphone = b.text_input("هاتف العميل (اختياري)")
    c, d, e = st.columns(3)
    distance = c.number_input("المسافة (كم)", min_value=0.0, value=float(st.session_state.get("order_distance", 3.0)), step=.1)
    eta = d.number_input("الوقت المتوقع (دقيقة)", min_value=0, value=25, step=1)
    billing = e.selectbox("التحصيل", ["كاش", "آجل"], index=0 if rrow["billing_mode"] == "كاش" else 1)
    f, g, h = st.columns(3); fee = f.number_input("رسوم خدمة التوصيل (مقترحة من المسافة)", min_value=0.0, value=suggested_fee(distance), step=1.0); reward = g.number_input("مكافأة للطيار", min_value=0.0, value=0.0, step=1.0); discount = h.number_input("خصم", min_value=0.0, value=0.0, step=1.0)
    rr = ranked_riders(br.get("lat"), br.get("lng")); labels = ["تعيين لاحقاً"]; ids = [None]
    for _, r in rr.iterrows(): labels.append(f"{r['name']} — {int(r['active_orders'])} طلب" + (" 🟢" if gps_fresh(r.to_dict()) else "")); ids.append(r["id"])
    sel = st.selectbox("الطيار — الأنسب أولاً (الأقرب والأقل طلبات)", labels); rider_id = ids[labels.index(sel)]
    comm = commission_for_order(distance, fee, rider_row(rider_id))
    mode_txt = PAY_MODES[rider_terms(rider_row(rider_id))["mode"]] if rider_id else "النظام الافتراضي"
    st.markdown(f'<div class="highlight"><b>عمولة الطيار:</b> {comm:,.2f} ج • <b>حصة الشركة:</b> {fee - comm:,.2f} ج<br><span style="color:#9AA4B2;font-size:.7rem">{esc(mode_txt)}</span></div>', unsafe_allow_html=True)
    notes = st.text_area("ملاحظات")
    if st.button("🚀 إنشاء الطلب", type="primary", use_container_width=True):
        try:
            create_order({"order_no": order_no, "restaurant_id": rid, "branch_id": br["id"], "delivery_address": address, "delivery_lat": point.get("lat"), "delivery_lng": point.get("lng"), "distance_km": distance, "eta_minutes": eta, "billing_mode": billing, "rider_id": rider_id, "delivery_fee": fee, "reward": reward, "discount": discount, "notes": notes, "customer_phone": cphone, "customer_name": cname}, user)
            for k in ("order_point", "order_distance", "new_order_no", "_last_click"): st.session_state.pop(k, None)
            st.success("تم إنشاء الطلب بنجاح."); st.rerun()
        except Exception as ex: st.error(str(ex))


def render_order_detail(o, user):
    role = user["role"]; closed = not order_active(o["status"])
    metric_grid([("الحالة", o["status"], o["rider"], "info"), ("رسوم الخدمة", f"{o['delivery_fee']:,.2f} ج", o["billing_mode"], "good"), ("عمولة الطيار", f"{o['rider_commission']:,.2f} ج", f"{o['distance_km']} كم", "warn"), ("حصة الشركة", f"{o['delivery_fee'] - o['rider_commission']:,.2f} ج", "بعد عمولة الطيار", "good")])
    if role in ("OWNER", "DISPATCHER") and not closed:
        rr = available_riders(); names = ["بدون طيار"] + (rr["name"].tolist() if not rr.empty else [])
        cur = o["rider"] if o["rider"] in names else "بدون طيار"
        sel = st.selectbox("تعيين الطيار", names, index=names.index(cur), key=f"assign_{o['id']}")
        if st.button("حفظ التعيين", key=f"assign_btn_{o['id']}", use_container_width=True):
            try: assign_rider(o["id"], None if sel == "بدون طيار" else rr[rr["name"] == sel].iloc[0]["id"], user); st.success("تم تحديث التعيين."); st.rerun()
            except Exception as ex: st.error(str(ex))
    if role in ("OWNER", "DISPATCHER") and not closed:
        if st.button("⚡ تعيين الأنسب تلقائياً (الأقرب والأقل طلبات)", key=f"auto_{o['id']}", use_container_width=True):
            try:
                bp = one("SELECT lat,lng FROM branches WHERE id=?", (o["branch_id"],)) or {}
                rr = ranked_riders(bp.get("lat"), bp.get("lng"))
                if rr.empty: raise ValueError("لا يوجد طيارون متاحون.")
                assign_rider(o["id"], rr.iloc[0]["id"], user); st.success(f"تم التعيين للطيار {rr.iloc[0]['name']}"); st.rerun()
            except Exception as ex: st.error(str(ex))
    allowed = transitions(o["status"])
    if role == "RIDER": allowed = [a for a in allowed if a != "ملغى"]
    if role == "RESTAURANT": allowed = [a for a in allowed if a == "ملغى"]
    if allowed and role in ("OWNER", "DISPATCHER", "RIDER", "RESTAURANT"):
        action = st.selectbox("الإجراء التالي", allowed, key=f"next_{o['id']}")
        if st.button("تنفيذ الإجراء", key=f"do_{o['id']}", type="primary", use_container_width=True):
            try: change_order_status(o["id"], action, user); st.success("تم تحديث حالة الطلب."); st.rerun()
            except Exception as ex: st.error(str(ex))
    if role in ("OWNER", "DISPATCHER") and not closed:
        with st.expander("✏️ تعديل بيانات الطلب"):
            pk = f"edit_point_{o['id']}"
            p = st.session_state.get(pk) or {"lat": o["delivery_lat"], "lng": o["delivery_lng"], "address": o["delivery_address"]}
            res = mount_map(points=[], center=[p.get("lat") or 31.2001, p.get("lng") or 29.9187], zoom=15, clickable=True, key=f"edit_map_{o['id']}", selected=p if p.get("lat") else None)
            click = _payload(res, "map_click") or _payload(res, "search_result") if res else None
            if click and click != st.session_state.get(f"_lc_{o['id']}"): st.session_state[f"_lc_{o['id']}"] = click; st.session_state[pk] = click; st.rerun()
            a, b = st.columns(2); addr = a.text_input("العنوان", value=p.get("address") or o["delivery_address"], key=f"ea_{o['id']}"); dist = b.number_input("المسافة (كم)", value=float(o["distance_km"]), min_value=0.0, step=.1, key=f"ed_{o['id']}")
            c, d = st.columns(2); eta = c.number_input("الوقت المتوقع", value=int(o["eta_minutes"]), min_value=0, step=1, key=f"ee_{o['id']}"); fee = d.number_input("رسوم الخدمة", value=float(o["delivery_fee"]), min_value=0.0, step=1.0, key=f"ef_{o['id']}")
            c, d, e = st.columns(3); billing = c.selectbox("التحصيل", ["كاش", "آجل"], index=0 if o["billing_mode"] == "كاش" else 1, key=f"eb_{o['id']}"); rew = d.number_input("مكافأة", value=float(o["reward"]), min_value=0.0, key=f"er_{o['id']}"); dis = e.number_input("خصم", value=float(o["discount"]), min_value=0.0, key=f"eds_{o['id']}")
            c, d = st.columns(2); cname = c.text_input("اسم العميل", value=o.get("customer_name") or "", key=f"en_{o['id']}"); cphone = d.text_input("هاتف العميل", value=o.get("customer_phone") or "", key=f"ep_{o['id']}")
            auto = commission_for_order(dist, fee, rider_row(o["rider_id"]))
            manual = st.checkbox(f"تعديل عمولة الطيار يدوياً (الحسابي {auto:,.2f} ج)", key=f"em_{o['id']}") if actor_is_owner(user) else False
            comm = st.number_input("عمولة الطيار", value=float(o["rider_commission"]), min_value=0.0, key=f"ec_{o['id']}") if manual else None
            notes = st.text_area("ملاحظات", value=o["notes"] or "", key=f"eno_{o['id']}")
            if st.button("حفظ التعديل", key=f"esave_{o['id']}", use_container_width=True):
                try:
                    update_order(o["id"], {"delivery_address": addr, "delivery_lat": p.get("lat"), "delivery_lng": p.get("lng"), "distance_km": dist, "eta_minutes": eta, "delivery_fee": fee, "billing_mode": billing, "reward": rew, "discount": dis, "notes": notes, "customer_phone": cphone, "customer_name": cname, "rider_commission": comm}, user)
                    st.session_state.pop(pk, None); st.success("تم حفظ التعديل."); st.rerun()
                except Exception as ex: st.error(str(ex))
    if actor_is_owner(user) and o["status"] == "تم التسليم":
        with st.expander("🛠️ تعديل حسابات الطلب المكتمل (المالك)"):
            st.info("التعديل يسجَّل في سجل التدقيق. لو كان الطلب مُسوّى سابقاً يُنشأ قيد تصحيحي تلقائي في الخزينة بالفرق فقط.")
            a, b, c = st.columns(3); fee = a.number_input("رسوم الخدمة", value=float(o["delivery_fee"]), min_value=0.0, key=f"cf_{o['id']}"); comm = b.number_input("عمولة الطيار", value=float(o["rider_commission"]), min_value=0.0, key=f"cc_{o['id']}"); dist = c.number_input("المسافة (كم)", value=float(o["distance_km"]), min_value=0.0, step=.1, key=f"cd_{o['id']}")
            a, b, c = st.columns(3); rew = a.number_input("مكافأة", value=float(o["reward"]), min_value=0.0, key=f"cr_{o['id']}"); dis = b.number_input("خصم", value=float(o["discount"]), min_value=0.0, key=f"cds_{o['id']}"); billing = c.selectbox("التحصيل", ["كاش", "آجل"], index=0 if o["billing_mode"] == "كاش" else 1, key=f"cb_{o['id']}")
            st.caption(f"القيم الحسابية حسب نظام الطيار الحالي: عمولة {commission_for_order(dist, fee, rider_row(o['rider_id'])):,.2f} ج")
            if st.button("حفظ تعديل الحسابات", key=f"csave_{o['id']}", type="primary", use_container_width=True):
                try:
                    rs_, rest_ = owner_edit_closed_order(o["id"], {"delivery_fee": fee, "rider_commission": comm, "reward": rew, "discount": dis, "billing_mode": billing, "distance_km": dist}, user)
                    st.success("تم تعديل الحسابات." + (" وتم تسجيل قيد تصحيحي لتصفية الطيار." if rs_ else "") + (" (الطلب مسدد جزئياً/كلياً من المطعم — راجع الرصيد)." if rest_ else "")); st.rerun()
                except Exception as ex: st.error(str(ex))
    ticket = f"🚚 {APP_NAME}\nالطلب: {o['order_no']}\nالاستلام: {o['restaurant']} — {o['branch']}\nالتسليم: {o['delivery_address']}\nالتحصيل: {o['billing_mode']}\nالمسافة: {o['distance_km']} كم\nالحالة: {o['status']}"
    st.code(ticket + (f"\nرابط تتبع العميل: <رابط التطبيق>?track={o['track_token']}" if o.get("track_token") else ""), language="text")
    if o["delivery_lat"] is not None and role != "RESTAURANT": st.link_button("🧭 ملاحة للعنوان", f"https://www.google.com/maps/dir/?api=1&destination={o['delivery_lat']},{o['delivery_lng']}", use_container_width=True)


def render_orders(user):
    header("الطلبات", "إنشاء، تعيين، متابعة، تعديل، وإغلاق الطلب — والحسابات تتحدث تلقائياً.")
    if user["role"] in ("OWNER", "DISPATCHER"):
        with st.expander("＋ إنشاء طلب", expanded=bool(st.session_state.pop("open_new_order", False))): render_new_order_form(user)
    q = "SELECT o.*,r.name restaurant,b.name branch,COALESCE(ry.name,'—') rider FROM orders o JOIN restaurants r ON r.id=o.restaurant_id JOIN branches b ON b.id=o.branch_id LEFT JOIN riders ry ON ry.id=o.rider_id WHERE 1=1"; params = []
    if user["role"] == "RESTAURANT": q += " AND o.restaurant_id=?"; params.append(user["ref_id"])
    if user["role"] == "RIDER": q += " AND o.rider_id=?"; params.append(user["ref_id"])
    c1, c2 = st.columns([2, 1])
    s = c1.text_input("🔎 بحث سريع", placeholder="رقم الطلب أو العنوان أو اسم المطعم"); status = c2.selectbox("الحالة", ["الكل", "نشطة فقط"] + ACTIVE_STATUSES[:0] + ["جديد", "تم التعيين", "تم القبول", "تم الاستلام", "في الطريق", "تم التسليم", "ملغى"])
    if s: q += " AND (o.order_no LIKE ? OR o.delivery_address LIKE ? OR r.name LIKE ?)"; params += [f"%{s}%"] * 3
    if status == "نشطة فقط": q += " AND o.status NOT IN ('تم التسليم','ملغى')"
    elif status != "الكل": q += " AND o.status=?"; params.append(status)
    orders = df(q + " ORDER BY o.created_at DESC LIMIT 400", tuple(params))
    if orders.empty: st.info("لا توجد طلبات مطابقة."); return
    st.dataframe(orders[list(ORDER_COLS)].rename(columns=ORDER_COLS), use_container_width=True, hide_index=True)
    selected = st.selectbox("فتح الطلب", orders["order_no"].tolist(), key="open_order")
    o = order_with_names(selected)
    if o: render_order_detail(o, user)


def order_with_names(order_no):
    return one("SELECT o.*,r.name restaurant,b.name branch,COALESCE(ry.name,'—') rider FROM orders o JOIN restaurants r ON r.id=o.restaurant_id JOIN branches b ON b.id=o.branch_id LEFT JOIN riders ry ON ry.id=o.rider_id WHERE o.order_no=?", (order_no,))


# =========================================================
# الطيارون / المطاعم / المستخدمون
# =========================================================
def pay_form_fields(prefix, r=None):
    """حقول نظام القبض — تُعرض داخل form."""
    r = r or {}
    codes = list(PAY_MODES)
    mode = st.selectbox("نظام قبض الطيار", codes, index=codes.index(r.get("pay_mode")) if r.get("pay_mode") in codes else 0, format_func=lambda c: PAY_MODES[c], key=f"{prefix}_mode")
    st.caption("• راتب شهري + عمولة: مرتب ثابت وعمولة على كل أوردر حسب المسافة.\n• عمولة فقط: بدون راتب، يقبض عمولة المسافة.\n• حصة الشركة: الشركة تأخذ مبلغاً ثابتاً من كل أوردر والطيار يأخذ الباقي من رسوم التوصيل.")
    a, b = st.columns(2)
    phone = a.text_input("الهاتف", value=r.get("phone") or "", key=f"{prefix}_ph")
    salary = b.number_input("المرتب الشهري (للنظام الشهري)", min_value=0.0, value=float(_num(r.get("salary"), _num(get_setting("salary_basic", 6000), 6000.0))), step=100.0, key=f"{prefix}_sal")
    t = rider_terms(r) if r else {"base_km": _num(get_setting("commission_base_km", 3), 3.0), "base": _num(get_setting("commission_base", 10), 10.0), "extra": _num(get_setting("commission_extra_per_km", 5), 5.0), "cut": 0.0}
    c, d, e, f = st.columns(4)
    bk = c.number_input("عمولة أساسية حتى (كم)", min_value=0.0, value=float(t["base_km"]), step=.5, key=f"{prefix}_bk")
    bs = d.number_input("العمولة الأساسية (ج)", min_value=0.0, value=float(t["base"]), step=1.0, key=f"{prefix}_bs")
    ex = e.number_input("لكل كم زائد (ج)", min_value=0.0, value=float(t["extra"]), step=.5, key=f"{prefix}_ex")
    cut = f.number_input("حصة الشركة/أوردر (ج)", min_value=0.0, value=float(t["cut"] or 0.0), step=1.0, key=f"{prefix}_cut")
    return {"pay_mode": mode, "phone": phone, "salary": salary, "comm_base_km": bk, "comm_base": bs, "comm_extra_km": ex, "company_cut": cut}


def render_riders(user):
    header("الطيارون", "الحالة، نظام القبض لكل طيار، GPS، والطلبات النشطة.")
    rs = df("SELECT * FROM riders ORDER BY active_orders,name")
    owner = actor_is_owner(user)
    for _, r in rs.iterrows():
        fresh = gps_fresh(r.to_dict()); active = r["status"] != "غير نشط"
        with st.container(border=True):
            a, b, c = st.columns([2.2, 1.3, 1.5])
            a.markdown(f"**{esc(r['name'])}**<br><span style='color:#9AA4B2;font-size:.7rem'>{esc(r['phone'] or 'بدون هاتف')} • {PAY_MODES.get(r['pay_mode'], '')}</span>", unsafe_allow_html=True)
            b.markdown(badge("نشط" if active else "غير نشط", "green" if active else "red"), unsafe_allow_html=True)
            c.write(f"{int(r['active_orders'])} طلبات • " + ("🟢 GPS" if fresh else "⚪ GPS قديم"))
            if owner:
                with st.expander("⚙️ إدارة الطيار وطريقة قبضه"):
                    with st.form(f"rider_form_{r['id']}"):
                        data = pay_form_fields(f"rf_{r['id']}", r.to_dict())
                        if st.form_submit_button("💾 حفظ بيانات الطيار", type="primary", use_container_width=True):
                            try: update_rider(r["id"], data, user); st.success("تم الحفظ — وتم تحديث عمولات طلباته النشطة."); st.rerun()
                            except Exception as ex: st.error(str(ex))
                    x, y = st.columns(2)
                    if x.button("تعطيل" if active else "تفعيل", key=f"ra_{r['id']}", use_container_width=True):
                        try: set_active("rider", r["id"], not active, user); st.rerun()
                        except Exception as ex: st.error(str(ex))
                    if y.button("💰 راتب الشهر", key=f"rp_{r['id']}", use_container_width=True): st.session_state.payroll_rider = r["id"]; goto("payroll")
    if owner:
        with st.expander("＋ إضافة طيار", expanded=bool(st.session_state.pop("quick_add_rider", False))):
            with st.form("add_rider"):
                n = st.text_input("الاسم"); data = pay_form_fields("newr")
                if st.form_submit_button("إضافة الطيار", type="primary", use_container_width=True):
                    try: create_rider(data | {"name": n}, user); st.success("تمت إضافة الطيار."); st.rerun()
                    except Exception as ex: st.error(str(ex))


def render_restaurants(user):
    header("المطاعم والفروع", "الحالة، الحساب، والفروع مع تحديد المواقع بالنقر على الخريطة.")
    rs = all_restaurants(); owner = actor_is_owner(user)
    if owner and st.session_state.pop("quick_add_branch", False):
        if rs.empty: st.warning("أضف مطعماً أولاً قبل إنشاء فرع.")
        else:
            qn = st.selectbox("اختر المطعم لإضافة الفرع", rs["name"].tolist(), key="quick_branch_restaurant"); st.session_state[f"branch_open_{rs[rs['name'] == qn].iloc[0]['id']}"] = True
    for _, r in rs.iterrows():
        bs = branches_for(r["id"], False)
        with st.container(border=True):
            a, b, c = st.columns([2, 1, 1.3]); a.markdown(f"**{esc(r['name'])}**<br><span style='color:#9AA4B2;font-size:.7rem'>{esc(r['phone'] or '')}</span>", unsafe_allow_html=True)
            b.markdown(badge("نشط" if r["active"] else "غير نشط", "green" if r["active"] else "red"), unsafe_allow_html=True); c.write(f"{r['billing_mode']} • {len(bs)} فروع")
            if owner:
                with st.expander("⚙️ إدارة المطعم"):
                    with st.form(f"rest_form_{r['id']}"):
                        a, b = st.columns(2); ph = a.text_input("الهاتف", value=r["phone"] or ""); mode = b.selectbox("التحصيل", ["كاش", "آجل"], index=0 if r["billing_mode"] == "كاش" else 1)
                        if st.form_submit_button("حفظ المطعم", use_container_width=True): update_restaurant(r["id"], ph, mode, user); st.success("تم الحفظ."); st.rerun()
                    x, y = st.columns(2)
                    if x.button("تعطيل" if r["active"] else "تفعيل", key=f"restact_{r['id']}", use_container_width=True):
                        try: set_active("restaurant", r["id"], not bool(r["active"]), user); st.rerun()
                        except Exception as ex: st.error(str(ex))
                    if y.button("＋ إضافة فرع", key=f"branch_{r['id']}", use_container_width=True): st.session_state[f"branch_open_{r['id']}"] = not st.session_state.get(f"branch_open_{r['id']}", False)
            for _, br in bs.iterrows():
                x, y = st.columns([4, 1]); x.markdown(f"• **{esc(br['name'])}** — {esc(br['address'] or 'بدون عنوان')} — {'نشط' if br['active'] else 'غير نشط'}", unsafe_allow_html=True)
                if owner and y.button("تعطيل" if br["active"] else "تفعيل", key=f"bract_{br['id']}"):
                    try: set_active("branch", br["id"], not bool(br["active"]), user); st.rerun()
                    except Exception as ex: st.error(str(ex))
            if owner and st.session_state.get(f"branch_open_{r['id']}", False):
                p = st.session_state.get("branch_pick", {})
                res = mount_map(center=[31.2001, 29.9187], zoom=12, clickable=True, key=f"branch_pick_map_{r['id']}")
                click = _payload(res, "map_click") or _payload(res, "search_result") if res else None
                if click and click != st.session_state.get("_branch_click"): st.session_state["_branch_click"] = click; st.session_state.branch_pick = click; st.rerun()
                p = st.session_state.get("branch_pick", {})
                if p.get("lat") is not None: st.success(f"موقع الفرع: {p.get('address', '')} — {p['lat']}, {p['lng']}")
                with st.form(f"add_branch_{r['id']}"):
                    a, b = st.columns(2); n = a.text_input("اسم الفرع"); addr = b.text_input("العنوان", value=p.get("address", ""))
                    if st.form_submit_button("حفظ الفرع", type="primary", use_container_width=True):
                        try: create_branch({"restaurant_id": r["id"], "name": n, "address": addr, "lat": p.get("lat"), "lng": p.get("lng")}, user); st.session_state.pop("branch_pick", None); st.session_state.pop("_branch_click", None); st.success("تمت إضافة الفرع."); st.rerun()
                        except Exception as ex: st.error(str(ex))
    if owner:
        with st.expander("＋ إضافة مطعم", expanded=bool(st.session_state.pop("quick_add_restaurant", False))):
            with st.form("add_restaurant"):
                a, b, c = st.columns(3); n = a.text_input("اسم المطعم"); ph = b.text_input("الهاتف"); mode = c.selectbox("التحصيل", ["كاش", "آجل"])
                if st.form_submit_button("إضافة المطعم", type="primary", use_container_width=True):
                    try: create_restaurant({"name": n, "phone": ph, "billing_mode": mode}, user); st.success("تمت إضافة المطعم."); st.rerun()
                    except Exception as ex: st.error(str(ex))


def _ref_select(role, current=None, key="ref"):
    if role == "RIDER": rr = df("SELECT id,name FROM riders ORDER BY name"); lab = "ربط بالطيار"
    elif role == "RESTAURANT": rr = all_restaurants(); lab = "ربط بالمطعم"
    else: return None
    if rr.empty: st.warning("أضف الطيار/المطعم أولاً."); return None
    ids = rr["id"].tolist(); idx = ids.index(current) if current in ids else 0
    return ids[rr["name"].tolist().index(st.selectbox(lab, rr["name"].tolist(), index=idx, key=key))]


def render_account_security(user):
    """واجهة أمن الحساب: تغيير PIN الشخصي، وللمالك تعيين PIN لمستخدم آخر."""
    header("أمان الحساب", "تغيير PIN وإدارة الوصول بدون إظهار أي كلمة مرور مخزنة.")
    with st.container(border=True):
        st.markdown("### 🔐 تغيير PIN الخاص بي")
        with st.form("change_own_pin_form"):
            a, b = st.columns(2)
            current = a.text_input("PIN الحالي", type="password", max_chars=8)
            new = b.text_input("PIN الجديد", type="password", max_chars=8)
            confirm = st.text_input("تأكيد PIN الجديد", type="password", max_chars=8)
            if st.form_submit_button("🔒 تغيير PIN", type="primary", use_container_width=True):
                try:
                    if new != confirm:
                        raise ValueError("تأكيد PIN الجديد غير مطابق.")
                    change_own_pin(current, new, user)
                    st.success("تم تغيير PIN بنجاح. الجلسة الحالية مستمرة.")
                    st.rerun()
                except Exception as ex:
                    st.error(str(ex))
    if actor_is_owner(user):
        st.divider()
        st.markdown("### 👑 تعيين PIN لمستخدم")
        us = df("SELECT id,name,email,role,active FROM users WHERE id!=? ORDER BY name", (user["id"],))
        if us.empty:
            st.info("لا توجد حسابات أخرى.")
        else:
            selected = st.selectbox("المستخدم", us["name"].tolist(), key="security_user_select")
            target = us[us["name"] == selected].iloc[0]
            with st.form("owner_set_user_pin_form"):
                p1 = st.text_input("PIN الجديد", type="password", max_chars=8)
                p2 = st.text_input("تأكيد PIN", type="password", max_chars=8)
                c1, c2 = st.columns(2)
                set_btn = c1.form_submit_button("تعيين PIN", type="primary", use_container_width=True)
                gen_btn = c2.form_submit_button("توليد PIN آمن", use_container_width=True)
                if set_btn or gen_btn:
                    try:
                        chosen = (''.join(secrets.choice('0123456789') for _ in range(6)) if gen_btn else p1)
                        if not gen_btn and chosen != p2:
                            raise ValueError("تأكيد PIN غير مطابق.")
                        owner_set_user_pin(target["id"], chosen, user)
                        st.session_state.generated_pin = {"name": target["name"], "pin": chosen}
                        st.success("تم تعيين PIN وإبطال الجلسات القديمة للمستخدم.")
                        st.rerun()
                    except Exception as ex:
                        st.error(str(ex))
    if st.session_state.get("generated_pin"):
        x = st.session_state["generated_pin"]
        st.warning(f"PIN الجديد لـ {x['name']}: {x['pin']} — احفظه الآن؛ سيُخفى بعد مغادرة الصفحة.")
        if st.button("إخفاء PIN", key="security_hide_pin", use_container_width=True):
            st.session_state.pop("generated_pin", None); st.rerun()


def render_users(user):
    header("المستخدمون والحسابات", "أنت تنشئ حساب كل موظف حسب مهمته وتحدد له PIN — ويبقى مسجلاً على جهازه حتى يخرج.")
    us = df("SELECT id,name,email,role,ref_id,active,created_at FROM users ORDER BY name")
    roles = ["DISPATCHER", "ACCOUNTANT", "RIDER", "RESTAURANT"]
    for _, u in us.iterrows():
        with st.container(border=True):
            a, b, c = st.columns([2.2, 1, 1]); a.markdown(f"**{esc(u['name'])}**<br><span style='color:#9AA4B2;font-size:.7rem'>{esc(u['email'])}</span>", unsafe_allow_html=True); b.write(role_label(u["role"])); c.markdown(badge("نشط" if u["active"] else "غير نشط", "green" if u["active"] else "red"), unsafe_allow_html=True)
            if u["id"] == user["id"] or u["role"] == "OWNER": continue
            with st.expander("✏️ تعديل الحساب"):
                role = st.selectbox("الدور", roles, index=roles.index(u["role"]) if u["role"] in roles else 0, format_func=role_label, key=f"ur_{u['id']}")
                ref = _ref_select(role, u["ref_id"], key=f"uref_{u['id']}")
                with st.form(f"uedit_{u['id']}"):
                    a, b = st.columns(2); n = a.text_input("الاسم", value=u["name"]); e = b.text_input("البريد", value=u["email"]); pin = st.text_input("PIN جديد (اتركه فارغاً لعدم التغيير)", type="password", max_chars=8)
                    if st.form_submit_button("حفظ التعديل", type="primary", use_container_width=True):
                        try: update_user(u["id"], {"name": n, "email": e, "role": role, "ref_id": ref, "pin": pin}, user); st.success("تم الحفظ."); st.rerun()
                        except Exception as ex: st.error(str(ex))
                x, y = st.columns(2)
                if x.button("تعطيل" if u["active"] else "تفعيل", key=f"uact_{u['id']}", use_container_width=True):
                    try: set_active("user", u["id"], not bool(u["active"]), user); st.rerun()
                    except Exception as ex: st.error(str(ex))
                if y.button("🔑 توليد PIN جديد", key=f"upin_{u['id']}", use_container_width=True): st.session_state.generated_pin = {"name": u["name"], "pin": reset_user_pin(u["id"], user)}; st.rerun()
    if st.session_state.get("generated_pin"):
        x = st.session_state.generated_pin; st.success(f"PIN الجديد لـ {x['name']}: {x['pin']} — يظهر مرة واحدة.")
        if st.button("إخفاء PIN", use_container_width=True): st.session_state.pop("generated_pin", None); st.rerun()
    with st.expander("＋ إنشاء حساب موظف"):
        role = st.selectbox("الدور", roles, format_func=role_label, key="new_user_role"); ref = _ref_select(role, key="new_user_ref")
        with st.form("create_user"):
            a, b = st.columns(2); n = a.text_input("الاسم"); e = b.text_input("البريد الإلكتروني"); pin = st.text_input("PIN أولي (4-8 أرقام)", type="password", max_chars=8)
            if st.form_submit_button("إنشاء الحساب", type="primary", use_container_width=True):
                try: create_user({"name": n, "email": e, "role": role, "pin": pin, "ref_id": ref}, user); st.success("تم إنشاء الحساب."); st.rerun()
                except Exception as ex: st.error(str(ex))


# =========================================================
# الحضور / المرتبات
# =========================================================
def render_attendance(user):
    header("الحضور وساعات العمل", "الساعات تُحسب من الدخول إلى الخروج مع خصم وقت الراحة.")
    period = st.date_input("اختر الشهر", value=today_d().replace(day=1), key="attendance_month").strftime("%Y-%m")
    if user["role"] == "RIDER":
        rid = user["ref_id"]; att = one("SELECT * FROM attendance WHERE rider_id=? AND work_date=?", (rid, today_str()))
        if not att or not att["clock_in"]:
            if st.button("🟢 تسجيل دخول الآن", type="primary", use_container_width=True): upsert_attendance({"rider_id": rid, "work_date": today_str(), "clock_in": now_iso(), "clock_out": None, "break_minutes": 0, "status": "حاضر", "reason": ""}, user); st.rerun()
        elif not att["clock_out"]:
            st.success(f"تم تسجيل الدخول: {att['clock_in']}")
            if st.button("🔴 تسجيل خروج الآن", type="primary", use_container_width=True): upsert_attendance({"rider_id": rid, "work_date": today_str(), "clock_in": att["clock_in"], "clock_out": now_iso(), "break_minutes": int(att.get("break_minutes") or 0), "status": "حاضر", "reason": att.get("reason", "")}, user); st.rerun()
        else: st.success(f"ساعات اليوم: {attendance_hours(att):.2f} ساعة")
        stats = attendance_for_month(rid, period); hours = sum(attendance_hours(x) for x in stats.to_dict("records")) if not stats.empty else 0
        metric_grid([("ساعات الشهر", f"{hours:.2f}", f"المتوقع {float(get_setting('working_days', 26)) * float(get_setting('daily_work_hours', 8)):.0f} ساعة", "info"), ("أيام حضور", int((stats["status"] == "حاضر").sum()) if not stats.empty else 0, "هذا الشهر", "good"), ("بعذر", int((stats["status"] == "إجازة بعذر").sum()) if not stats.empty else 0, "يوم", "warn"), ("بدون عذر", int((stats["status"] == "إجازة بدون عذر").sum()) if not stats.empty else 0, "يوم", "danger")])
        if not stats.empty:
            view = stats.copy(); view["ساعات العمل"] = [attendance_hours(x) for x in stats.to_dict("records")]
            st.dataframe(view[["work_date", "status", "clock_in", "clock_out", "break_minutes", "ساعات العمل", "reason"]].rename(columns={"work_date": "التاريخ", "status": "الحالة", "clock_in": "دخول", "clock_out": "خروج", "break_minutes": "راحة/دقيقة", "reason": "السبب"}), use_container_width=True, hide_index=True)
        return
    riders = df("SELECT id,name FROM riders ORDER BY name")
    if actor_is_owner(user) and not riders.empty:
        with st.expander("＋ تسجيل/تعديل يوم"):
            with st.form("attendance_edit"):
                rn = st.selectbox("الطيار", riders["name"].tolist()); rid = riders[riders["name"] == rn].iloc[0]["id"]; wd = st.date_input("اليوم", value=today_d())
                status = st.selectbox("الحالة", ["حاضر", "إجازة بعذر", "إجازة بدون عذر", "غياب"])
                a, b, c = st.columns(3); ci = a.time_input("وقت الدخول", value=datetime.strptime("09:00", "%H:%M").time()); co = b.time_input("وقت الخروج", value=datetime.strptime("17:00", "%H:%M").time()); br = c.number_input("راحة بالدقائق", min_value=0, value=0, step=5)
                reason = st.text_input("السبب")
                if st.form_submit_button("حفظ", type="primary", use_container_width=True):
                    try:
                        present = status == "حاضر"
                        upsert_attendance({"rider_id": rid, "work_date": wd.isoformat(), "clock_in": f"{wd.isoformat()} {ci.strftime('%H:%M:%S')}" if present else None, "clock_out": f"{wd.isoformat()} {co.strftime('%H:%M:%S')}" if present else None, "break_minutes": br, "status": status, "reason": reason}, user)
                        st.success("تم تسجيل الحضور."); st.rerun()
                    except Exception as ex: st.error(str(ex))
    rows = []
    for _, r in riders.iterrows():
        stt = attendance_for_month(r["id"], period)
        rows.append({"الطيار": r["name"], "أيام الحضور": int((stt["status"] == "حاضر").sum()) if not stt.empty else 0, "بعذر": int((stt["status"] == "إجازة بعذر").sum()) if not stt.empty else 0, "بدون عذر": int((stt["status"] == "إجازة بدون عذر").sum()) if not stt.empty else 0, "ساعات العمل": round(sum(attendance_hours(x) for x in stt.to_dict("records")), 2) if not stt.empty else 0})
    if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_payroll(user):
    header("إقفال الرواتب الشهرية", "الراتب − خصم الإجازات ± التسويات فقط. عمولات الكاش والآجل في «حساب الطيار» وتُصفّى في أي وقت بشكل منفصل.")
    period = st.date_input("الشهر", value=today_d().replace(day=1), key="payroll_month").strftime("%Y-%m")
    riders = df("SELECT id,name FROM riders ORDER BY name")
    if riders.empty: st.info("لا يوجد طيارون."); return
    sel_id = st.session_state.get("payroll_rider", riders.iloc[0]["id"]); names = riders["name"].tolist(); ids = riders["id"].tolist()
    rn = st.selectbox("الطيار", names, index=ids.index(sel_id) if sel_id in ids else 0, key="payroll_select"); rid = ids[names.index(rn)]; st.session_state.payroll_rider = rid
    p = payroll_summary(rid, period)
    st.markdown(f'<div class="highlight"><b>نظام القبض:</b> {esc(p["mode_label"])} • طلبات مسلمة هذا الشهر {p["orders_count"]} (سُوّيت منها {p["settled_count"]})</div>', unsafe_allow_html=True)
    metric_grid([("الأساسي", f"{p['basic']:,.2f} ج", "شهري" if p["mode"] == "MONTHLY" else "لا يوجد راتب", "info"), ("ساعات العمل", f"{p['hours']:.2f}", f"المتوقع {p['expected_hours']:.0f}", "info"), ("عمولات (حساب الطيار)", f"{rider_wallet(rid)['comm']:,.2f} ج", "منفصلة عن الإقفال", "info"), ("خصم الإجازات", f"{p['leave_deduction']:,.2f} ج", f"بعذر {p['excused']} • بدون {p['unexcused']}", "warn"), ("صافي المستحق", f"{p['net']:,.2f} ج", "قبل الدفعات", "good"), ("المتبقي", f"{p['remaining']:,.2f} ج", f"مدفوع {p['paid']:,.2f} ج", "danger" if p['remaining'] > 0 else "good")])
    _all = []
    for _, x in riders.iterrows():
        q = payroll_summary(x["id"], period); _all.append({"الطيار": x["name"], "النظام": q["mode_label"], "الأساسي": q["basic"], "خصم إجازات": q["leave_deduction"], "عمولات": q["commissions"], "مكافآت": q["rewards"], "خصومات طلبات": q["discounts"], "إضافات": q["adjust_add"], "خصومات وسلف": q["adjust_deduct"], "الصافي": q["net"], "المدفوع": q["paid"], "المتبقي": q["remaining"]})
    export_button("📥 تصدير مرتبات كل الطيارين (Excel)", {"المرتبات": pd.DataFrame(_all)}, f"payroll_{period}")
    with st.expander("🧾 تفاصيل طريقة الحساب"):
        st.write(f"المرتب الأساسي: {p['basic']:,.2f} ج • خصم الإجازات: −{p['leave_deduction']:,.2f} ج")
        st.caption("العمولات والمكافآت وخصومات الطلبات تُصفّى من «حساب الطيار» بشكل منفصل عن الراتب.")
        st.write(f"إضافات: +{p['adjust_add']:,.2f} ج • خصومات/سلف: −{p['adjust_deduct']:,.2f} ج"); st.write(f"**الصافي: {p['net']:,.2f} ج**")
    if user["role"] in ("OWNER", "ACCOUNTANT"):
        a, b = st.columns(2)
        with a:
            with st.form("pay_salary"):
                amount = st.number_input("مبلغ القبض", min_value=0.0, max_value=max(0.0, float(p["remaining"])), value=0.0, step=100.0); method = st.selectbox("طريقة الدفع", ["كاش", "تحويل بنكي", "محفظة إلكترونية"]); ref = st.text_input("مرجع/إيصال"); notes = st.text_input("ملاحظات")
                if st.form_submit_button("💸 تسجيل قبض المرتب", type="primary", use_container_width=True):
                    try: record_payroll_payment({"rider_id": rid, "period": period, "amount": amount, "method": method, "reference": ref, "notes": notes}, user); st.success("تم تسجيل القبض وربطه بالخزينة."); st.rerun()
                    except Exception as ex: st.error(str(ex))
        with b:
            with st.form("payroll_adjust"):
                typ = st.selectbox("نوع التسوية", ["إضافة", "خصم", "سلفة"]); amount = st.number_input("المبلغ", min_value=0.0, step=50.0); desc = st.text_input("الوصف")
                if st.form_submit_button("إضافة تسوية", use_container_width=True):
                    try: add_payroll_adjustment({"rider_id": rid, "period": period, "type": typ, "amount": amount, "description": desc}, user); st.success("تمت الإضافة."); st.rerun()
                    except Exception as ex: st.error(str(ex))
    owner = actor_is_owner(user)
    adj = df("SELECT id,type,amount,description,created_at FROM payroll_adjustments WHERE rider_id=? AND period=? ORDER BY created_at DESC", (rid, period))
    if not adj.empty:
        st.markdown("**التسويات المسجلة**")
        for _, x in adj.iterrows():
            c1, c2 = st.columns([4, 1]); c1.write(f"{x['type']} — {x['amount']:,.2f} ج — {x['description'] or ''} ({x['created_at']})")
            if owner and c2.button("حذف", key=f"deladj_{x['id']}"): delete_payroll_adjustment(x["id"], user); st.rerun()
    pay = df("SELECT id,paid_at,amount,method,reference FROM payroll_payments WHERE rider_id=? AND period=? ORDER BY paid_at DESC", (rid, period))
    if not pay.empty:
        st.markdown("**الدفعات**")
        for _, x in pay.iterrows():
            c1, c2 = st.columns([4, 1]); c1.write(f"{x['paid_at']} — {x['amount']:,.2f} ج — {x['method']} {x['reference'] or ''}")
            if owner and c2.button("إلغاء", key=f"delpay_{x['id']}"): void_payroll_payment(x["id"], user); st.rerun()


def render_settlements(user):
    header("التسويات والخزينة", "افصل بين تصفية كاش الطيار، تحصيل الآجل من المطاعم، وصرف الرواتب — والمالك يستطيع إلغاء أي تسوية وإعادتها.")
    owner = actor_is_owner(user)
    if user["role"] in ("OWNER", "DISPATCHER", "ACCOUNTANT"):
        with st.container(border=True):
            st.markdown("### تصفية حساب الطيار (كاش + آجل معاً) — التنفيذ للمالك فقط")
            riders = df("SELECT id,name FROM riders ORDER BY name")
            if not riders.empty:
                rn = st.selectbox("الطيار", riders["name"].tolist(), key="sett_rider"); rid = riders[riders["name"] == rn].iloc[0]["id"]
                a, b = st.columns(2); start = a.date_input("من", value=today_d()); end = b.date_input("إلى", value=today_d())
                os_ = rider_unsettled_orders(rid, start.isoformat(), (end + timedelta(days=1)).isoformat())
                gross = float(os_["remaining_cash"].sum()) if not os_.empty else 0; comm = float(os_["rider_commission"].sum()) if not os_.empty else 0; rew = float(os_["reward"].sum()) if not os_.empty else 0; dis = float(os_["discount"].sum()) if not os_.empty else 0; due = gross - comm - rew + dis
                metric_grid([("عدد الطلبات", len(os_), "غير مصفاة", "info"), ("الكاش", f"{gross:,.2f} ج", "المتحصل", "info"), ("عمولات الطيار", f"{comm:,.2f} ج", "تُخصم", "warn"), ("التوريد", f"{due:,.2f} ج", "المطلوب للخزينة", "good")])
                if not os_.empty: st.dataframe(os_[["order_no", "restaurant", "delivered_at", "cash_collected", "rider_commission", "reward", "discount"]].rename(columns={"order_no": "الطلب", "restaurant": "المطعم", "delivered_at": "التسليم", "cash_collected": "الكاش", "rider_commission": "العمولة", "reward": "مكافأة", "discount": "خصم"}), use_container_width=True, hide_index=True)
                if not owner: st.info("👑 التصفية ينفذها المالك فقط؛ يمكنك مراجعة الأرقام.")
                elif st.button("إغلاق التصفية وتسجيل الخزينة", type="primary", use_container_width=True):
                    try: sid, due, n = create_rider_settlement(rid, start.isoformat(), (end + timedelta(days=1)).isoformat(), user); st.success(f"تمت التصفية: {n} طلب • صافي التوريد {due:,.2f} ج"); st.rerun()
                    except Exception as ex: st.error(str(ex))
        if user["role"] in ("OWNER", "ACCOUNTANT"):
            with st.container(border=True):
                st.markdown("### تحصيل مطعم آجل")
                rs = all_restaurants(); credit = rs[rs["billing_mode"] == "آجل"] if not rs.empty else rs
                if credit.empty: st.caption("لا توجد مطاعم على نظام الآجل.")
                else:
                    rn = st.selectbox("المطعم", credit["name"].tolist(), key="sett_rest"); rid = credit[credit["name"] == rn].iloc[0]["id"]
                    a, b = st.columns(2); start = a.date_input("من", value=today_d().replace(day=1), key="rsstart"); end = b.date_input("إلى", value=today_d(), key="rsend")
                    os_ = restaurant_unsettled_orders(rid, start.isoformat(), (end + timedelta(days=1)).isoformat()); due = float(os_["remaining_due"].sum()) if not os_.empty else 0.0
                    st.markdown(f"**المديونية غير المسددة:** `{due:,.2f} ج` ({len(os_)} طلب)")
                    paid = st.number_input("المبلغ المحصل", min_value=0.0, max_value=max(due, 0.0), value=float(due), step=10.0)
                    if st.button("تسجيل تحصيل المطعم", type="primary", use_container_width=True):
                        try: create_restaurant_settlement(rid, start.isoformat(), (end + timedelta(days=1)).isoformat(), paid, user); st.success("تم تسجيل التحصيل."); st.rerun()
                        except Exception as ex: st.error(str(ex))
    with st.expander("📄 كشف حساب مطعم وتصدير Excel"):
        rs_all = all_restaurants()
        if rs_all.empty: st.caption("لا توجد مطاعم.")
        else:
            rn = st.selectbox("المطعم", rs_all["name"].tolist(), key="stmt_rest"); rid_s = rs_all[rs_all["name"] == rn].iloc[0]["id"]
            a, b = st.columns(2); s0 = a.date_input("من", value=today_d().replace(day=1), key="stmt_s"); e0 = b.date_input("إلى", value=today_d(), key="stmt_e")
            stt = restaurant_statement(rid_s, s0.isoformat(), (e0 + timedelta(days=1)).isoformat())
            if stt.empty: st.info("لا توجد طلبات مسلّمة في الفترة.")
            else:
                stt["المتبقي"] = (stt["delivery_fee"] - stt["settled"]).where(stt["billing_mode"] == "آجل", 0.0)
                st.markdown(f"**{len(stt)} طلب** • إجمالي رسوم الخدمة **{stt['delivery_fee'].sum():,.2f} ج** • المتبقي على المطعم **{stt['المتبقي'].sum():,.2f} ج**")
                view = stt.rename(columns={"order_no": "الطلب", "delivered_at": "التسليم", "branch": "الفرع", "billing_mode": "التحصيل", "delivery_fee": "رسوم الخدمة", "settled": "مسدد"})
                st.dataframe(view, use_container_width=True, hide_index=True)
                export_button("📥 تحميل كشف الحساب", {"كشف حساب": view}, f"statement_{rn}_{s0.isoformat()}")
    st.markdown("### سجل التسويات")
    hist = df("SELECT s.id,s.kind,s.created_at,s.gross,s.commissions,s.cash_due,s.paid,COALESCE(s.voided,0) voided,COALESCE(ry.name,rs.name,s.party_id) party FROM settlements s LEFT JOIN riders ry ON ry.id=s.party_id LEFT JOIN restaurants rs ON rs.id=s.party_id ORDER BY s.created_at DESC LIMIT 60")
    for _, s in hist.iterrows():
        c1, c2 = st.columns([4, 1.2])
        c1.markdown(f"{'~~' if s['voided'] else ''}**{s['kind'].replace('_', ' ')}** — {esc(s['party'])} — {s['created_at']} — إجمالي {s['gross']:,.2f} • صافي {s['cash_due'] if s['kind'] != 'مطعم' else s['paid']:,.2f} ج{'~~ (ملغاة)' if s['voided'] else ''}")
        if owner and not s["voided"] and s["kind"] in ("طيار_كاش", "حساب_طيار", "مطعم"):
            if c2.button("↩️ إلغاء التسوية", key=f"void_{s['id']}", use_container_width=True):
                try: void_settlement(s["id"], user); st.success("تم إلغاء التسوية وعادت الطلبات غير مصفاة."); st.rerun()
                except Exception as ex: st.error(str(ex))
    st.markdown("### آخر الحركات المالية")
    ledger = df("SELECT created_at,txn_type,account_type,amount,direction,reference_id,description FROM ledger ORDER BY id DESC LIMIT 200")
    if not ledger.empty: st.dataframe(ledger.rename(columns={"created_at": "الوقت", "txn_type": "نوع الحركة", "account_type": "الحساب", "amount": "المبلغ", "direction": "الاتجاه", "reference_id": "المرجع", "description": "الوصف"}), use_container_width=True, hide_index=True)


def render_analysis(user):
    header("التحليل والأداء", "قراءة تشغيلية ومالية من نفس البيانات.")
    a, b = st.columns(2); start = a.date_input("من", value=today_d() - timedelta(days=29), key="an_start"); end = b.date_input("إلى", value=today_d(), key="an_end")
    orders = df("SELECT * FROM orders WHERE created_at>=? AND created_at<?", (start.isoformat() + " 00:00:00", (end + timedelta(days=1)).isoformat() + " 00:00:00"))
    if orders.empty: st.info("لا توجد بيانات للفترة."); return
    delivered = orders[orders["status"] == "تم التسليم"]; cancel = orders[orders["status"] == "ملغى"]; vals = []
    for _, o in delivered.iterrows():
        try: vals.append((parse_ts(o["delivered_at"]) - parse_ts(o["created_at"])).total_seconds() / 60)
        except Exception: pass
    fees = float(delivered["delivery_fee"].sum()); comm = float(delivered["rider_commission"].sum())
    metric_grid([("إجمالي الطلبات", len(orders), "الفترة", "info"), ("نسبة التسليم", f"{len(delivered) / len(orders) * 100:.1f}%", "من الإجمالي", "good"), ("الإلغاء", f"{len(cancel)}", f"{len(cancel) / len(orders) * 100:.1f}%", "danger"), ("متوسط الزمن", f"{(sum(vals) / len(vals) if vals else 0):.1f} د", "إنشاء ← تسليم", "info"), ("رسوم الخدمة", f"{fees:,.0f} ج", "المسلّم", "good"), ("صافي الشركة", f"{fees - comm:,.0f} ج", f"بعد عمولات {comm:,.0f} ج", "good")])
    st.markdown("### أداء الطيارين")
    rrows = []
    for _, r in df("SELECT id,name,pay_mode FROM riders ORDER BY name").iterrows():
        od = delivered[delivered["rider_id"] == r["id"]]; att = df("SELECT * FROM attendance WHERE rider_id=? AND work_date>=? AND work_date<=?", (r["id"], start.isoformat(), end.isoformat()))
        rrows.append({"الطيار": r["name"], "النظام": PAY_MODES.get(r["pay_mode"], ""), "تم التسليم": len(od), "العمولات": round(float(od["rider_commission"].sum()), 2) if not od.empty else 0, "حصة الشركة": round(float((od["delivery_fee"] - od["rider_commission"]).sum()), 2) if not od.empty else 0, "الساعات": round(sum(attendance_hours(x) for x in att.to_dict("records")), 2) if not att.empty else 0, "في الموعد %": on_time_rate(od)})
    st.dataframe(pd.DataFrame(rrows), use_container_width=True, hide_index=True)
    st.markdown("### أداء المطاعم")
    rr = orders.groupby("restaurant_id").agg(طلبات=("id", "count"), رسوم=("delivery_fee", "sum")).reset_index(); names = df("SELECT id,name FROM restaurants")
    if not names.empty: st.dataframe(rr.merge(names, left_on="restaurant_id", right_on="id")[["name", "طلبات", "رسوم"]].rename(columns={"name": "المطعم"}), use_container_width=True, hide_index=True)
    daily = orders.assign(التاريخ=orders["created_at"].str[:10]).groupby("التاريخ")["id"].count().reset_index(name="الطلبات")
    st.bar_chart(daily.set_index("التاريخ"))
    export_button("📥 تصدير طلبات الفترة (Excel)", {"الطلبات": orders.drop(columns=[c for c in ("track_token",) if c in orders.columns]), "أداء الطيارين": pd.DataFrame(rrows)}, f"orders_{start.isoformat()}_{end.isoformat()}")


def render_tools(user):
    header("الأدوات والإعدادات", "القيم الافتراضية (تُطبق على أي طيار لم تُحدد له قيم خاصة).")
    if actor_is_owner(user):
        a, b, c = st.columns(3); salary = a.number_input("المرتب الافتراضي", value=float(get_setting("salary_basic", 6000)), step=100.0); work = b.number_input("أيام العمل الشهري", value=float(get_setting("working_days", 26)), min_value=1.0, step=1.0); hours = c.number_input("ساعات العمل/اليوم", value=float(get_setting("daily_work_hours", 8)), min_value=.5, step=.5)
        d, e, f, g = st.columns(4); gps = d.number_input("GPS حديث حتى (ثانية)", value=float(get_setting("gps_fresh_seconds", 30)), min_value=5.0, step=5.0); bkm = e.number_input("العمولة الأساسية حتى (كم)", value=float(get_setting("commission_base_km", 3)), step=.5); base = f.number_input("العمولة الأساسية (ج)", value=float(get_setting("commission_base", 10)), step=1.0); extra = g.number_input("لكل كم زائد (ج)", value=float(get_setting("commission_extra_per_km", 5)), step=.5)
        h, i, j = st.columns(3); grace = h.number_input("سماح التأخير (دقيقة)", value=float(get_setting("order_overdue_grace_minutes", 15)), min_value=0.0, step=5.0); exc = i.number_input("خصم الإجازة بعذر (أيام)", value=float(get_setting("excused_leave_days", 1)), step=.25); unx = j.number_input("خصم الإجازة بدون عذر (أيام)", value=float(get_setting("unexcused_leave_days", 1.25)), step=.25)
        k1, k2, k3, k4 = st.columns(4); fb = k1.number_input("رسوم التوصيل الأساسية (ج)", value=float(get_setting("fee_base", 30)), step=1.0); fbk = k2.number_input("تشمل حتى (كم)", value=float(get_setting("fee_base_km", 3)), step=.5); fex = k3.number_input("رسوم كل كم زائد (ج)", value=float(get_setting("fee_extra_km", 5)), step=.5); climit = k4.number_input("حد تنبيه كاش الطيار (ج)", value=float(get_setting("cash_limit", 1500)), step=100.0)
        if st.button("حفظ الإعدادات", type="primary", use_container_width=True):
            for k, v in [("salary_basic", salary), ("working_days", work), ("daily_work_hours", hours), ("gps_fresh_seconds", gps), ("commission_base_km", bkm), ("commission_base", base), ("commission_extra_per_km", extra), ("order_overdue_grace_minutes", grace), ("excused_leave_days", exc), ("unexcused_leave_days", unx), ("fee_base", fb), ("fee_base_km", fbk), ("fee_extra_km", fex), ("cash_limit", climit)]: set_setting(k, v)
            st.success("تم حفظ الإعدادات.")
        st.caption("ملاحظة: تغيير القيم الافتراضية لا يغيّر عمولات الطلبات المكتملة. لتعديل طلب مكتمل استخدم «تعديل حسابات الطلب المكتمل».")
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        for t in [x for x in SCHEMA if x != "sessions"]: z.writestr(f"{t}.csv", df(f"SELECT * FROM {t}" + (" WHERE key!='ai_api_key'" if t == "settings" else "")).to_csv(index=False, encoding="utf-8-sig"))
    st.download_button("📦 تنزيل نسخة بيانات ONWAY", data=mem.getvalue(), file_name=f"ONWAY_Backup_{today_str()}.zip", mime="application/zip", use_container_width=True)
    if user["role"] in ("OWNER", "ACCOUNTANT"):
        with st.expander("سجل التدقيق"): st.dataframe(df("SELECT created_at,actor_id,action,entity,entity_id FROM audit_log ORDER BY id DESC LIMIT 500").rename(columns={"created_at": "الوقت", "actor_id": "المستخدم", "action": "العملية", "entity": "الكيان", "entity_id": "المعرف"}), use_container_width=True, hide_index=True)


def render_rider_wallet(user):
    header("محفظة الطيار", "مستحقاتك: العمولة المكتسبة، ما تمت تسويته، وما تبقى.")
    rid = user.get("ref_id"); owner = actor_is_owner(user)
    if owner and not rid:
        riders = df("SELECT id,name FROM riders ORDER BY name")
        if riders.empty: st.info("لا يوجد طيارون."); return
        rid = riders.iloc[riders["name"].tolist().index(st.selectbox("اختر الطيار", riders["name"].tolist(), key="owner_wallet_rider"))]["id"]
    r = rider_row(rid)
    if not r: st.error("لا يوجد طيار مرتبط بهذه المساحة."); return
    a, b = st.columns(2); sd = a.date_input("من", value=today_d() - timedelta(days=6), key=f"ws_{rid}"); ed = b.date_input("إلى", value=today_d(), key=f"we_{rid}")
    if ed < sd: st.error("تاريخ النهاية يجب أن يكون بعد البداية."); return
    s_, e_ = sd.isoformat(), (ed + timedelta(days=1)).isoformat()
    delivered = df("SELECT * FROM orders WHERE rider_id=? AND status='تم التسليم' AND delivered_at>=? AND delivered_at<?", (rid, s_ + " 00:00:00", e_ + " 00:00:00"))
    settled = df("SELECT DISTINCT si.order_id FROM settlement_items si JOIN settlements s ON s.id=si.settlement_id WHERE s.kind='طيار_كاش' AND COALESCE(s.voided,0)=0 AND si.order_id IN (SELECT id FROM orders WHERE rider_id=? AND status='تم التسليم' AND delivered_at>=? AND delivered_at<?)", (rid, s_ + " 00:00:00", e_ + " 00:00:00"))
    sids = set(settled["order_id"].tolist()) if not settled.empty else set()
    earned = float(delivered["rider_commission"].sum()) if not delivered.empty else 0.0
    paid_c = float(delivered[delivered["id"].isin(sids)]["rider_commission"].sum()) if not delivered.empty else 0.0
    os_ = rider_unsettled_orders(rid, s_, e_)
    cash_open = float(os_["remaining_cash"].sum()) if not os_.empty else 0.0
    net = round(cash_open - (float(os_["rider_commission"].sum()) if not os_.empty else 0) - (float(os_["reward"].sum()) if not os_.empty else 0) + (float(os_["discount"].sum()) if not os_.empty else 0), 2)
    metric_grid([("طلبات مسلّمة", len(delivered), f"{PAY_MODES.get(r['pay_mode'], '')}", "info"), ("إجمالي العمولة", f"{earned:,.2f} ج", "المكتسبة", "good"), ("عمولة مُسوّاة", f"{paid_c:,.2f} ج", "ضمن تصفية الكاش", "info"), ("عمولة متبقية", f"{earned - paid_c:,.2f} ج", "تدخل في المستحقات", "warn"), ("كاش معك", f"{cash_open:,.2f} ج", "لم يُورَّد", "danger" if cash_open > 0 else "good"), ("صافي التوريد", f"{net:,.2f} ج", "توريد/صرف الآن", "good")])
    if os_.empty: st.success("✅ لا توجد طلبات كاش غير مصفاة في الفترة.")
    else: st.dataframe(os_[["order_no", "restaurant", "branch", "delivered_at", "rider_commission", "reward", "discount", "remaining_cash"]].rename(columns={"order_no": "الطلب", "restaurant": "المطعم", "branch": "الفرع", "delivered_at": "التسليم", "rider_commission": "العمولة", "reward": "المكافأة", "discount": "الخصم", "remaining_cash": "الكاش المتبقي"}), use_container_width=True, hide_index=True)
    if owner and not os_.empty and st.button("💰 تنفيذ تصفية الطيار الآن", type="primary", use_container_width=True):
        try: sid, due, n = create_rider_settlement(rid, s_, e_, user); st.success(f"تمت التصفية • {n} طلب • صافي التوريد {due:,.2f} ج"); st.rerun()
        except Exception as ex: st.error(str(ex))


# =========================================================
# شاشة الطيار — بسيطة: طلب واحد وزر واحد كبير
# =========================================================
RIDER_ACTIONS = {"تم القبول": "✅ قبول الطلب", "تم الاستلام": "📦 استلمت الطلب من المطعم", "في الطريق": "🛵 أنا في الطريق للعميل", "تم التسليم": "🏁 تم التسليم للعميل"}


def render_rider(user):
    r = rider_row(user["ref_id"])
    if not r: st.error("حساب الطيار غير مرتبط بسجل صالح — تواصل مع الإدارة."); return
    header(f"🛵 أهلاً {r['name']}", "طلبك الحالي وزر واحد للخطوة التالية.")
    my = df("SELECT o.*,rs.name restaurant,rs.phone restaurant_phone,b.name branch,b.address branch_address,b.lat branch_lat,b.lng branch_lng FROM orders o JOIN restaurants rs ON rs.id=o.restaurant_id JOIN branches b ON b.id=o.branch_id WHERE o.rider_id=? AND o.status NOT IN ('تم التسليم','ملغى') ORDER BY o.created_at", (r["id"],))
    fresh = gps_fresh(r)
    w = rider_wallet(r["id"])
    metric_grid([("طلبات نشطة", len(my), r["status"], "info"), ("GPS", "🟢 يعمل" if fresh else "🟠 افتح الخريطة", "موقعك", "good" if fresh else "warn"), ("حسابك المالي", f"{abs(w['due_to_rider']):,.0f} ج", "لك عند الشركة" if w["due_to_rider"] >= 0 else "عليك توريده", "good" if w["due_to_rider"] >= 0 else "warn")])
    route = None
    if my.empty:
        st.success("لا يوجد طلب نشط الآن — أنت جاهز، وستصلك نغمة عند وصول طلب جديد 🔔")
    else:
        cur = my.iloc[0].to_dict(); before_pickup = cur["status"] in ("جديد", "تم التعيين", "تم القبول")
        st.markdown(f'''<div class="rider-order"><div class="no">{esc(cur["order_no"])} &nbsp; {badge(cur["status"])}</div>
        <div class="row"><div class="ico">🏪</div><div><b>الاستلام:</b> {esc(cur["restaurant"])} — {esc(cur["branch"])}<br><span style="color:#9AA4B2">{esc(cur["branch_address"] or "")}</span></div></div>
        <div class="row"><div class="ico">📍</div><div><b>التسليم:</b> {esc(cur["delivery_address"])}{("<br>" + esc(cur.get("customer_name") or "")) if cur.get("customer_name") else ""}</div></div>
        <div class="row"><div class="ico">💵</div><div><b>التحصيل:</b> {"كاش — حصّل " + format(cur["cash_collected"], ",.0f") + " ج من المطعم" if cur["billing_mode"] == "كاش" else "آجل — لا تحصيل"}</div></div>
        <div class="earn">عمولتك من هذا الطلب: {cur["rider_commission"]:,.2f} ج</div></div>''', unsafe_allow_html=True)
        nxt = [a for a in transitions(cur["status"]) if a != "ملغى"]
        if nxt:
            st.markdown('<div class="rider-action">', unsafe_allow_html=True)
            if st.button(RIDER_ACTIONS.get(nxt[0], nxt[0]), type="primary", use_container_width=True, key=f"r_action_{cur['id']}_{nxt[0]}"):
                try: change_order_status(cur["id"], nxt[0], user); st.toast("تم ✅"); st.rerun()
                except Exception as ex: st.error(str(ex))
            st.markdown('</div>', unsafe_allow_html=True)
        a, b = st.columns(2)
        if before_pickup and cur.get("branch_lat") is not None:
            a.link_button("🧭 ملاحة للمطعم", f"https://www.google.com/maps/dir/?api=1&destination={cur['branch_lat']},{cur['branch_lng']}", use_container_width=True)
        elif cur.get("delivery_lat") is not None:
            a.link_button("🧭 ملاحة للعميل", f"https://www.google.com/maps/dir/?api=1&destination={cur['delivery_lat']},{cur['delivery_lng']}", use_container_width=True)
        if before_pickup and cur.get("restaurant_phone"): b.link_button("📞 اتصال بالمطعم", f"tel:{cur['restaurant_phone']}", use_container_width=True)
        elif cur.get("customer_phone"): b.link_button("📞 اتصال بالعميل", f"tel:{cur['customer_phone']}", use_container_width=True)
        tgt = [float(cur["branch_lat"]), float(cur["branch_lng"])] if before_pickup and cur.get("branch_lat") is not None else ([float(cur["delivery_lat"]), float(cur["delivery_lng"])] if cur.get("delivery_lat") is not None else None)
        if tgt and r.get("last_lat") is not None: route = {"from": [float(r["last_lat"]), float(r["last_lng"])], "to": tgt}
        if len(my) > 1:
            with st.expander(f"📋 طلبات قادمة ({len(my) - 1})"):
                for _, o in my.iloc[1:].iterrows(): st.markdown(f"**{esc(o['order_no'])}** — {esc(o['restaurant'])} ← {esc(o['delivery_address'])} — {badge(o['status'])}", unsafe_allow_html=True)
    gps_state = st.session_state.get("gps_status") or {}
    hint = "الإذن مرفوض: من إعدادات المتصفح > أذونات الموقع > السماح، ثم أعد تحميل الصفحة." if gps_state.get("code") == 1 else "اترك هذه الصفحة مفتوحة أثناء العمل ليصل موقعك للإدارة. اضغط «تشغيل موقعي» في الخريطة أول مرة."
    st.markdown(f'<div class="gps-panel"><div class="gps-title">📍 تتبع الموقع</div><div class="gps-sub">{hint}</div></div>', unsafe_allow_html=True)
    live_map_fragment(user, route=route)
    att = one("SELECT * FROM attendance WHERE rider_id=? AND work_date=?", (r["id"], today_str()))
    st.markdown("### ⏱️ يوم العمل")
    if not att or not att["clock_in"]:
        if st.button("🟢 تسجيل دخول", type="primary", use_container_width=True): upsert_attendance({"rider_id": r["id"], "work_date": today_str(), "clock_in": now_iso(), "clock_out": None, "break_minutes": 0, "status": "حاضر", "reason": ""}, user); st.rerun()
    elif not att["clock_out"]:
        st.info(f"دخلت الساعة {att['clock_in'][11:16]}")
        if st.button("🔴 تسجيل خروج", type="primary", use_container_width=True): upsert_attendance({"rider_id": r["id"], "work_date": today_str(), "clock_in": att["clock_in"], "clock_out": now_iso(), "break_minutes": int(att.get("break_minutes") or 0), "status": "حاضر", "reason": ""}, user); st.rerun()
    else: st.success(f"ساعات اليوم: {attendance_hours(att):.2f} ساعة")




# =========================================================
# حساب الطيار الموحد: عمولات الكاش + الآجل معاً — منفصل عن إقفال الشهر
# =========================================================
def rider_wallet(rider_id, start=None, end=None):
    s0 = start or "2000-01-01"; e0 = end or (today_d() + timedelta(days=1)).isoformat()
    os_ = rider_unsettled_orders(rider_id, s0, e0)
    z = {"orders": os_, "n": 0, "comm_cash": 0.0, "comm_credit": 0.0, "comm": 0.0, "rewards": 0.0, "discounts": 0.0, "cash_held": 0.0, "due_to_rider": 0.0}
    if os_.empty: return z
    cash = os_["billing_mode"] == "كاش"
    z.update(n=len(os_), comm_cash=float(os_.loc[cash, "rider_commission"].sum()), comm_credit=float(os_.loc[~cash, "rider_commission"].sum()),
             rewards=float(os_["reward"].sum()), discounts=float(os_["discount"].sum()), cash_held=float(os_["remaining_cash"].sum()))
    z["comm"] = z["comm_cash"] + z["comm_credit"]
    z["due_to_rider"] = round(z["comm"] + z["rewards"] - z["discounts"] - z["cash_held"], 2)   # + للطيار ، − عليه
    return z


def render_rider_wallet(user):
    header("حساب الطيار", "عمولات الكاش والآجل معاً في حساب واحد — تُصفّى في أي وقت، منفصلة تماماً عن إقفال الراتب الشهري.")
    rid = user.get("ref_id"); owner = actor_is_owner(user)
    if owner and not rid:
        riders = df("SELECT id,name FROM riders ORDER BY name")
        if riders.empty: st.info("لا يوجد طيارون."); return
        rid = riders.iloc[riders["name"].tolist().index(st.selectbox("اختر الطيار", riders["name"].tolist(), key="owner_wallet_rider"))]["id"]
    r = rider_row(rid)
    if not r: st.error("لا يوجد طيار مرتبط بهذه المساحة."); return
    a, b = st.columns(2); sd = a.date_input("من", value=today_d() - timedelta(days=30), key=f"ws_{rid}"); ed = b.date_input("إلى", value=today_d(), key=f"we_{rid}")
    if ed < sd: st.error("تاريخ النهاية يجب أن يكون بعد البداية."); return
    s_, e_ = sd.isoformat(), (ed + timedelta(days=1)).isoformat()
    w = rider_wallet(rid, s_, e_); d = w["due_to_rider"]
    metric_grid([("طلبات غير مسوّاة", w["n"], PAY_MODES.get(r["pay_mode"], ""), "info"), ("عمولة الكاش", f"{w['comm_cash']:,.2f} ج", "تُخصم من الكاش", "good"), ("عمولة الآجل", f"{w['comm_credit']:,.2f} ج", "مستحقة له", "good"),
                 ("كاش مع الطيار", f"{w['cash_held']:,.2f} ج", "لم يُورَّد", "danger" if w["cash_held"] > 0 else "good"),
                 ("الصافي", f"{abs(d):,.2f} ج", "مستحق له ⬅ ندفع له" if d > 0 else ("عليه ⬅ يورّد للشركة" if d < 0 else "متزن"), "good" if d >= 0 else "warn")])
    st.markdown('<div class="highlight"><b>طريقة الحساب:</b> الصافي = عمولات الكاش + عمولات الآجل + المكافآت − الخصومات − الكاش الذي معه. هذا الحساب مستقل عن الراتب الشهري، وعند التصفية تُغلق كل الطلبات المعروضة معاً.</div>', unsafe_allow_html=True)
    if w["orders"].empty: st.success("✅ لا توجد طلبات غير مسوّاة في الفترة.")
    else:
        v = w["orders"][["order_no", "restaurant", "billing_mode", "delivered_at", "rider_commission", "reward", "discount", "remaining_cash"]]
        st.dataframe(v.rename(columns={"order_no": "الطلب", "restaurant": "المطعم", "billing_mode": "التحصيل", "delivered_at": "التسليم", "rider_commission": "العمولة", "reward": "المكافأة", "discount": "الخصم", "remaining_cash": "الكاش معه"}), use_container_width=True, hide_index=True)
    if owner and not w["orders"].empty and st.button("💰 تصفية حساب الطيار الآن", type="primary", use_container_width=True):
        try: sid, due, n = create_rider_settlement(rid, s_, e_, user); st.success(f"تمت التصفية • {n} طلب • " + (f"على الطيار توريد {due:,.2f} ج" if due > 0 else f"ندفع للطيار {abs(due):,.2f} ج")); st.rerun()
        except Exception as ex: st.error(str(ex))
    hist = df("SELECT created_at,kind,gross,commissions,cash_due FROM settlements WHERE party_id=? AND COALESCE(voided,0)=0 AND kind IN ('حساب_طيار','طيار_كاش') ORDER BY created_at DESC LIMIT 15", (rid,))
    if not hist.empty:
        with st.expander("سجل التصفيات السابقة"): st.dataframe(hist.rename(columns={"created_at": "الوقت", "kind": "النوع", "gross": "الكاش", "commissions": "العمولات", "cash_due": "الصافي"}), use_container_width=True, hide_index=True)


# =========================================================
# فحص وعلاج الأخطاء
# =========================================================
def health_checks():
    issues = []
    for r in df("SELECT id,name,active_orders,status FROM riders").to_dict("records"):
        real = one("SELECT COUNT(*) n FROM orders WHERE rider_id=? AND status NOT IN ('تم التسليم','ملغى')", (r["id"],))["n"]
        if int(r["active_orders"] or 0) != real: issues.append({"id": f"cnt:{r['id']}", "text": f"عداد طلبات الطيار {r['name']} = {r['active_orders']} والفعلي {real}", "fix": True})
        elif r["status"] != "غير نشط" and r["status"] != ("في مهمة" if real else "متاح"): issues.append({"id": f"stat:{r['id']}", "text": f"حالة الطيار {r['name']} «{r['status']}» لا تطابق طلباته الفعلية", "fix": True})
    for o in df("SELECT o.id,o.order_no FROM orders o WHERE o.status='تم التسليم' AND NOT EXISTS (SELECT 1 FROM ledger l WHERE l.reference_id=o.id AND l.txn_type='إيراد خدمة توصيل')").to_dict("records"):
        issues.append({"id": f"acc:{o['id']}", "text": f"طلب {o['order_no']} مسلّم بدون قيد استحقاق", "fix": True})
    for o in df("SELECT id,order_no FROM orders WHERE status!='ملغى' AND COALESCE(comm_settled,0)=0 AND ((billing_mode='كاش' AND ABS(cash_collected-delivery_fee)>0.01) OR (billing_mode='آجل' AND cash_collected!=0))").to_dict("records"):
        issues.append({"id": f"cash:{o['id']}", "text": f"طلب {o['order_no']}: مبلغ الكاش لا يطابق رسوم الخدمة/طريقة التحصيل", "fix": True})
    for o in df("SELECT o.id,o.order_no,o.distance_km,o.delivery_fee,o.rider_commission,o.rider_id FROM orders o WHERE o.status NOT IN ('تم التسليم','ملغى')").to_dict("records"):
        if abs(commission_for_order(o["distance_km"], o["delivery_fee"], rider_row(o["rider_id"])) - float(o["rider_commission"])) > 0.01:
            issues.append({"id": f"comm:{o['id']}", "text": f"طلب نشط {o['order_no']}: العمولة لا تطابق نظام قبض الطيار (قد تكون معدّلة يدوياً)", "fix": True})
    for o in df("SELECT id,order_no FROM orders WHERE COALESCE(comm_settled,0)=1 AND (comm_settlement_id IS NULL OR comm_settlement_id NOT IN (SELECT id FROM settlements WHERE COALESCE(voided,0)=0))").to_dict("records"):
        issues.append({"id": f"sett:{o['id']}", "text": f"طلب {o['order_no']} مُعلَّم كمسوّى وليس له تسوية سارية", "fix": True})
    lim = (now_dt() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    for o in df("SELECT order_no,status FROM orders WHERE status NOT IN ('تم التسليم','ملغى') AND created_at<?", (lim,)).to_dict("records"):
        issues.append({"id": f"stuck:{o['order_no']}", "text": f"طلب {o['order_no']} ({o['status']}) مفتوح من أكثر من 24 ساعة — أغلقه أو ألغه", "fix": False})
    for o in df("SELECT o.order_no,r.name FROM orders o JOIN riders r ON r.id=o.rider_id WHERE o.status NOT IN ('تم التسليم','ملغى') AND r.status='غير نشط'").to_dict("records"):
        issues.append({"id": f"inact:{o['order_no']}", "text": f"طلب {o['order_no']} معيّن لطيار غير نشط ({o['name']})", "fix": False})
    for a in df("SELECT a.work_date,r.name FROM attendance a JOIN riders r ON r.id=a.rider_id WHERE a.clock_in IS NOT NULL AND a.clock_out IS NULL AND a.work_date<?", (today_str(),)).to_dict("records"):
        issues.append({"id": f"att:{a['name']}:{a['work_date']}", "text": f"{a['name']}: دخول بدون خروج يوم {a['work_date']} — عدّله من الحضور", "fix": False})
    return issues


def fix_issue(issue_id, actor):
    need_owner(actor, "العلاج للمالك فقط.")
    kind, _, ref = issue_id.partition(":")
    with get_conn() as c:
        if kind in ("cnt", "stat"):
            real = c.execute("SELECT COUNT(*) FROM orders WHERE rider_id=? AND status NOT IN ('تم التسليم','ملغى')", (ref,)).fetchone()[0]
            c.execute("UPDATE riders SET active_orders=? WHERE id=?", (real, ref))
            c.execute("UPDATE riders SET status=? WHERE id=? AND status!='غير نشط'", ("في مهمة" if real else "متاح", ref))
        elif kind == "acc":
            o = c.execute("SELECT * FROM orders WHERE id=?", (ref,)).fetchone()
            c.execute("INSERT INTO ledger(txn_no,txn_type,account_type,account_id,amount,direction,reference_id,description,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)", (uid("TXN"), "إيراد خدمة توصيل", "إيراد_مستحق", o["restaurant_id"], float(o["delivery_fee"]), "استحقاق", ref, "علاج: إثبات استحقاق ناقص", actor["id"], now_iso()))
        elif kind == "cash":
            c.execute("UPDATE orders SET cash_collected=CASE WHEN billing_mode='كاش' THEN delivery_fee ELSE 0 END WHERE id=?", (ref,))
        elif kind == "sett":
            c.execute("UPDATE orders SET comm_settled=0,comm_settlement_id=NULL WHERE id=?", (ref,))
        elif kind == "comm":
            o = c.execute("SELECT * FROM orders WHERE id=?", (ref,)).fetchone()
            rd = c.execute("SELECT * FROM riders WHERE id=?", (o["rider_id"],)).fetchone() if o["rider_id"] else None
            c.execute("UPDATE orders SET rider_commission=? WHERE id=?", (commission_for_order(o["distance_km"], o["delivery_fee"], dict(rd) if rd else None), ref))
        else: raise ValueError("هذه المشكلة تحتاج تدخلاً يدوياً.")
    audit(actor["id"], "health_fix", "system", issue_id)


def fix_all_issues(actor):
    n = 0
    for i in health_checks():
        if i["fix"]:
            try: fix_issue(i["id"], actor); n += 1
            except Exception: pass
    return n


# =========================================================
# المساعد الذكي — أوامر بالصوت/الكتابة تُنفَّذ على النظام نفسه (بيانات وإعدادات، لا تعديل في الكود)
# =========================================================
AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
NUM_SETTINGS = {"salary_basic": "المرتب الافتراضي", "working_days": "أيام العمل الشهري", "daily_work_hours": "ساعات العمل/اليوم", "excused_leave_days": "خصم إجازة بعذر (أيام)", "unexcused_leave_days": "خصم إجازة بدون عذر (أيام)",
                "commission_base_km": "العمولة الأساسية حتى (كم)", "commission_base": "العمولة الأساسية (ج)", "commission_extra_per_km": "لكل كم زائد (ج)", "gps_fresh_seconds": "GPS حديث حتى (ثانية)", "order_overdue_grace_minutes": "سماح التأخير (دقيقة)"}
PAGE_LABELS = {"dashboard": "الرئيسية", "orders": "الطلبات", "map": "الخريطة", "navigation": "الملاحة", "riders": "الطيارون", "rider_wallet": "حساب الطيار", "restaurants": "المطاعم", "attendance": "الحضور", "payroll": "المرتبات", "settlements": "التسويات", "analysis": "التحليل", "users": "المستخدمون", "tools": "الأدوات"}
EDITABLE = {"rider": ("riders", "name", {"name", "phone", "salary"}), "restaurant": ("restaurants", "name", {"name", "phone", "billing_mode"}), "branch": ("branches", "name", {"name", "address"}),
            "user": ("users", "name", {"name"}), "order": ("orders", "order_no", {"delivery_address", "notes", "customer_phone", "customer_name", "eta_minutes"})}
ACTIONS = {}


def _norm(s):
    s = str(s or "").strip().lower()
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ة", "ه"), ("ى", "ي"), ("ؤ", "و"), ("ئ", "ي")): s = s.replace(a, b)
    return " ".join(s.split())


def _find(table, col, name, where=""):
    rows = df(f"SELECT * FROM {table} {where}").to_dict("records"); n = _norm(name)
    ex = [r for r in rows if _norm(r[col]) == n]
    if len(ex) == 1: return ex[0]
    part = [r for r in rows if n and (n in _norm(r[col]) or _norm(r[col]) in n)]
    if len(part) == 1 and not ex: return part[0]
    if not part and not ex: raise ValueError(f"لم أجد «{name}».")
    raise ValueError(f"الاسم «{name}» يطابق أكثر من سجل — وضّح الاسم كاملاً.")


def _order(no):
    o = one("SELECT * FROM orders WHERE lower(order_no)=lower(?)", (str(no).strip(),))
    if not o: raise ValueError(f"لا يوجد طلب برقم {no}.")
    return o


def action(type_, title, args_doc, danger=False):
    def deco(fn): ACTIONS[type_] = {"title": title, "args": args_doc, "danger": danger, "fn": fn}; return fn
    return deco


def recompute_all_active():
    for r in df("SELECT DISTINCT rider_id FROM orders WHERE rider_id IS NOT NULL AND status NOT IN ('تم التسليم','ملغى')")["rider_id"].tolist(): recompute_active_commissions(r)
    with get_conn() as c:
        for o in c.execute("SELECT id,distance_km,delivery_fee FROM orders WHERE rider_id IS NULL AND status='جديد'").fetchall(): c.execute("UPDATE orders SET rider_commission=? WHERE id=?", (commission_for_order(o["distance_km"], o["delivery_fee"], None), o["id"]))


@action("set_setting", "تغيير إعداد عام", {"key": "one of: " + ", ".join(NUM_SETTINGS) + ", ui_accent (لون #RRGGBB), ui_brand (اسم التطبيق)", "value": "رقم أو لون أو نص"})
def _a_set_setting(a, actor):
    need_owner(actor, "للمالك فقط."); key, val = a.get("key"), a.get("value"); old = get_setting(key)
    if key in NUM_SETTINGS:
        v = _num(val)
        if v is None or v < 0: raise ValueError("القيمة يجب أن تكون رقماً موجباً.")
        set_setting(key, v); val = v
        if key.startswith("commission"): recompute_all_active()
    elif key == "ui_accent":
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(val)): raise ValueError("اللون يجب أن يكون بصيغة #RRGGBB.")
        set_setting(key, val)
    elif key == "ui_brand":
        if not (2 <= len(str(val).strip()) <= 40): raise ValueError("اسم التطبيق من 2 إلى 40 حرفاً.")
        set_setting(key, str(val).strip())
    else: raise ValueError("هذا الإعداد غير مسموح بتغييره.")
    audit(actor["id"], "ai_set_setting", "setting", key, before={"v": old}, after={"v": val}); return f"تم تغيير «{NUM_SETTINGS.get(key, key)}» من {old} إلى {val}.", None


@action("set_rider_pay", "تغيير نظام قبض طيار", {"rider": "اسم الطيار", "pay_mode": "MONTHLY | DISTANCE | COMPANY_CUT", "salary": "اختياري", "comm_base_km": "اختياري", "comm_base": "اختياري", "comm_extra_km": "اختياري", "company_cut": "اختياري: حصة الشركة الثابتة لكل أوردر"})
def _a_rider_pay(a, actor):
    r = _find("riders", "name", a["rider"]); g = lambda k: a[k] if a.get(k) is not None else r.get(k)
    update_rider(r["id"], {"pay_mode": a.get("pay_mode") or r["pay_mode"], "phone": r.get("phone") or "", "salary": g("salary"), "comm_base_km": g("comm_base_km"), "comm_base": g("comm_base"), "comm_extra_km": g("comm_extra_km"), "company_cut": g("company_cut")}, actor)
    return f"تم تحديث نظام قبض {r['name']} إلى {PAY_MODES.get(a.get('pay_mode') or r['pay_mode'])}.", None


@action("set_order_financials", "تعديل حسابات طلب (نشط أو مكتمل)", {"order_no": "رقم الطلب", "delivery_fee": "اختياري", "rider_commission": "اختياري", "reward": "اختياري", "discount": "اختياري", "billing_mode": "كاش | آجل — اختياري", "distance_km": "اختياري"})
def _a_order_fin(a, actor):
    o = _order(a["order_no"]); pick = lambda k: a[k] if a.get(k) is not None else o[k]
    if o["status"] == "تم التسليم":
        owner_edit_closed_order(o["id"], {"delivery_fee": pick("delivery_fee"), "rider_commission": pick("rider_commission"), "reward": pick("reward"), "discount": pick("discount"), "billing_mode": pick("billing_mode"), "distance_km": pick("distance_km")}, actor)
    elif order_active(o["status"]):
        update_order(o["id"], {"delivery_address": o["delivery_address"], "delivery_lat": o["delivery_lat"], "delivery_lng": o["delivery_lng"], "distance_km": pick("distance_km"), "eta_minutes": o["eta_minutes"], "notes": o["notes"] or "", "delivery_fee": pick("delivery_fee"), "billing_mode": pick("billing_mode"), "reward": pick("reward"), "discount": pick("discount"), "customer_phone": o.get("customer_phone") or "", "customer_name": o.get("customer_name") or "", "rider_commission": a.get("rider_commission")}, actor)
    else: raise ValueError("الطلب ملغى ولا يمكن تعديل حساباته.")
    return f"تم تعديل حسابات الطلب {o['order_no']}.", None


@action("assign_rider", "تعيين/تغيير طيار لطلب", {"order_no": "رقم الطلب", "rider": "اسم الطيار أو null لإزالة التعيين"})
def _a_assign(a, actor):
    o = _order(a["order_no"]); r = _find("riders", "name", a["rider"]) if a.get("rider") else None
    assign_rider(o["id"], r["id"] if r else None, actor); return f"تم تعيين {r['name'] if r else 'لا أحد'} للطلب {o['order_no']}.", None


@action("cancel_order", "إلغاء طلب", {"order_no": "رقم الطلب"}, danger=True)
def _a_cancel(a, actor):
    o = _order(a["order_no"]); change_order_status(o["id"], "ملغى", actor); return f"تم إلغاء الطلب {o['order_no']}.", None


@action("settle_rider", "تصفية حساب طيار (كاش + آجل)", {"rider": "اسم الطيار", "from_date": "YYYY-MM-DD اختياري", "to_date": "YYYY-MM-DD اختياري"}, danger=True)
def _a_settle(a, actor):
    r = _find("riders", "name", a["rider"]); end = a.get("to_date") or today_str()
    sid, due, n = create_rider_settlement(r["id"], a.get("from_date") or "2000-01-01", (datetime.strptime(end, "%Y-%m-%d").date() + timedelta(days=1)).isoformat(), actor)
    return f"تمت تصفية {r['name']}: {n} طلب — " + (f"عليه توريد {due:,.2f} ج" if due > 0 else f"ندفع له {abs(due):,.2f} ج"), None


@action("void_last_settlement", "إلغاء آخر تسوية لطيار أو مطعم", {"party": "اسم الطيار أو المطعم"}, danger=True)
def _a_void(a, actor):
    n = _norm(a["party"]); ids = [x["id"] for x in df("SELECT id,name FROM riders UNION ALL SELECT id,name FROM restaurants").to_dict("records") if _norm(x["name"]) == n or (n and n in _norm(x["name"]))]
    if len(ids) != 1: raise ValueError("حدد اسم الطيار/المطعم بدقة.")
    s = one("SELECT id FROM settlements WHERE party_id=? AND COALESCE(voided,0)=0 AND kind IN ('حساب_طيار','طيار_كاش','مطعم') ORDER BY created_at DESC LIMIT 1", (ids[0],))
    if not s: raise ValueError("لا توجد تسوية سارية.")
    void_settlement(s["id"], actor); return "تم إلغاء آخر تسوية وعادت الطلبات غير مصفاة.", None


@action("toggle_active", "تفعيل/تعطيل سجل", {"entity": "rider | restaurant | branch | user", "name": "الاسم", "active": "true/false"})
def _a_toggle(a, actor):
    ent = a["entity"]; tbl, col, _ = EDITABLE.get(ent, (None,) * 3)
    if ent not in ("rider", "restaurant", "branch", "user"): raise ValueError("نوع غير مدعوم.")
    r = _find(tbl, col, a["name"]); set_active(ent, r["id"], bool(a.get("active")), actor); return f"تم {'تفعيل' if a.get('active') else 'تعطيل'} {r[col]}.", None


@action("create_rider", "إضافة طيار", {"name": "الاسم", "phone": "اختياري", "pay_mode": "MONTHLY | DISTANCE | COMPANY_CUT", "salary": "اختياري", "company_cut": "اختياري"})
def _a_new_rider(a, actor): create_rider({"name": a["name"], "phone": a.get("phone", ""), "pay_mode": a.get("pay_mode", "MONTHLY"), "salary": a.get("salary"), "company_cut": a.get("company_cut")}, actor); return f"تمت إضافة الطيار {a['name']}.", None


@action("create_restaurant", "إضافة مطعم", {"name": "الاسم", "phone": "اختياري", "billing_mode": "كاش | آجل"})
def _a_new_rest(a, actor): create_restaurant({"name": a["name"], "phone": a.get("phone", ""), "billing_mode": a.get("billing_mode", "كاش")}, actor); return f"تمت إضافة المطعم {a['name']} (أضف له فرعاً من صفحة المطاعم).", None


@action("payroll_adjustment", "إضافة/خصم/سلفة على مرتب طيار", {"rider": "اسم الطيار", "type": "إضافة | خصم | سلفة", "amount": "رقم", "period": "YYYY-MM اختياري", "description": "اختياري"})
def _a_padj(a, actor):
    r = _find("riders", "name", a["rider"]); add_payroll_adjustment({"rider_id": r["id"], "period": a.get("period") or month_key(), "type": a["type"], "amount": a["amount"], "description": a.get("description", "")}, actor)
    return f"تم تسجيل {a['type']} {a['amount']} ج على {r['name']}.", None


@action("reset_pin", "توليد PIN جديد لمستخدم", {"user": "اسم المستخدم أو بريده"}, danger=True)
def _a_pin(a, actor):
    u = _find("users", "name", a["user"]) if "@" not in str(a["user"]) else one("SELECT * FROM users WHERE lower(email)=lower(?)", (a["user"],))
    if not u: raise ValueError("المستخدم غير موجود.")
    pin = reset_user_pin(u["id"], actor); return f"PIN الجديد لـ {u['name']}: {pin} (يظهر مرة واحدة).", f"تم توليد PIN جديد لـ {u['name']}"


@action("edit_record", "تعديل حقل في سجل", {"entity": "rider | restaurant | branch | user | order", "name": "الاسم أو رقم الطلب", "field": "name/phone/salary/address/notes/billing_mode/delivery_address/customer_phone/customer_name/eta_minutes حسب النوع", "value": "القيمة الجديدة"})
def _a_edit(a, actor):
    need_owner(actor, "للمالك فقط."); ent = a.get("entity")
    if ent not in EDITABLE: raise ValueError("نوع غير مدعوم.")
    tbl, col, fields = EDITABLE[ent]
    if a.get("field") not in fields: raise ValueError(f"الحقل غير مسموح. المسموح: {', '.join(sorted(fields))}")
    r = _order(a["name"]) if ent == "order" else _find(tbl, col, a["name"]); val = a.get("value")
    if a["field"] == "billing_mode" and val not in ("كاش", "آجل"): raise ValueError("التحصيل: كاش أو آجل.")
    if a["field"] in ("salary", "eta_minutes"):
        val = _num(val)
        if val is None or val < 0: raise ValueError("القيمة يجب أن تكون رقماً.")
    with get_conn() as c: c.execute(f"UPDATE {tbl} SET {a['field']}=? WHERE id=?", (val, r["id"]))
    audit(actor["id"], "ai_edit", ent, r["id"], before={a["field"]: r.get(a["field"])}, after={a["field"]: val}); return f"تم تعديل {a['field']} لـ {r[col]}.", None


@action("page_visibility", "إظهار/إخفاء صفحة لغير المالك", {"page": "one of: " + ", ".join(PAGE_LABELS), "visible": "true/false"})
def _a_vis(a, actor):
    need_owner(actor, "للمالك فقط."); p = a.get("page")
    if p not in PAGE_LABELS: raise ValueError("صفحة غير معروفة.")
    hidden = {x for x in (get_setting("hidden_pages", "") or "").split(",") if x}
    (hidden.discard if a.get("visible") else hidden.add)(p); set_setting("hidden_pages", ",".join(sorted(hidden)))
    audit(actor["id"], "ai_page_visibility", "setting", p, after={"visible": bool(a.get("visible"))}); return f"تم {'إظهار' if a.get('visible') else 'إخفاء'} صفحة «{PAGE_LABELS[p]}» لغير المالك.", None


@action("run_health_fix", "فحص النظام وعلاج الأخطاء القابلة للعلاج تلقائياً", {})
def _a_health(a, actor): n = fix_all_issues(actor); left = len(health_checks()); return f"تم علاج {n} مشكلة. المتبقي للمراجعة اليدوية: {left}.", None


def describe_action(a):
    spec = ACTIONS.get(a.get("type"))
    if not spec: return f"❓ إجراء غير معروف: {a.get('type')}"
    args = "، ".join(f"{k}: {v}" for k, v in (a.get("args") or {}).items() if v is not None)
    return f"{'⚠️ ' if spec['danger'] else '🔧 '}{spec['title']} — {args}"


def execute_action(a, actor):
    spec = ACTIONS.get(a.get("type"))
    if not spec: raise ValueError("إجراء غير مسموح.")
    return spec["fn"](a.get("args") or {}, actor)


# ---------- الفهم: نموذج ذكاء اصطناعي إن وُجد مفتاح، وإلا قواعد مدمجة ----------
def ai_key():
    try: k = st.secrets.get("ANTHROPIC_API_KEY")
    except Exception: k = None
    return k or os.environ.get("ANTHROPIC_API_KEY") or get_setting("ai_api_key", "") or None


def llm_plan(command):
    ctx = {"today": today_str(), "current_month": month_key(), "riders": [f"{r['name']} ({r['pay_mode']})" for r in df("SELECT name,pay_mode FROM riders").to_dict("records")],
           "restaurants": df("SELECT name FROM restaurants")["name"].tolist(), "settings": {k: get_setting(k) for k in list(NUM_SETTINGS) + ["ui_accent", "ui_brand"]}, "pay_modes": PAY_MODES}
    catalog = "\n".join(f"- {t}: {s['title']} | args: {json.dumps(s['args'], ensure_ascii=False)}" for t, s in ACTIONS.items())
    system = ("أنت مساعد تشغيل لتطبيق توصيل (شركة تأخذ رسوم خدمة توصيل فقط من المطاعم). حوّل أمر المالك (عربي مصري غالباً، قد يكون منطوقاً وفيه أخطاء إملائية) إلى قائمة إجراءات من القائمة المسموحة فقط، عبر أداة submit_plan.\n"
              "قواعد: لا تخترع إجراءات أو أسماء؛ استخدم الأسماء كما في السياق. إن كان الأمر غامضاً أو ناقصاً أرجع actions فارغة واكتب سؤالاً في clarification. لا تنفّذ شيئاً لم يُطلب. الأرقام بالإنجليزية. التواريخ YYYY-MM-DD.\n"
              f"الإجراءات المسموحة:\n{catalog}\n\nالسياق الحالي:\n{json.dumps(ctx, ensure_ascii=False)}")
    tool = {"name": "submit_plan", "description": "قدّم خطة التنفيذ", "input_schema": {"type": "object", "properties": {"understood": {"type": "string", "description": "ملخص عربي قصير لما فهمته"}, "clarification": {"type": "string"},
            "actions": {"type": "array", "items": {"type": "object", "properties": {"type": {"type": "string", "enum": list(ACTIONS)}, "args": {"type": "object"}}, "required": ["type", "args"]}}}, "required": ["actions"]}}
    body = {"model": os.environ.get("ONWAY_AI_MODEL", "claude-sonnet-5-5"), "max_tokens": 1500, "system": system, "tools": [tool], "tool_choice": {"type": "tool", "name": "submit_plan"}, "messages": [{"role": "user", "content": command}]}
    req = Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode("utf-8"), headers={"content-type": "application/json", "x-api-key": ai_key(), "anthropic-version": "2023-06-01"})
    try:
        with urlopen(req, timeout=45) as r: data = json.loads(r.read().decode("utf-8"))
    except Exception as ex:
        raise ValueError(f"تعذر الاتصال بالذكاء الاصطناعي: {getattr(ex, 'code', '')} {ex}")
    for b in data.get("content", []):
        if b.get("type") == "tool_use": return b["input"]
    raise ValueError("لم يرجع النموذج خطة.")


def rule_plan(text):
    t = _norm(text.translate(AR_DIGITS)); acts = []; m = re.search(r"(\d+(?:\.\d+)?)", t); n = float(m.group(1)) if m else None
    riders = df("SELECT name FROM riders")["name"].tolist(); rests = df("SELECT name FROM restaurants")["name"].tolist()
    rider = next((x for x in riders if _norm(x) in t), None); rest = next((x for x in rests if _norm(x) in t), None)
    if any(w in t for w in ("افحص", "اصلح", "علاج", "فحص")) and any(w in t for w in ("النظام", "الاخطاء", "المشاكل", "مشاكل")): acts.append({"type": "run_health_fix", "args": {}})
    for kw, key in (("العموله الاساسيه", "commission_base"), ("كم زايد", "commission_extra_per_km"), ("كل كم", "commission_extra_per_km"), ("حتي كم", "commission_base_km"), ("المرتب", "salary_basic"), ("ايام العمل", "working_days"), ("ساعات العمل", "daily_work_hours"), ("سماح", "order_overdue_grace_minutes")):
        if kw in t and n is not None and not rider: acts.append({"type": "set_setting", "args": {"key": key, "value": n}}); break
    mo = re.search(r"on-\d{6}-\d+", t)
    if mo and ("الغ" in t or "الغي" in t): acts.append({"type": "cancel_order", "args": {"order_no": mo.group(0)}})
    if "تصفي" in t and rider: acts.append({"type": "settle_rider", "args": {"rider": rider}})
    if rider or rest:
        ent, nm = ("rider", rider) if rider else ("restaurant", rest)
        if any(w in t for w in ("عطل", "وقف", "ايقاف")): acts.append({"type": "toggle_active", "args": {"entity": ent, "name": nm, "active": False}})
        elif "فعل" in t: acts.append({"type": "toggle_active", "args": {"entity": ent, "name": nm, "active": True}})
    if rider:
        if "شهري" in t or "راتب" in t and "شهر" in t: acts.append({"type": "set_rider_pay", "args": {"rider": rider, "pay_mode": "MONTHLY", **({"salary": n} if n else {})}})
        elif "حصه" in t: acts.append({"type": "set_rider_pay", "args": {"rider": rider, "pay_mode": "COMPANY_CUT", **({"company_cut": n} if n is not None else {})}})
        elif "مسافه" in t: acts.append({"type": "set_rider_pay", "args": {"rider": rider, "pay_mode": "DISTANCE"}})
    if "لون" in t:
        hx = re.search(r"#[0-9a-f]{6}", t); cm = {"ازرق": "#2F80ED", "اخضر": "#00C27A", "احمر": "#FF4D4D", "بنفسجي": "#8B5CF6", "برتقالي": "#FF5A00", "اصفر": "#FFB020", "وردي": "#EC4899"}
        col = hx.group(0) if hx else next((v for k, v in cm.items() if k in t), None)
        if col: acts.append({"type": "set_setting", "args": {"key": "ui_accent", "value": col}})
    if not acts: return {"understood": "", "actions": [], "clarification": "لم أفهم الأمر بالقواعد المدمجة. فعّل مفتاح الذكاء الاصطناعي (أسفل) ليفهم أي صياغة، أو جرّب: «خلي العمولة الأساسية 12»، «فعّل الطيار أحمد»، «غيّر اللون أزرق»."}
    return {"understood": "فهمت الأمر بالقواعد المدمجة", "actions": acts}


def make_plan(command):
    return llm_plan(command) if ai_key() else rule_plan(command)


def log_command(actor, command, plan, result):
    with get_conn() as c: c.execute("INSERT INTO ai_commands(actor_id,command,plan_json,result,created_at) VALUES (?,?,?,?,?)", (actor["id"], command, json.dumps(plan, ensure_ascii=False, default=str), result, now_iso()))


def render_assistant(user):
    header("🎙️ المساعد الذكي", "قل أو اكتب ما تريد تعديله — يفهم، يعرض عليك الخطة، وينفّذها بعد موافقتك. يعالج البيانات والإعدادات بدون أي تعديل في الكود.")
    if not actor_is_owner(user): st.warning("هذه الصفحة للمالك فقط."); return
    actor = st.session_state.user
    speak = st.session_state.pop("_speak", "")
    if VOICE_COMPONENT is not None:
        res = VOICE_COMPONENT(key="voice_cmd", data={"speak": speak, "token": f"{time.time()}" if speak else ""})
        sp = _payload(res, "speech") if res else None
        if sp and sp.get("ts") != st.session_state.get("_voice_ts"):
            st.session_state["_voice_ts"] = sp.get("ts"); st.session_state["ai_cmd"] = sp.get("text", ""); st.session_state["_ai_go"] = True
    else: st.info("الميكروفون يحتاج Streamlit حديث — يمكنك الكتابة.")
    st.caption("🔑 " + ("الذكاء الاصطناعي مفعّل — يفهم أي صياغة." if ai_key() else "وضع القواعد المدمجة (محدود). فعّل مفتاح الذكاء الاصطناعي من الأسفل لفهم أي صياغة."))
    cmd = st.text_area("الأمر", key="ai_cmd", placeholder="مثال: خلّي أحمد يقبض حصة ثابتة للشركة 8 جنيه على كل أوردر • عدّل عمولة الطلب ON-260930-004 إلى 25 • اقفل حساب محمد • غيّر لون التطبيق أزرق", height=90)
    go = st.button("🧠 افهم الأمر", type="primary", use_container_width=True) or st.session_state.pop("_ai_go", False)
    if go and cmd.strip():
        try:
            with st.spinner("أفهم الأمر…"): st.session_state["ai_plan"] = make_plan(cmd.strip()); st.session_state["ai_plan_cmd"] = cmd.strip()
        except Exception as ex: st.error(str(ex)); st.session_state.pop("ai_plan", None)
    plan = st.session_state.get("ai_plan")
    if plan:
        if plan.get("understood"): st.markdown(f'<div class="highlight"><b>فهمت:</b> {esc(plan["understood"])}</div>', unsafe_allow_html=True)
        if plan.get("clarification"): st.warning(plan["clarification"])
        acts = [a for a in plan.get("actions", []) if a.get("type") in ACTIONS]
        picks = []
        for i, a in enumerate(acts):
            if st.checkbox(describe_action(a), value=True, key=f"ai_pick_{i}"): picks.append(a)
        if acts:
            c1, c2 = st.columns(2)
            if c1.button(f"✅ نفّذ ({len(picks)})", type="primary", use_container_width=True, disabled=not picks):
                shown, logs = [], []
                for a in picks:
                    try: d, lg = execute_action(a, actor); shown.append("✅ " + d); logs.append("✅ " + (lg or d))
                    except Exception as ex: shown.append(f"❌ {describe_action(a)} — {ex}"); logs.append(f"❌ {ex}")
                log_command(actor, st.session_state.get("ai_plan_cmd", ""), plan, "\n".join(logs))
                st.session_state["ai_results"] = shown; st.session_state["_speak"] = "تم التنفيذ. " + ("، ".join(x[2:60] for x in shown if x.startswith("✅"))[:200] or "لكن حدثت أخطاء")
                for k in [k for k in st.session_state if k.startswith("ai_pick_")]: st.session_state.pop(k)
                st.session_state.pop("ai_plan", None); st.rerun()
            if c2.button("إلغاء", use_container_width=True): st.session_state.pop("ai_plan", None); st.rerun()
    for line in st.session_state.pop("ai_results", []): (st.success if line.startswith("✅") else st.error)(line)

    with st.expander("🩺 فحص النظام وعلاج الأخطاء", expanded=True):
        issues = health_checks()
        if not issues: st.success("✅ لا توجد مشاكل — البيانات سليمة ومتسقة.")
        else:
            st.warning(f"عدد المشاكل: {len(issues)}")
            for i in issues:
                c1, c2 = st.columns([4, 1]); c1.write(("🔧 " if i["fix"] else "👀 ") + i["text"])
                if i["fix"] and c2.button("علاج", key=f"fix_{i['id']}", use_container_width=True):
                    try: fix_issue(i["id"], actor); st.rerun()
                    except Exception as ex: st.error(str(ex))
            if any(i["fix"] for i in issues) and st.button("🔧 علاج كل القابل للعلاج", use_container_width=True): st.success(f"تم علاج {fix_all_issues(actor)} مشكلة."); st.rerun()
    with st.expander("🔑 إعداد الذكاء الاصطناعي (اختياري)"):
        st.caption("ضع مفتاح Anthropic API ليفهم المساعد أي صياغة صوتية أو مكتوبة. الأفضل وضعه في Secrets باسم ANTHROPIC_API_KEY؛ أو احفظه هنا (لا يدخل في النسخة الاحتياطية). لا تُرسَل للنموذج بيانات الطلبات ولا العملاء — فقط الأمر وأسماء الطيارين والمطاعم والإعدادات.")
        k = st.text_input("المفتاح", type="password", key="ai_key_input")
        c1, c2 = st.columns(2)
        if c1.button("حفظ المفتاح", use_container_width=True) and k.strip(): set_setting("ai_api_key", k.strip()); st.success("تم الحفظ."); st.rerun()
        if c2.button("حذف المفتاح المحفوظ", use_container_width=True): set_setting("ai_api_key", ""); st.rerun()
    with st.expander("📜 سجل الأوامر"):
        h = df("SELECT created_at,command,result FROM ai_commands ORDER BY id DESC LIMIT 30")
        if h.empty: st.caption("لا توجد أوامر بعد.")
        else: st.dataframe(h.rename(columns={"created_at": "الوقت", "command": "الأمر", "result": "النتيجة"}), use_container_width=True, hide_index=True)
# =========================================================
# تشغيل التطبيق
# =========================================================
def render_tracking(token):
    """صفحة تتبع عامة للعميل بدون تسجيل دخول: ?track=<الرمز>"""
    st.markdown(f'<div class="onway-hero"><h1>🧡 تتبع طلبك — ONWAY</h1><p>الصفحة تتحدث تلقائياً.</p></div>', unsafe_allow_html=True)

    @st.fragment(run_every="10s")
    def _live():
        o = one("SELECT o.order_no,o.status,o.eta_minutes,o.created_at,r.name restaurant FROM orders o JOIN restaurants r ON r.id=o.restaurant_id WHERE o.track_token=?", (token,))
        if not o: st.error("رابط التتبع غير صحيح."); return
        stage = {"جديد": 0, "تم التعيين": 0, "تم القبول": 1, "تم الاستلام": 2, "في الطريق": 2, "تم التسليم": 3}.get(o["status"], 0)
        if o["status"] == "ملغى": st.error("تم إلغاء هذا الطلب."); return
        labels = ["✅ تم استلام طلبك", "🛵 الطيار في طريقه للمطعم", "📦 طلبك مع الطيار في الطريق إليك", "🏁 تم التسليم — بالهناء والشفاء"]
        st.markdown(f"**{esc(o['restaurant'])}** — طلب رقم {esc(o['order_no'])}")
        for i, t in enumerate(labels):
            st.markdown(f'<div class="cockpit-alert" style="{"border-color:rgba(255,90,0,.5);background:rgba(255,90,0,.08)" if i == stage else ("opacity:.55" if i > stage else "")}"><b>{t}</b></div>', unsafe_allow_html=True)
        if stage < 3 and o["eta_minutes"]:
            eta = parse_ts(o["created_at"]) + timedelta(minutes=int(o["eta_minutes"]))
            st.caption(f"الوصول المتوقع تقريباً: {eta.strftime('%H:%M')}")
    _live()


PAGES = {"dashboard": render_dashboard, "orders": render_orders, "map": render_live_map, "navigation": render_navigation_center, "riders": render_riders, "rider_wallet": render_rider_wallet,
         "restaurants": render_restaurants, "attendance": render_attendance, "payroll": render_payroll, "settlements": render_settlements, "analysis": render_analysis, "users": render_users, "security": render_account_security, "tools": render_tools, "rider": render_rider, "assistant": render_assistant}


def main():
    setup_db()
    inject_theme()
    tk = st.query_params.get("track")
    if tk:
        render_tracking(tk if isinstance(tk, str) else tk[0]); return
    if "user" not in st.session_state:
        if not st.session_state.get("_clear_cookie"):
            tok = read_device_token(); u = user_from_token(tok)
            if u:
                st.session_state.user = u; st.session_state["_token"] = tok; st.session_state["workspace_role"] = u["role"]
                st.session_state.page = "rider" if u["role"] == "RIDER" else "dashboard"
        if "user" not in st.session_state:
            if st.session_state.get("_clear_cookie"): sync_device_cookie("clear")
            login(); return
    if st.session_state.get("_token") and DEVICE_COMPONENT is not None: sync_device_cookie("set", st.session_state["_token"])
    user = effective_user()
    menu_bar(user)
    live_notifications_fragment(user)
    page = st.session_state.get("page", nav_menu(user)[0][1])
    if page not in [k for _, k in nav_menu(user)]: page = nav_menu(user)[0][1]
    try:
        PAGES.get(page, render_dashboard)(user)
    except Exception as ex:
        st.error("حدث خطأ داخل الواجهة وتم حمايتك من توقف النظام.")
        if actor_is_owner(user): st.exception(ex)
    bottom_nav(user)


if not NO_UI:
    main()
