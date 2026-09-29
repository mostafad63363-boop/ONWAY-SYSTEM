import streamlit as st
import sqlite3
import pandas as pd
import json
import math
import hashlib
import hmac
import secrets
import io
import zipfile
from datetime import datetime, date, timedelta
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

APP_NAME = "ONWAY Operations Cockpit"
DB_PATH = Path("onway_delivery.db")

st.set_page_config(
    page_title=f"{APP_NAME}",
    page_icon="🧡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================================================
# الهوية البصرية — مستوحاة من النمط البرتقالي الذي طلبته
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&display=swap');
:root{
 --bg:#080A0D; --surface:#0F1217; --surface2:#141922; --surface3:#191E27;
 --text:#F6F7F9; --muted:#9AA4B2; --soft:#C8CED6; --line:#242B35;
 --brand:#FF5A00; --brand2:#FF7A33; --brandSoft:rgba(255,90,0,.13);
 --good:#00C27A; --goodSoft:rgba(0,194,122,.13);
 --warn:#FFB020; --warnSoft:rgba(255,176,32,.13);
 --danger:#FF4D4D; --dangerSoft:rgba(255,77,77,.13);
 --info:#4DA3FF; --infoSoft:rgba(77,163,255,.13);
 --shadow:0 12px 34px rgba(0,0,0,.24); --shadowBrand:0 12px 30px rgba(255,90,0,.18);
 --r:18px; --r2:13px;
}
html,body,[class*="css"]{font-family:'Cairo',sans-serif!important;direction:rtl;text-align:right}
body{background:var(--bg)!important;color:var(--text)!important}
*,*:before,*:after{box-sizing:border-box}
[data-testid="stAppViewContainer"]{background:radial-gradient(circle at 15% 0%,rgba(255,90,0,.07),transparent 28%),linear-gradient(180deg,#080A0D 0%,#0A0D11 100%)!important}
[data-testid="stHeader"]{background:rgba(8,10,13,.70)!important;backdrop-filter:blur(12px)}
[data-testid="stDecoration"],#MainMenu,footer{display:none!important}
.block-container{max-width:1500px;padding:.65rem .8rem 5rem;margin:0 auto}
[data-testid="stSidebar"]{display:none!important;visibility:hidden!important;width:0!important;min-width:0!important;max-width:0!important;padding:0!important;margin:0!important}
[data-testid="stSidebarCollapsedControl"]{display:none!important}
[data-testid="stSidebar"] *{color:var(--soft)!important}
[data-testid="stSidebar"] [role="radiogroup"] label{padding:.75rem .82rem!important;border-radius:12px!important;margin:.15rem 0!important;background:transparent!important;border:1px solid transparent!important;font-weight:800!important;font-size:.82rem!important}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:var(--brandSoft)!important;color:#FF9B68!important}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:var(--brandSoft)!important;color:#FF7A33!important;border-right:4px solid var(--brand)!important}
.sidebar-title{font-size:1.15rem;font-weight:900;color:#fff;text-align:center;margin:.45rem 0 .05rem}.sidebar-sub{font-size:.66rem!important;color:var(--muted)!important;text-align:center;margin-bottom:1rem}
.app-topbar{display:flex;align-items:center;justify-content:space-between;gap:12px;background:rgba(15,18,23,.94);border:1px solid var(--line);border-radius:var(--r);padding:10px 12px;margin-bottom:11px;box-shadow:var(--shadow);backdrop-filter:blur(14px)}
.app-brand{display:flex;align-items:center;gap:10px;color:#fff;font-size:.98rem;font-weight:900}.app-brand-mark{width:40px;height:40px;border-radius:13px;display:grid;place-items:center;background:var(--brand);color:#fff;box-shadow:var(--shadowBrand);font-size:1.12rem}
.user-chip{display:flex;align-items:center;gap:8px;background:#12161D;border:1px solid #2A313C;border-radius:999px;padding:6px 10px;color:var(--soft);font-size:.72rem;font-weight:800}.user-dot{width:8px;height:8px;border-radius:50%;background:var(--good);box-shadow:0 0 0 4px rgba(0,194,122,.10)}
.onway-hero{background:linear-gradient(135deg,#11151B 0%,#0E1116 60%,#17110D 100%);border:1px solid var(--line);border-right:4px solid var(--brand);border-radius:var(--r);padding:16px 18px;margin-bottom:12px;box-shadow:var(--shadow)}
.onway-hero h1{margin:0;color:#fff;font-size:1.42rem;font-weight:900;line-height:1.2}.onway-hero p{margin:.4rem 0 0;color:var(--muted);font-size:.76rem;line-height:1.7}
.metric-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:9px;margin-bottom:12px}.metric{position:relative;overflow:hidden;background:linear-gradient(180deg,#11151B,#0E1116);border:1px solid var(--line);border-radius:15px;padding:13px 12px;box-shadow:var(--shadow);min-height:87px}.metric:before{content:"";position:absolute;right:0;top:0;width:4px;height:100%;background:var(--brand)}.metric.good:before{background:var(--good)}.metric.warn:before{background:var(--warn)}.metric.info:before{background:var(--info)}.metric.danger:before{background:var(--danger)}
.metric .v{font-size:1.28rem;font-weight:900;color:#fff;line-height:1.15}.metric .l{font-size:.68rem;font-weight:800;color:#D2D7DE;margin-top:5px}.metric .s{font-size:.58rem;color:var(--muted);margin-top:2px}
.card,.panel{background:linear-gradient(180deg,#10141A,#0D1015);border:1px solid var(--line);border-radius:var(--r);padding:14px;box-shadow:var(--shadow);margin-bottom:11px;color:var(--text)}
.card-title,.section-title{font-size:.92rem;font-weight:900;color:#fff;margin-bottom:4px}.card-sub,.section-sub{font-size:.66rem;color:var(--muted);line-height:1.65}
.section-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin:13px 0 8px}
.status-pill{display:inline-flex;align-items:center;gap:4px;border-radius:999px;padding:.27rem .62rem;font-size:.63rem;font-weight:900}.status-green{background:var(--goodSoft);color:#6DE8BA}.status-blue{background:var(--infoSoft);color:#8FC6FF}.status-amber{background:var(--warnSoft);color:#FFD06B}.status-red{background:var(--dangerSoft);color:#FF9E9E}.status-soft{background:#171C24;color:#C8CED6}
.stButton>button,.stDownloadButton>button,.stLinkButton>a{min-height:46px!important;border-radius:13px!important;border:1px solid #2A313C!important;font-weight:800!important;font-size:.81rem!important;background:#141922!important;color:#F6F7F9!important;box-shadow:none!important;transition:.14s ease!important}
.stButton>button:hover,.stDownloadButton>button:hover,.stLinkButton>a:hover{transform:translateY(-1px);border-color:#4A5564!important;box-shadow:0 8px 22px rgba(0,0,0,.20)!important}
.stButton>button[kind="primary"]{background:linear-gradient(180deg,var(--brand2),var(--brand))!important;color:#fff!important;border-color:var(--brand)!important;box-shadow:var(--shadowBrand)!important}
.stButton>button:disabled{background:#11151B!important;color:#677181!important;border-color:#202631!important}
.stTextInput input,.stNumberInput input,.stTextArea textarea,.stDateInput input{min-height:47px!important;border-radius:12px!important;border:1px solid #2A313C!important;background:#11151B!important;color:#F6F7F9!important;font-size:15px!important}
.stTextInput input::placeholder,.stTextArea textarea::placeholder{color:#6F7A88!important}
[data-baseweb="select"]>div{min-height:47px!important;border-radius:12px!important;border-color:#2A313C!important;background:#11151B!important;color:#F6F7F9!important}[data-baseweb="select"] *{color:#F6F7F9!important}
label{font-size:.71rem!important;font-weight:800!important;color:#CDD3DB!important}
[data-testid="stForm"]{border:1px solid var(--line)!important;border-radius:var(--r)!important;padding:12px!important;background:#0F1217!important;box-shadow:var(--shadow)!important}
[data-testid="stExpander"]{border:1px solid var(--line)!important;border-radius:14px!important;background:#0F1217!important;overflow:hidden}[data-testid="stExpander"] summary{color:#F6F7F9!important;font-weight:800!important}
.stAlert{border-radius:13px!important;background:#12161D!important;color:#E8ECF1!important}.stSuccess{background:var(--goodSoft)!important}.stWarning{background:var(--warnSoft)!important}.stError{background:var(--dangerSoft)!important}.stInfo{background:var(--infoSoft)!important}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:13px;overflow:hidden;background:#11151B}
[data-testid="stDataFrame"] *{color:#F0F2F5!important}
[data-testid="stMetric"]{background:#11151B;border:1px solid var(--line);border-radius:14px;padding:8px}
.highlight{background:linear-gradient(135deg,rgba(255,90,0,.13),rgba(255,90,0,.03));border:1px solid rgba(255,90,0,.28);border-right:4px solid var(--brand);border-radius:14px;padding:12px;color:#fff}
.workspace-switch{background:#0F1217;border:1px solid var(--line);border-radius:15px;padding:8px 10px;box-shadow:var(--shadow);margin-bottom:10px}.workspace-label{font-size:.66rem;font-weight:900;color:#9FA8B5;margin-bottom:6px}
.gps-panel{background:linear-gradient(135deg,rgba(0,194,122,.12),rgba(15,18,23,.95));border:1px solid rgba(0,194,122,.35);border-radius:15px;padding:11px 13px;margin-bottom:10px}.gps-title{font-size:.88rem;font-weight:900;color:#70E7B7}.gps-sub{font-size:.65rem;color:#ADB6C2;line-height:1.75}
.rider-action button{min-height:66px!important;font-size:1rem!important;border-radius:16px!important}
.quick-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin-bottom:11px}.quick-card{background:#11151B;border:1px solid var(--line);border-radius:14px;padding:10px;text-align:center;font-weight:900;color:#fff;box-shadow:var(--shadow)}
.cockpit-alert{padding:10px 12px;border-radius:13px;margin-bottom:7px;border:1px solid var(--line);background:#11151B}.cockpit-alert b{color:#fff}.cockpit-alert span{color:var(--muted);font-size:.66rem}
@media(max-width:1100px){.metric-grid{grid-template-columns:repeat(3,minmax(0,1fr))}.quick-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}.top-nav-panel{background:rgba(15,18,23,.94);border:1px solid var(--line);border-radius:15px;padding:8px 9px;margin-bottom:10px;box-shadow:var(--shadow);backdrop-filter:blur(12px)}.top-nav-label{font-size:.62rem;font-weight:900;color:#8f9aa8;margin:0 0 6px}.top-nav-panel+div [data-testid="stButton"]>button{min-height:44px!important;font-size:.70rem!important;border-radius:12px!important}.top-nav-panel~div [data-testid="stSelectbox"]{margin-top:5px!important}
@media(max-width:700px){.block-container{padding:.35rem .42rem 4.8rem}.app-topbar{padding:8px;border-radius:14px}.app-brand{font-size:.79rem}.app-brand-mark{width:34px;height:34px;border-radius:10px;font-size:1rem}.user-chip{font-size:.58rem;padding:5px 7px;max-width:47%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.onway-hero{padding:13px;border-radius:14px}.onway-hero h1{font-size:1.12rem}.onway-hero p{font-size:.64rem}.metric-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}.metric{min-height:76px;padding:9px}.metric .v{font-size:1.02rem}.metric .l{font-size:.59rem}.metric .s{font-size:.50rem}.quick-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}.stButton>button,.stDownloadButton>button,.stLinkButton>a{min-height:50px!important;font-size:.78rem!important}.stTextInput input,.stNumberInput input,.stTextArea textarea,[data-baseweb="select"]>div{min-height:51px!important;font-size:16px!important}.rider-action button{min-height:70px!important;font-size:1rem!important}.card,.panel{padding:11px;border-radius:15px}.section-title{font-size:.87rem}}
</style>
""", unsafe_allow_html=True)

if not hasattr(st, "fragment"):
    def _fragment_fallback(*args, **kwargs):
        return lambda f: f
    st.fragment = _fragment_fallback

# =========================================================
# قاعدة البيانات — تحافظ على onway_delivery.db وتضيف الجداول الجديدة فقط
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
}

DEFAULTS = {
    "salary_basic": "6000", "working_days": "26", "excused_leave_days": "1", "unexcused_leave_days": "1.25",
    "daily_work_hours": "8", "commission_base_km": "3", "commission_base": "10", "commission_extra_per_km": "5",
    "gps_fresh_seconds": "30", "order_overdue_grace_minutes": "15",
}


def get_conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=5000")
    c.execute("PRAGMA foreign_keys=ON")
    return c


def now_iso(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def today_str(): return date.today().isoformat()
def month_key(d=None):
    d = d or date.today()
    return d.strftime("%Y-%m")
def uid(prefix): return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"


def ensure_column(table, column, col_type):
    with get_conn() as c:
        cols = [r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()]
        if column not in cols:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")


def setup_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as c:
        for table, cols in SCHEMA.items():
            c.execute(f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(cols)})")
        for k, v in DEFAULTS.items():
            c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES (?,?)", (k, v))
        c.execute("DROP INDEX IF EXISTS uq_settlement_order")
    ensure_column("attendance", "break_minutes", "INTEGER NOT NULL DEFAULT 0")
    # ترحيل واحد لسجل الخزينة القديم: إيراد الخدمة عند التسليم = استحقاق، وليس قبضاً نقدياً.
    try:
        if get_setting("legacy_ledger_reclass_done", "0") != "1":
            with get_conn() as c:
                c.execute("UPDATE ledger SET direction='استحقاق' WHERE txn_type='إيراد خدمة توصيل' AND direction='داخل'")
            set_setting("legacy_ledger_reclass_done", "1")
    except Exception:
        pass


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
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt.encode(), 180_000).hex()
    return f"{salt}${digest}"


def verify_pin(pin, stored):
    try:
        salt, digest = stored.split("$", 1)
        calc = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt.encode(), 180_000).hex()
        return hmac.compare_digest(calc, digest)
    except Exception:
        return False


def commission_for_distance(distance):
    d = max(0.0, float(distance or 0))
    base_km = float(get_setting("commission_base_km", 3))
    base = float(get_setting("commission_base", 10))
    extra = float(get_setting("commission_extra_per_km", 5))
    return round(base if d <= base_km else base + (d - base_km) * extra, 2)


def haversine_km(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2): return 9999.0
    r = 6371.0
    p1 = math.radians(float(lat1)); p2 = math.radians(float(lat2))
    dp = math.radians(float(lat2)-float(lat1)); dl = math.radians(float(lon2)-float(lon1))
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.asin(math.sqrt(a))


def gps_fresh(rider):
    raw = rider.get("last_gps_at") if isinstance(rider, dict) else None
    if not raw: return False
    try:
        age = (datetime.now() - datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")).total_seconds()
        return age <= float(get_setting("gps_fresh_seconds", 30))
    except Exception:
        return False


def status_class(status):
    if status == "تم التسليم": return "status-green"
    if status == "ملغى": return "status-red"
    if status in ("تم التعيين", "تم القبول", "تم الاستلام", "في الطريق"): return "status-blue"
    return "status-amber"


def badge(text, kind=None):
    if kind is None:
        kind = status_class(text).replace("status-", "") if text not in ("نشط", "غير نشط") else ("green" if text == "نشط" else "red")
    cls = {"green":"status-green","blue":"status-blue","amber":"status-amber","red":"status-red","soft":"status-soft"}.get(kind, "status-soft")
    return f'<span class="status-pill {cls}">{text}</span>'


def role_label(role):
    return {"OWNER":"المالك","DISPATCHER":"الديسباتشر","ACCOUNTANT":"الحسابات","RIDER":"الطيار","RESTAURANT":"المطعم"}.get(role, role or "مستخدم")


def transitions(status):
    return {
        "جديد": ["تم التعيين", "ملغى"],
        "تم التعيين": ["تم القبول", "ملغى"],
        "تم القبول": ["تم الاستلام", "ملغى"],
        "تم الاستلام": ["في الطريق"],
        "في الطريق": ["تم التسليم"],
        "تم التسليم": [], "ملغى": [],
    }.get(status, [])


def order_active(status):
    return status not in ("تم التسليم", "ملغى")


def available_riders():
    return df("SELECT * FROM riders WHERE status!='غير نشط' ORDER BY active_orders,name")


def all_restaurants(): return df("SELECT * FROM restaurants ORDER BY name")
def active_restaurants(): return df("SELECT * FROM restaurants WHERE active=1 ORDER BY name")
def branches_for(rid, active_only=True):
    q = "SELECT * FROM branches WHERE restaurant_id=?" + (" AND active=1" if active_only else "") + " ORDER BY name"
    return df(q, (rid,))


def ranked_riders(pickup_lat=None, pickup_lng=None):
    r = available_riders()
    if r.empty: return r
    scores=[]
    for _, row in r.iterrows():
        age=9999
        if row.get("last_gps_at"):
            try: age=max(0,(datetime.now()-datetime.strptime(row["last_gps_at"],"%Y-%m-%d %H:%M:%S")).total_seconds())
            except Exception: pass
        dist=haversine_km(row.get("last_lat"),row.get("last_lng"),pickup_lat,pickup_lng)
        scores.append(float(row.get("active_orders") or 0)*12 + min(dist,20)*2 + (10 if age>float(get_setting("gps_fresh_seconds",30)) else age/60))
    r=r.copy(); r["score"]=scores
    return r.sort_values(["score","active_orders","name"]).reset_index(drop=True)


# =========================================================
# CRUD / الحسابات
# =========================================================
def create_restaurant(data, actor):
    if not data.get("name","").strip(): raise ValueError("اسم المطعم مطلوب.")
    rid=uid("RST")
    with get_conn() as c:
        c.execute("INSERT INTO restaurants(id,name,phone,billing_mode,active,created_at) VALUES (?,?,?,?,1,?)", (rid,data["name"].strip(),data.get("phone","").strip(),data.get("billing_mode","كاش"),now_iso()))
    audit(actor["id"],"create","restaurant",rid,after=data|{"id":rid}); return rid


def create_branch(data, actor):
    if not data.get("name","").strip(): raise ValueError("اسم الفرع مطلوب.")
    if data.get("lat") is None or data.get("lng") is None: raise ValueError("اختَر موقع الفرع على الخريطة أولاً.")
    bid=uid("BRN")
    with get_conn() as c:
        c.execute("INSERT INTO branches(id,restaurant_id,name,address,lat,lng,active,created_at) VALUES (?,?,?,?,?,?,1,?)", (bid,data["restaurant_id"],data["name"].strip(),data.get("address","").strip(),float(data["lat"]),float(data["lng"]),now_iso()))
    audit(actor["id"],"create","branch",bid,after=data|{"id":bid}); return bid


def create_rider(data, actor):
    if not data.get("name","").strip(): raise ValueError("اسم الطيار مطلوب.")
    rid=uid("RYD")
    with get_conn() as c:
        c.execute("INSERT INTO riders(id,name,phone,salary,status,created_at) VALUES (?,?,?,?,?,?)", (rid,data["name"].strip(),data.get("phone","").strip(),float(data.get("salary") or get_setting("salary_basic",6000)),"متاح",now_iso()))
    audit(actor["id"],"create","rider",rid,after=data|{"id":rid}); return rid


def create_user(data, actor):
    email=data.get("email","").strip().lower(); pin=data.get("pin","").strip()
    if not data.get("name","").strip() or "@" not in email or not pin.isdigit() or len(pin)<4: raise ValueError("الاسم والبريد وPIN صحيحة مطلوبة.")
    uidv=uid("USR")
    with get_conn() as c:
        c.execute("INSERT INTO users(id,name,email,role,ref_id,pin_hash,active,created_at) VALUES (?,?,?,?,?,?,1,?)", (uidv,data["name"].strip(),email,data["role"],data.get("ref_id"),hash_pin(pin),now_iso()))
    audit(actor["id"],"create","user",uidv,after={k:v for k,v in data.items() if k!="pin"}|{"id":uidv}); return uidv


def update_rider(rider_id, phone, salary, actor):
    old=one("SELECT * FROM riders WHERE id=?",(rider_id,))
    with get_conn() as c: c.execute("UPDATE riders SET phone=?,salary=? WHERE id=?",(phone.strip(),float(salary),rider_id))
    new=one("SELECT * FROM riders WHERE id=?",(rider_id,)); audit(actor["id"],"update","rider",rider_id,before=old,after=new)


def update_restaurant(rid, phone, billing_mode, actor):
    old=one("SELECT * FROM restaurants WHERE id=?",(rid,))
    with get_conn() as c: c.execute("UPDATE restaurants SET phone=?,billing_mode=? WHERE id=?",(phone.strip(),billing_mode,rid))
    new=one("SELECT * FROM restaurants WHERE id=?",(rid,)); audit(actor["id"],"update","restaurant",rid,before=old,after=new)


def set_active(entity, entity_id, active, actor):
    table={"rider":"riders","restaurant":"restaurants","branch":"branches","user":"users"}.get(entity)
    if not table: raise ValueError("نوع السجل غير معروف.")
    old=one(f"SELECT * FROM {table} WHERE id=?",(entity_id,))
    if not old: raise ValueError("السجل غير موجود.")
    if not active:
        if entity=="rider" and int(old.get("active_orders") or 0)>0: raise ValueError("لا يمكن تعطيل طيار لديه طلبات نشطة.")
        if entity=="restaurant" and one("SELECT 1 FROM orders WHERE restaurant_id=? AND status NOT IN ('تم التسليم','ملغى')",(entity_id,)): raise ValueError("لا يمكن تعطيل مطعم لديه طلبات نشطة.")
        if entity=="branch" and one("SELECT 1 FROM orders WHERE branch_id=? AND status NOT IN ('تم التسليم','ملغى')",(entity_id,)): raise ValueError("لا يمكن تعطيل فرع لديه طلبات نشطة.")
    with get_conn() as c:
        if entity=="rider": c.execute("UPDATE riders SET status=? WHERE id=?",("متاح" if active else "غير نشط",entity_id))
        else: c.execute(f"UPDATE {table} SET active=? WHERE id=?",(1 if active else 0,entity_id))
    new=one(f"SELECT * FROM {table} WHERE id=?",(entity_id,)); audit(actor["id"],"activate" if active else "deactivate",entity,entity_id,before=old,after=new)


def reset_user_pin(user_id, actor):
    u=one("SELECT * FROM users WHERE id=?",(user_id,));
    if not u: raise ValueError("المستخدم غير موجود.")
    pin=''.join(secrets.choice('0123456789') for _ in range(6))
    with get_conn() as c: c.execute("UPDATE users SET pin_hash=? WHERE id=?",(hash_pin(pin),user_id))
    audit(actor["id"],"reset_pin","user",user_id,after={"pin_reset":True}); return pin


def create_order(data, actor):
    oid=uid("ORD")
    with get_conn() as c:
        if c.execute("SELECT 1 FROM orders WHERE order_no=?",(data["order_no"],)).fetchone(): raise ValueError("رقم الطلب موجود بالفعل.")
        br=c.execute("SELECT * FROM branches WHERE id=? AND restaurant_id=? AND active=1",(data["branch_id"],data["restaurant_id"])).fetchone()
        if not br: raise ValueError("الفرع غير تابع للمطعم المختار أو غير نشط.")
        rest=c.execute("SELECT billing_mode FROM restaurants WHERE id=? AND active=1",(data["restaurant_id"],)).fetchone()
        if not rest: raise ValueError("المطعم غير نشط.")
        billing=data.get("billing_mode") or rest[0]
        if billing not in ("كاش","آجل"): raise ValueError("طريقة التحصيل غير صحيحة.")
        if data.get("delivery_lat") is None or data.get("delivery_lng") is None:
            raise ValueError("اختَر موقع التسليم على الخريطة قبل إنشاء الطلب.")
        dist=float(data.get("distance_km") or 0)
        comm=commission_for_distance(dist)
        rider_id=data.get("rider_id")
        status="تم التعيين" if rider_id else "جديد"
        cash=float(data.get("delivery_fee") or 0) if billing=="كاش" else 0.0
        if rider_id:
            r=c.execute("SELECT status FROM riders WHERE id=?",(rider_id,)).fetchone()
            if not r or r[0]=="غير نشط": raise ValueError("الطيار غير متاح.")
        c.execute("INSERT INTO orders(id,order_no,restaurant_id,branch_id,delivery_address,delivery_lat,delivery_lng,distance_km,eta_minutes,billing_mode,rider_id,status,delivery_fee,rider_commission,reward,discount,cash_collected,notes,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (oid,data["order_no"].strip(),data["restaurant_id"],data["branch_id"],data["delivery_address"].strip(),data.get("delivery_lat"),data.get("delivery_lng"),dist,int(data.get("eta_minutes") or 0),billing,rider_id,status,float(data["delivery_fee"]),comm,float(data.get("reward") or 0),float(data.get("discount") or 0),cash,data.get("notes","").strip(),actor["id"],now_iso()))
        if rider_id: c.execute("UPDATE riders SET active_orders=active_orders+1,status='في مهمة' WHERE id=?",(rider_id,))
    audit(actor["id"],"create","order",oid,after=data|{"order_id":oid,"rider_commission":comm})
    return oid


def assign_rider(order_id, rider_id, actor):
    with get_conn() as c:
        oldr=c.execute("SELECT * FROM orders WHERE id=?",(order_id,)).fetchone()
        if not oldr: raise ValueError("الطلب غير موجود.")
        old=dict(oldr)
        if old["status"] in ("تم التسليم","ملغى"): raise ValueError("لا يمكن تعيين طلب مغلق.")
        if old["rider_id"]==rider_id: return
        if old["rider_id"]:
            c.execute("UPDATE riders SET active_orders=MAX(0,active_orders-1) WHERE id=?",(old["rider_id"],))
            c.execute("UPDATE riders SET status=CASE WHEN active_orders=0 THEN 'متاح' ELSE status END WHERE id=?",(old["rider_id"],))
        if rider_id:
            r=c.execute("SELECT status FROM riders WHERE id=?",(rider_id,)).fetchone()
            if not r or r[0]=="غير نشط": raise ValueError("الطيار غير متاح.")
            c.execute("UPDATE riders SET active_orders=active_orders+1,status='في مهمة' WHERE id=?",(rider_id,))
            c.execute("UPDATE orders SET rider_id=?,status=CASE WHEN status='جديد' THEN 'تم التعيين' ELSE status END WHERE id=?",(rider_id,order_id))
        else: c.execute("UPDATE orders SET rider_id=NULL,status='جديد' WHERE id=?",(order_id,))
        new=dict(c.execute("SELECT * FROM orders WHERE id=?",(order_id,)).fetchone())
    audit(actor["id"],"assign_rider","order",order_id,before=old,after=new)


def change_order_status(order_id,new_status,actor):
    with get_conn() as c:
        r=c.execute("SELECT * FROM orders WHERE id=?",(order_id,)).fetchone()
        if not r: raise ValueError("الطلب غير موجود.")
        old=dict(r)
        # المطعم يمكنه الإلغاء قبل الاستلام فقط.
        if actor["role"]=="RESTAURANT":
            if old["restaurant_id"]!=actor.get("ref_id"): raise ValueError("لا تملك هذا الطلب.")
            if new_status!="ملغى" or old["status"] not in ("جديد","تم التعيين","تم القبول"): raise ValueError("المطعم يستطيع إلغاء الطلب قبل الاستلام فقط.")
        if actor["role"]=="RIDER" and old["rider_id"]!=actor.get("ref_id"): raise ValueError("الطلب غير مخصص لك.")
        if actor["role"]=="RIDER" and new_status not in transitions(old["status"]): raise ValueError(f"لا يمكن الانتقال من {old['status']} إلى {new_status}.")
        if new_status not in transitions(old["status"]): raise ValueError(f"الانتقال من {old['status']} إلى {new_status} غير مسموح.")
        stamp=now_iso(); cols=["status=?"]; vals=[new_status]
        if new_status=="تم القبول": cols.append("accepted_at=?"); vals.append(stamp)
        if new_status=="تم الاستلام": cols.append("picked_up_at=?"); vals.append(stamp)
        if new_status=="تم التسليم": cols.append("delivered_at=?"); vals.append(stamp)
        if new_status=="ملغى": cols.append("cancelled_at=?"); vals.append(stamp)
        vals.append(order_id); c.execute(f"UPDATE orders SET {', '.join(cols)} WHERE id=?",vals)
        if new_status in ("تم التسليم","ملغى") and old["rider_id"]:
            c.execute("UPDATE riders SET active_orders=MAX(0,active_orders-1) WHERE id=?",(old["rider_id"],))
            c.execute("UPDATE riders SET status=CASE WHEN active_orders=0 THEN 'متاح' ELSE status END WHERE id=?",(old["rider_id"],))
        # الإيراد هنا استحقاق محاسبي، وليس قبضاً نقدياً؛ الخزينة تتحدث عند التصفية/السداد.
        if new_status=="تم التسليم":
            c.execute("INSERT INTO ledger(txn_no,txn_type,account_type,account_id,amount,direction,reference_id,description,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                      (uid("TXN"),"إيراد خدمة توصيل","إيراد_مستحق",old["restaurant_id"],float(old["delivery_fee"]),"استحقاق",order_id,"إثبات استحقاق خدمة التوصيل",actor["id"],stamp))
        new=dict(c.execute("SELECT * FROM orders WHERE id=?",(order_id,)).fetchone())
    audit(actor["id"],"status_change","order",order_id,before=old,after=new)


def update_order(order_id, data, actor):
    old=order_with_names(data.get("order_no_old")) if data.get("order_no_old") else one("SELECT * FROM orders WHERE id=?",(order_id,))
    if not old: raise ValueError("الطلب غير موجود.")
    if old["status"] in ("تم التسليم","ملغى"): raise ValueError("لا يمكن تعديل طلب مغلق.")
    if actor["role"]=="RIDER": raise ValueError("لا يسمح للطيار بتعديل بيانات الطلب التشغيلية.")
    fields=["delivery_address=?","delivery_lat=?","delivery_lng=?","distance_km=?","eta_minutes=?","notes=?"]
    vals=[data["delivery_address"],data.get("delivery_lat"),data.get("delivery_lng"),float(data["distance_km"]),int(data["eta_minutes"]),data.get("notes","")]
    if actor["role"] in ("OWNER","DISPATCHER"):
        fields += ["delivery_fee=?","billing_mode=?"]
        vals += [float(data["delivery_fee"]),data["billing_mode"]]
        vals += [order_id]
    else: vals += [order_id]
    with get_conn() as c: c.execute(f"UPDATE orders SET {', '.join(fields)} WHERE id=?",vals)
    # العمولة تتغير تبعاً للمسافة دائماً.
    comm=commission_for_distance(data["distance_km"])
    with get_conn() as c: c.execute("UPDATE orders SET rider_commission=? WHERE id=?",(comm,order_id))
    new=one("SELECT * FROM orders WHERE id=?",(order_id,)); audit(actor["id"],"update","order",order_id,before=old,after=new)


def order_with_names(order_no):
    return one("SELECT o.*,r.name restaurant,b.name branch,COALESCE(ry.name,'—') rider FROM orders o JOIN restaurants r ON r.id=o.restaurant_id JOIN branches b ON b.id=o.branch_id LEFT JOIN riders ry ON ry.id=o.rider_id WHERE o.order_no=?",(order_no,))


# =========================================================
# الحضور / ساعات العمل / المرتبات
# =========================================================
def attendance_hours(row):
    if not row or not row.get("clock_in") or not row.get("clock_out"): return 0.0
    try:
        start=datetime.strptime(row["clock_in"],"%Y-%m-%d %H:%M:%S"); end=datetime.strptime(row["clock_out"],"%Y-%m-%d %H:%M:%S")
        if end < start: end += timedelta(days=1)
        mins=max(0,(end-start).total_seconds()/60 - float(row.get("break_minutes") or 0))
        return round(mins/60,2)
    except Exception: return 0.0


def attendance_for_month(rider_id, period):
    start=f"{period}-01"
    d=datetime.strptime(start,"%Y-%m-%d").date()
    next_month=(d.replace(day=28)+timedelta(days=4)).replace(day=1)
    return df("SELECT * FROM attendance WHERE rider_id=? AND work_date>=? AND work_date<? ORDER BY work_date",(rider_id,start,next_month.isoformat()))


def upsert_attendance(data, actor):
    rid=data["rider_id"]; wd=data["work_date"]
    old=one("SELECT * FROM attendance WHERE rider_id=? AND work_date=?",(rid,wd))
    with get_conn() as c:
        if old:
            c.execute("UPDATE attendance SET clock_in=?,clock_out=?,break_minutes=?,status=?,reason=? WHERE id=?",(data.get("clock_in") or None,data.get("clock_out") or None,int(data.get("break_minutes") or 0),data["status"],data.get("reason","") ,old["id"]))
            aid=old["id"]
        else:
            aid=uid("ATT")
            c.execute("INSERT INTO attendance(id,rider_id,work_date,clock_in,clock_out,break_minutes,status,reason,created_at) VALUES (?,?,?,?,?,?,?,?,?)",(aid,rid,wd,data.get("clock_in") or None,data.get("clock_out") or None,int(data.get("break_minutes") or 0),data["status"],data.get("reason","") ,now_iso()))
    new=one("SELECT * FROM attendance WHERE id=?",(aid,)); audit(actor["id"],"upsert","attendance",aid,before=old,after=new)


def payroll_summary(rider_id, period):
    rider=one("SELECT * FROM riders WHERE id=?",(rider_id,))
    if not rider: raise ValueError("الطيار غير موجود.")
    d=datetime.strptime(period,"%Y-%m").date(); nxt=(d.replace(day=28)+timedelta(days=4)).replace(day=1)
    start=d.isoformat(); end=nxt.isoformat();
    att=attendance_for_month(rider_id,period)
    hours=round(sum(attendance_hours(x) for x in att.to_dict("records")),2) if not att.empty else 0.0
    present=int((att["status"]=="حاضر").sum()) if not att.empty else 0
    excused=int((att["status"]=="إجازة بعذر").sum()) if not att.empty else 0
    unexcused=int((att["status"]=="إجازة بدون عذر").sum()) if not att.empty else 0
    daily=float(rider["salary"])/float(get_setting("working_days",26))
    leave_ded=(excused*float(get_setting("excused_leave_days",1))+unexcused*float(get_setting("unexcused_leave_days",1.25)))*daily
    orders=df("SELECT * FROM orders WHERE rider_id=? AND status='تم التسليم' AND delivered_at>=? AND delivered_at<?",(rider_id,start+" 00:00:00",end+" 00:00:00"))
    commissions=float(orders["rider_commission"].sum()) if not orders.empty else 0.0
    rewards=float(orders["reward"].sum()) if not orders.empty else 0.0
    discounts=float(orders["discount"].sum()) if not orders.empty else 0.0
    adj=df("SELECT type,COALESCE(SUM(amount),0) amount FROM payroll_adjustments WHERE rider_id=? AND period=? GROUP BY type",(rider_id,period))
    add=float(adj.loc[adj["type"]=="إضافة","amount"].iloc[0]) if not adj.empty and (adj["type"]=="إضافة").any() else 0.0
    deduct=float(adj.loc[adj["type"].isin(["خصم","سلفة"]),"amount"].sum()) if not adj.empty else 0.0
    paid=float(df("SELECT COALESCE(SUM(amount),0) x FROM payroll_payments WHERE rider_id=? AND period=?",(rider_id,period))["x"][0])
    net=max(0.0,float(rider["salary"])-leave_ded+commissions+rewards-discounts+add-deduct)
    return {"rider":rider,"period":period,"present":present,"excused":excused,"unexcused":unexcused,"hours":hours,"expected_hours":float(get_setting("working_days",26))*float(get_setting("daily_work_hours",8)),"basic":float(rider["salary"]),"daily_rate":daily,"leave_deduction":leave_ded,"commissions":commissions,"rewards":rewards,"discounts":discounts,"adjust_add":add,"adjust_deduct":deduct,"net":net,"paid":paid,"remaining":max(0,net-paid)}


def add_payroll_adjustment(data, actor):
    amount=float(data["amount"])
    if amount<=0: raise ValueError("المبلغ يجب أن يكون أكبر من صفر.")
    aid=uid("PADJ")
    with get_conn() as c: c.execute("INSERT INTO payroll_adjustments(id,rider_id,period,type,amount,description,created_by,created_at) VALUES (?,?,?,?,?,?,?,?)",(aid,data["rider_id"],data["period"],data["type"],amount,data.get("description","") ,actor["id"],now_iso()))
    audit(actor["id"],"create","payroll_adjustment",aid,after=data|{"id":aid})


def record_payroll_payment(data, actor):
    p=payroll_summary(data["rider_id"],data["period"]); amount=float(data["amount"])
    if amount<=0 or amount>p["remaining"]+0.01: raise ValueError(f"المبلغ يتجاوز المستحق المتبقي ({p['remaining']:.2f} ج).")
    pid=uid("PAY")
    stamp=now_iso()
    with get_conn() as c:
        c.execute("INSERT INTO payroll_payments(id,rider_id,period,amount,method,reference,notes,paid_at,created_by) VALUES (?,?,?,?,?,?,?,?,?)",(pid,data["rider_id"],data["period"],amount,data["method"],data.get("reference","") ,data.get("notes","") ,stamp,actor["id"]))
        c.execute("INSERT INTO ledger(txn_no,txn_type,account_type,account_id,amount,direction,reference_id,description,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",(uid("TXN"),"صرف راتب شهرى","طيار",data["rider_id"],amount,"خارج",pid,f"راتب {data['period']}",actor["id"],stamp))
    audit(actor["id"],"pay","payroll_payment",pid,after=data|{"id":pid,"amount":amount}); return pid


# =========================================================
# التصفية والخزينة
# =========================================================
def rider_unsettled_orders(rider_id, start, end):
    return df("""SELECT o.*,r.name restaurant,b.name branch,
                       o.cash_collected-COALESCE((SELECT SUM(si.amount) FROM settlement_items si WHERE si.order_id=o.id),0) remaining_cash
                FROM orders o JOIN restaurants r ON r.id=o.restaurant_id JOIN branches b ON b.id=o.branch_id
                WHERE o.rider_id=? AND o.status='تم التسليم' AND o.billing_mode='كاش'
                  AND o.delivered_at>=? AND o.delivered_at<?
                  AND o.cash_collected-COALESCE((SELECT SUM(si.amount) FROM settlement_items si WHERE si.order_id=o.id),0)>0.01""",(rider_id,start+" 00:00:00",end+" 00:00:00"))


def create_rider_settlement(rider_id, start, end, actor):
    os=rider_unsettled_orders(rider_id,start,end)
    if os.empty: raise ValueError("لا توجد طلبات كاش غير مصفاة في الفترة.")
    gross=float(os["remaining_cash"].sum()); commissions=float(os["rider_commission"].sum()); rewards=float(os["reward"].sum()); discounts=float(os["discount"].sum())
    due=round(gross-commissions-rewards+discounts,2)
    sid=uid("RSTL")
    with get_conn() as c:
        c.execute("INSERT INTO settlements(id,kind,party_id,period_start,period_end,gross,commissions,rewards,discounts,cash_due,paid,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",(sid,"طيار_كاش",rider_id,start,end,gross,commissions,rewards,discounts,due,max(0,due),actor["id"],now_iso()))
        for oid,amt in os[["id","remaining_cash"]].itertuples(index=False): c.execute("INSERT INTO settlement_items(id,settlement_id,order_id,amount) VALUES (?,?,?,?)",(uid("SETI"),sid,oid,float(amt)))
        if due!=0:
            direction="داخل" if due>0 else "خارج"
            c.execute("INSERT INTO ledger(txn_no,txn_type,account_type,account_id,amount,direction,reference_id,description,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",(uid("TXN"),"تصفية طيار كاش","طيار",rider_id,abs(due),direction,sid,f"تصفية الفترة {start} إلى {end}",actor["id"],now_iso()))
    audit(actor["id"],"settle","rider_cash_settlement",sid,after={"gross":gross,"commissions":commissions,"rewards":rewards,"discounts":discounts,"cash_due":due,"orders":int(len(os))})
    return sid, due, len(os)


def restaurant_unsettled_orders(rid,start,end):
    return df("""SELECT o.*,b.name branch,
                       o.delivery_fee-COALESCE((SELECT SUM(si.amount) FROM settlement_items si WHERE si.order_id=o.id),0) remaining_due
                FROM orders o JOIN branches b ON b.id=o.branch_id
                WHERE o.restaurant_id=? AND o.status='تم التسليم' AND o.billing_mode='آجل'
                  AND o.delivered_at>=? AND o.delivered_at<?
                  AND o.delivery_fee-COALESCE((SELECT SUM(si.amount) FROM settlement_items si WHERE si.order_id=o.id),0)>0.01""",(rid,start+" 00:00:00",end+" 00:00:00"))


def create_restaurant_settlement(rid,start,end,paid,actor):
    os=restaurant_unsettled_orders(rid,start,end)
    if os.empty: raise ValueError("لا توجد مديونية آجل غير مسددة في الفترة.")
    due=float(os["remaining_due"].sum()); paid=float(paid)
    if paid<=0 or paid>due+0.01: raise ValueError(f"الدفعة يجب أن تكون بين 0 و{due:.2f} ج.")
    sid=uid("RSET")
    with get_conn() as c:
        c.execute("INSERT INTO settlements(id,kind,party_id,period_start,period_end,gross,paid,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?)",(sid,"مطعم",rid,start,end,due,paid,actor["id"],now_iso()))
        # لتبسيط التخصيص والشفافية، نوزع الدفعة على الطلبات الأقدم أولاً.
        rem=paid
        for row in os.sort_values("delivered_at").to_dict("records"):
            alloc=min(rem,float(row["remaining_due"]))
            if alloc<=0: break
            c.execute("INSERT INTO settlement_items(id,settlement_id,order_id,amount) VALUES (?,?,?,?)",(uid("SETI"),sid,row["id"],alloc)); rem-=alloc
        c.execute("INSERT INTO ledger(txn_no,txn_type,account_type,account_id,amount,direction,reference_id,description,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",(uid("TXN"),"تحصيل مطعم آجل","مطعم",rid,paid,"داخل",sid,"تحصيل مديونية مطعم آجل",actor["id"],now_iso()))
    audit(actor["id"],"settle","restaurant_settlement",sid,after={"due":due,"paid":paid,"orders":int(len(os))})
    return sid,due,paid


def treasury_balance():
    return float(df("SELECT COALESCE(SUM(CASE WHEN direction='داخل' THEN amount WHEN direction='خارج' THEN -amount ELSE 0 END),0) x FROM ledger")["x"][0])


def cash_receipts_today():
    return float(df("SELECT COALESCE(SUM(amount),0) x FROM ledger WHERE direction='داخل' AND substr(created_at,1,10)=?",(today_str(),))["x"][0])


# =========================================================
# =========================================================
# خريطة ONWAY التشغيلية — مبنية على خريطة Netlify الأصلية مع دمجها داخل التطبيق
# =========================================================
MAP_COMPONENT=None
try:
    from streamlit.components.v2 import component as _component

    MAP_HTML="""
    <div id='owroot' dir='rtl'>
      <div class='ow-search'>
        <input id='owsearch' autocomplete='off' placeholder='ابحث عن شارع، مطعم، منطقة أو وجهة…' />
        <button id='owmic' title='بحث صوتي'>🎤</button>
        <button id='owsearchbtn'>بحث</button>
      </div>
      <div id='owhint'>انقر على الخريطة لتحديد الوجهة أو اضغط «GPS» لمعرفة موقع الجهاز.</div>
      <div id='owmap'></div>
      <div id='owstatus'></div>
      <button id='owgps'>📍 GPS</button>
      <div id='owcontrols'>
        <button id='owshare' title='مشاركة الوجهة'>🔗</button>
        <button id='owfit' title='ملاءمة العناصر'>⌖</button>
        <button id='owfull' title='شاشة كاملة'>⛶</button>
      </div>
      <div id='owbadge'></div>
    </div>
    """
    MAP_CSS="""
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@500;600;700;800;900&display=swap');
    *{box-sizing:border-box}#owroot{height:100%;min-height:470px;position:relative;overflow:hidden;border-radius:18px;background:#101318;font-family:Cairo,Arial,sans-serif}
    #owmap{position:absolute;inset:0}.leaflet-container{font-family:Cairo,Arial,sans-serif;background:#dfe5ea}.leaflet-popup-content{direction:rtl;line-height:1.7;font-size:12px}.leaflet-control{font-family:Cairo,Arial,sans-serif}
    .ow-search{position:absolute;top:12px;left:50%;transform:translateX(-50%);z-index:1200;display:flex;gap:6px;width:min(94%,560px);padding:7px;background:rgba(18,18,18,.94);border:1px solid #3a414d;border-radius:999px;box-shadow:0 8px 28px rgba(0,0,0,.28);backdrop-filter:blur(10px)}
    .ow-search input{flex:1;min-width:0;border:0;outline:0;background:transparent;color:#fff;font:700 13px Cairo,Arial;padding:7px 10px}.ow-search input::placeholder{color:#8b96a5}.ow-search button,.ow-search+button{border:0;color:#fff;background:#252b34;border-radius:999px;padding:8px 11px;font:800 12px Cairo;cursor:pointer}.ow-search #owsearchbtn{background:#FF5A00}.ow-search #owmic{background:#00B368}
    #owhint{position:absolute;top:72px;right:50%;transform:translateX(50%);z-index:1150;background:rgba(16,19,24,.82);border:1px solid rgba(255,255,255,.08);color:#ffd18b;padding:5px 10px;border-radius:999px;font:700 10px Cairo;pointer-events:none;white-space:nowrap;max-width:92%;overflow:hidden;text-overflow:ellipsis}
    #owstatus{display:none;position:absolute;top:108px;right:50%;transform:translateX(50%);z-index:1250;background:rgba(16,19,24,.96);color:#fff;padding:7px 12px;border-radius:999px;font:800 11px Cairo;box-shadow:0 6px 18px rgba(0,0,0,.25)}
    #owgps{display:none;position:absolute;top:12px;right:12px;z-index:1250;border:1px solid #2d3744;background:#007AFF;color:#fff;border-radius:999px;padding:9px 13px;font:900 11px Cairo;box-shadow:0 6px 16px rgba(0,0,0,.24);cursor:pointer}#owgps.on{background:#00B368}#owgps.warn{background:#FFB020;color:#161616}
    #owcontrols{position:absolute;bottom:16px;left:16px;z-index:1200;display:flex;gap:7px}#owcontrols button{width:42px;height:42px;border:1px solid #3a414d;background:rgba(18,18,18,.92);color:#fff;border-radius:13px;font-size:17px;cursor:pointer;box-shadow:0 5px 16px rgba(0,0,0,.24)}
    #owbadge{display:none;position:absolute;bottom:16px;right:16px;z-index:1200;background:rgba(18,18,18,.92);color:#dbe1e8;border:1px solid #3a414d;padding:8px 10px;border-radius:999px;font:800 10px Cairo;box-shadow:0 5px 16px rgba(0,0,0,.24)}
    .owpin{display:flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:50%;border:2px solid #fff;box-shadow:0 4px 14px rgba(0,0,0,.25);font-size:17px}.owpin.rider{box-shadow:0 0 0 5px rgba(0,194,122,.12),0 4px 14px rgba(0,0,0,.25)}
    @media(max-width:650px){#owroot{min-height:58vh}.ow-search{width:95%;top:9px}.ow-search input{font-size:14px}.ow-search button{padding:8px 10px}.owhint{display:none}#owhint{top:66px;font-size:9px}.leaflet-control-zoom{margin-bottom:72px!important}.leaflet-bottom.leaflet-left{bottom:7px}}
    """
    MAP_JS="""
    export default function(component){
      const {data,setTriggerValue,parentElement}=component;
      const root=parentElement; if(!root) return;
      const mapEl=root.querySelector('#owmap'), searchEl=root.querySelector('#owsearch'), searchBtn=root.querySelector('#owsearchbtn'), micBtn=root.querySelector('#owmic'), gpsBtn=root.querySelector('#owgps'), statusEl=root.querySelector('#owstatus'), badge=root.querySelector('#owbadge'), hint=root.querySelector('#owhint');
      let cfg={}; try{cfg=JSON.parse(atob(data));}catch(e){return;}
      const esc=v=>String(v??'').replace(/[<>&"']/g,ch=>({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;',"'":'&#39;'}[ch]));
      const showStatus=t=>{statusEl.textContent=t;statusEl.style.display='block';clearTimeout(root.__owST);root.__owST=setTimeout(()=>statusEl.style.display='none',2600)};
      const setBadge=(t,kind='normal')=>{badge.style.display='block';badge.textContent=t;badge.style.borderColor=kind==='ok'?'#2a614e':kind==='warn'?'#6b541e':'#3a414d';badge.style.color=kind==='ok'?'#8df0c8':kind==='warn'?'#ffd36e':'#dbe1e8'};
      const loadCss=()=>{if(document.getElementById('ow-leaflet-css'))return;const l=document.createElement('link');l.id='ow-leaflet-css';l.rel='stylesheet';l.href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';document.head.appendChild(l)};
      const loadJs=src=>new Promise((resolve,reject)=>{if(window.L){resolve();return;}const s=document.createElement('script');s.src=src;s.onload=resolve;s.onerror=reject;document.head.appendChild(s)});
      const routeKey=cfg.route?.from&&cfg.route?.to?JSON.stringify([cfg.route.from,cfg.route.to]):'';
      const distanceM=(a,b)=>{const R=6371000,p1=a[0]*Math.PI/180,p2=b[0]*Math.PI/180,dp=(b[0]-a[0])*Math.PI/180,dl=(b[1]-a[1])*Math.PI/180;const x=Math.sin(dp/2)**2+Math.cos(p1)*Math.cos(p2)*Math.sin(dl/2)**2;return 2*R*Math.asin(Math.sqrt(x));};
      (async()=>{
        loadCss();
        try{await loadJs('https://unpkg.com/leaflet@1.9.4/dist/leaflet.js')}catch(e){showStatus('تعذر تحميل مكتبة الخريطة');return;}
        let map=mapEl.__owMap;
        if(!map){
          const center=cfg.center||[31.2001,29.9187];
          map=L.map(mapEl,{zoomControl:false,preferCanvas:true}).setView(center,cfg.zoom||12); mapEl.__owMap=map; mapEl.__owLayer=L.layerGroup().addTo(map); mapEl.__owRoute=L.layerGroup().addTo(map); mapEl.__owMe=L.layerGroup().addTo(map); mapEl.__owWatch=null; mapEl.__owGps=false; mapEl.__owClickable=false; mapEl.__owInitialFit=false; mapEl.__owRouteFitted=false; mapEl.__owLastGps=null;
          L.control.zoom({position:'bottomleft'}).addTo(map);
          L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,detectRetina:true,attribution:'© OpenStreetMap contributors • ONWAY'}).addTo(map);
        } else {const centerKey=JSON.stringify(cfg.center||[31.2001,29.9187]);if(centerKey!==mapEl.__owCenter){map.setView(cfg.center||[31.2001,29.9187],cfg.zoom||12);mapEl.__owCenter=centerKey;}}
        mapEl.__owLayer.clearLayers();
        const bounds=[];
        (cfg.points||[]).forEach(p=>{if(p.lat==null||p.lng==null)return;const color=p.kind==='rider'?(p.online?'#00B368':'#7F8A97'):p.kind==='self'?'#007AFF':p.kind==='branch'?'#FF5A00':'#FF4D4D';const cl=p.kind==='rider'?'owpin rider':'owpin';const icon=L.divIcon({className:'',html:`<div class='${cl}' style='background:${color}'>${esc(p.icon||'📍')}</div>`,iconSize:[34,34],iconAnchor:[17,17]});const m=L.marker([p.lat,p.lng],{icon}).addTo(mapEl.__owLayer);let html=`<b>${esc(p.title||'')}</b>`;if(p.meta)html+=`<br>${esc(p.meta)}`;if(p.kind==='rider'&&p.accuracy!=null)html+=`<br>دقة GPS: ${esc(Number(p.accuracy).toFixed(1))} م`;m.bindPopup(`<div style='direction:rtl;font-family:Cairo,Arial;min-width:160px'>${html}</div>`);m.on('click',()=>setTriggerValue('marker_click',JSON.stringify({id:p.id,kind:p.kind})));bounds.push([p.lat,p.lng])});
        const drawRoute=(coords,meta)=>{mapEl.__owRoute.clearLayers();L.polyline(coords,{color:'#FF5A00',weight:6,opacity:.88,lineCap:'round',lineJoin:'round'}).addTo(mapEl.__owRoute);setTriggerValue('route_meta',JSON.stringify(meta||{}));if(!mapEl.__owRouteFitted||mapEl.__owRouteKey!==routeKey){map.fitBounds(coords,{padding:[40,40],maxZoom:16});mapEl.__owRouteFitted=true;}};
        window.__owRC=window.__owRC||{};window.__owRM=window.__owRM||{};
        if(routeKey){
          const from=cfg.route.from,to=cfg.route.to;
          if(window.__owRC[routeKey]) drawRoute(window.__owRC[routeKey],window.__owRM[routeKey]); else {const url=`https://router.project-osrm.org/route/v1/driving/${from[1]},${from[0]};${to[1]},${to[0]}?overview=full&geometries=geojson`;fetch(url).then(r=>r.json()).then(d=>{if(d.routes&&d.routes[0]){const rt=d.routes[0],coords=rt.geometry.coordinates.map(c=>[c[1],c[0]]),meta={distance_m:rt.distance,duration_s:rt.duration};window.__owRC[routeKey]=coords;window.__owRM[routeKey]=meta;drawRoute(coords,meta)}}).catch(()=>showStatus('تعذر حساب خط السير الآن'));}
          mapEl.__owRouteKey=routeKey;
        }else{mapEl.__owRoute.clearLayers();mapEl.__owRouteKey='';mapEl.__owRouteFitted=false;if(bounds.length&&!mapEl.__owInitialFit){map.fitBounds(bounds,{padding:[35,35],maxZoom:15});mapEl.__owInitialFit=true}}
        if(cfg.clickable&&!mapEl.__owClickable){
          mapEl.__owClickable=true;
          map.on('click',e=>{const lat=Number(e.latlng.lat.toFixed(6)),lng=Number(e.latlng.lng.toFixed(6));showStatus('جاري تحديد العنوان…');fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}&zoom=18&accept-language=ar`).then(r=>r.json()).then(d=>{const address=d.display_name||'موقع محدد';setTriggerValue('map_click',JSON.stringify({lat,lng,address}));showStatus('تم تحديد الوجهة');}).catch(()=>{setTriggerValue('map_click',JSON.stringify({lat,lng,address:''}));showStatus('تم تحديد النقطة')})});
        }
        const geolocate=()=>{
          if(!navigator.geolocation){setBadge('🟠 GPS غير متاح','warn');return;}
          gpsBtn.classList.remove('warn');gpsBtn.textContent='⏳ جاري GPS…';setBadge('⏳ طلب إذن الموقع…');
          const push=pos=>{const c=pos.coords,now=Date.now(),lat=Number(c.latitude.toFixed(6)),lng=Number(c.longitude.toFixed(6));const p={lat,lng,accuracy:c.accuracy==null?null:Number(c.accuracy.toFixed(1)),heading:c.heading==null?null:Number(c.heading.toFixed(1)),speed:c.speed==null?null:Number((c.speed||0).toFixed(1)),ts:now};const last=mapEl.__owLastGps; if(last&&now-last.ts<4500&&distanceM([last.lat,last.lng],[lat,lng])<12)return;mapEl.__owLastGps=p;setTriggerValue('gps',JSON.stringify(p));gpsBtn.classList.add('on');gpsBtn.textContent='🟢 GPS';setBadge(`🟢 دقة ${p.accuracy==null?'—':p.accuracy+' م'}`,'ok');mapEl.__owMe.clearLayers();const ic=L.divIcon({className:'',html:`<div class='owpin' style='background:#007AFF'>🚴</div>`,iconSize:[34,34],iconAnchor:[17,17]});L.marker([lat,lng],{icon:ic}).addTo(mapEl.__owMe).bindPopup('📍 موقعي الآن');};
          const fail=e=>{let t='تعذر تحديد الموقع';if(e?.code===1)t='تم رفض إذن الموقع';if(e?.code===2)t='الموقع غير متاح';if(e?.code===3)t='انتهت مهلة GPS';gpsBtn.classList.remove('on');gpsBtn.classList.add('warn');gpsBtn.textContent='📍 السماح بالموقع';setBadge('🟠 '+t,'warn');setTriggerValue('gps_status',JSON.stringify({code:e?.code||0,message:t}))};
          navigator.geolocation.getCurrentPosition(push,fail,{enableHighAccuracy:true,maximumAge:3000,timeout:12000});
          if(!mapEl.__owWatch){mapEl.__owWatch=navigator.geolocation.watchPosition(push,fail,{enableHighAccuracy:true,maximumAge:3000,timeout:15000})}
        };
        if(cfg.geolocation){gpsBtn.style.display='block';gpsBtn.onclick=geolocate;if(cfg.auto_request_gps&&!mapEl.__owAutoRequested){mapEl.__owAutoRequested=true;setTimeout(geolocate,500)}}
        const doSearch=()=>{const q=(searchEl.value||'').trim();if(!q)return;showStatus('جاري البحث…');const url=`https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&accept-language=ar&q=${encodeURIComponent(q+', Alexandria, Egypt')}`;fetch(url).then(r=>r.json()).then(d=>{if(!d||!d.length){showStatus('لم يتم العثور على المكان');return}const lat=Number(d[0].lat),lng=Number(d[0].lon),address=d[0].display_name||q;setTriggerValue('search_result',JSON.stringify({lat,lng,address,q}));showStatus('تم العثور على المكان ✅');}).catch(()=>showStatus('خطأ في الاتصال'))};
        searchBtn.onclick=doSearch;searchEl.onkeydown=e=>{if(e.key==='Enter')doSearch()};
        if(micBtn){micBtn.onclick=()=>{const SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR){showStatus('البحث الصوتي غير مدعوم في المتصفح');return}const r=new SR();r.lang='ar-EG';r.interimResults=false;r.maxAlternatives=1;r.onstart=()=>showStatus('تحدث الآن…');r.onresult=e=>{searchEl.value=e.results[0][0].transcript;doSearch()};r.onerror=()=>showStatus('تعذر قراءة الصوت');r.start();}}
        const findAndShowTarget=p=>{if(p?.lat==null)return;const lat=Number(p.lat),lng=Number(p.lng);map.setView([lat,lng],17);L.marker([lat,lng]).addTo(mapEl.__owLayer).bindPopup(`<div style='direction:rtl;font-family:Cairo'><b>📍 ${esc(p.title||'الوجهة')}</b><br>${esc(p.address||'')}</div>`).openPopup();if(p.from){const from=p.from,to=[lat,lng],rk=JSON.stringify([from,to]);const url=`https://router.project-osrm.org/route/v1/driving/${from[1]},${from[0]};${to[1]},${to[0]}?overview=full&geometries=geojson`;fetch(url).then(r=>r.json()).then(d=>{if(d.routes&&d.routes[0]){const rt=d.routes[0],coords=rt.geometry.coordinates.map(c=>[c[1],c[0]]);L.polyline(coords,{color:'#FF5A00',weight:6,opacity:.9}).addTo(mapEl.__owRoute);setTriggerValue('route_meta',JSON.stringify({distance_m:rt.distance,duration_s:rt.duration,key:rk}))}})}};
        if(cfg.search_result)findAndShowTarget(cfg.search_result);
        if(cfg.selected&&cfg.selected.lat!=null){
          const selectedKey=JSON.stringify([cfg.selected.lat,cfg.selected.lng,cfg.selected.title||'']);
          if(mapEl.__owSelectedKey!==selectedKey){ mapEl.__owSelectedKey=selectedKey; map.setView([cfg.selected.lat,cfg.selected.lng],Math.max(16,cfg.zoom||12)); }
        }
        root.querySelector('#owshare').onclick=()=>{const s=cfg.selected||cfg.route?.to;if(!s){showStatus('حدد وجهة أولاً');return}const lat=s.lat??s[0],lng=s.lng??s[1],url=`https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;if(navigator.share)navigator.share({title:'ONWAY',text:'وجهة ONWAY',url}).catch(()=>{});else navigator.clipboard?.writeText(url).then(()=>showStatus('تم نسخ رابط الملاحة'))};
        root.querySelector('#owfit').onclick=()=>{if(bounds.length)map.fitBounds(bounds,{padding:[35,35],maxZoom:15});else map.setView(cfg.center||[31.2001,29.9187],cfg.zoom||12)};
        root.querySelector('#owfull').onclick=()=>{if(!document.fullscreenElement)root.requestFullscreen?.().catch(()=>{});else document.exitFullscreen?.()};
      })();
      return ()=>{};
    }
    """
    MAP_COMPONENT=_component("onway_operational_map_v8",html=MAP_HTML,css=MAP_CSS,js=MAP_JS,isolate_styles=True)
except Exception:
    MAP_COMPONENT=None


def mount_map(points=None,center=None,zoom=12,clickable=False,geolocation=False,route=None,key="map",selected=None,search_result=None):
    cfg={"points":points or [],"center":center or [31.2001,29.9187],"zoom":zoom,"clickable":clickable,"geolocation":geolocation,"auto_request_gps":bool(geolocation and key.startswith("live_map_RIDER")),"route":route,"selected":selected,"search_result":search_result}
    if MAP_COMPONENT:
        import base64
        payload=base64.b64encode(json.dumps(cfg,ensure_ascii=False).encode()).decode()
        return MAP_COMPONENT(key=key,data=payload)
    pts=[{"lat":p["lat"],"lon":p["lng"]} for p in (points or []) if p.get("lat") is not None and p.get("lng") is not None]
    if pts: st.map(pd.DataFrame(pts),latitude="lat",longitude="lon",zoom=zoom,height=470)
    else: st.info("الخريطة تحتاج إصدار Streamlit حديثاً أو لا توجد مواقع صالحة.")
    return None


def geocode_address(query):
    query=query.strip()
    if not query: return None
    try:
        url="https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&accept-language=ar&q="+quote(query+", Alexandria, Egypt")
        req=Request(url,headers={"User-Agent":"ONWAY-Delivery/8.1 (operations app)"})
        with urlopen(req,timeout=8) as r: data=json.loads(r.read().decode("utf-8"))
        if data:
            return {"lat":round(float(data[0]["lat"]),6),"lng":round(float(data[0]["lon"]),6),"address":data[0].get("display_name",query)}
    except Exception:
        return None
    return None


# =========================================================
# وضع العمل — المالك يستطيع التبديل بين الاختصاصات بدون تسجيل خروج
# =========================================================
def effective_user():
    base=st.session_state.get("user",{})
    if not base: return base
    if base.get("role")!="OWNER": return base
    mode=st.session_state.get("workspace_role","OWNER")
    out=dict(base); out["role"]=mode
    if mode=="RIDER":
        riders=df("SELECT id,name FROM riders WHERE status!='غير نشط' ORDER BY name")
        selected=st.session_state.get("workspace_rider_id")
        ids=riders["id"].tolist() if not riders.empty else []
        if selected not in ids: selected=ids[0] if ids else None
        st.session_state["workspace_rider_id"]=selected
        out["ref_id"]=selected
    elif mode=="RESTAURANT":
        rests=active_restaurants()
        selected=st.session_state.get("workspace_restaurant_id")
        ids=rests["id"].tolist() if not rests.empty else []
        if selected not in ids: selected=ids[0] if ids else None
        st.session_state["workspace_restaurant_id"]=selected
        out["ref_id"]=selected
    else:
        out["ref_id"]=base.get("ref_id")
    return out

def _on_workspace_rider_change():
    selected=st.session_state.get("workspace_rider_select")
    if selected is None: return
    st.session_state["workspace_rider_id"]=selected

def render_workspace_switcher(base_user):
    if base_user.get("role")!="OWNER": return effective_user()
    current=st.session_state.get("workspace_role","OWNER")
    st.markdown('<div class="workspace-switch"><div class="workspace-label">🔄 مساحة العمل — التبديل بدون تسجيل خروج</div></div>',unsafe_allow_html=True)
    roles=[("OWNER","👑 المالك"),("DISPATCHER","🎯 الديسباتشر"),("RIDER","🚴 الطيار"),("ACCOUNTANT","💰 الحسابات")]
    cols=st.columns(4,gap="small")
    for i,(code,label) in enumerate(roles):
        if cols[i].button(label,type="primary" if current==code else "secondary",use_container_width=True,key=f"workspace_{code}"):
            st.session_state["workspace_role"]=code
            st.session_state.page="rider" if code=="RIDER" else "dashboard"
            st.rerun()
    if current=="RIDER":
        riders=df("SELECT id,name FROM riders WHERE status!='غير نشط' ORDER BY name")
        if riders.empty:
            st.warning("لا يوجد طيارون نشطون لاختيار وضع الطيار.")
        else:
            ids=riders["id"].tolist(); names=riders["name"].tolist(); cur=st.session_state.get("workspace_rider_id",ids[0]); idx=ids.index(cur) if cur in ids else 0
            st.selectbox("الطيار الذي ستفتح واجهته",names,index=idx,key="workspace_rider_select",on_change=_on_workspace_rider_change)
    return effective_user()

# =========================================================
# واجهة الدخول
# =========================================================
def header(title,subtitle=""):
    user=effective_user() or {}
    st.markdown(f'<div class="app-topbar"><div class="app-brand"><div class="app-brand-mark">🧡</div><div>{APP_NAME}</div></div><div class="user-chip"><span class="user-dot"></span>{user.get("name","زائر")} • {role_label(user.get("role"))}</div></div>',unsafe_allow_html=True)
    if st.session_state.get("user",{}).get("role")=="OWNER":
        render_workspace_switcher(st.session_state.user)
    st.markdown(f'<div class="onway-hero"><h1>{title}</h1><p>{subtitle}</p></div>',unsafe_allow_html=True)


def metric_grid(items):
    html=[]
    for label,value,sub,kind in items:
        html.append(f'<div class="metric {kind or ""}"><div class="v">{value}</div><div class="l">{label}</div><div class="s">{sub}</div></div>')
    st.markdown('<div class="metric-grid">'+''.join(html)+'</div>',unsafe_allow_html=True)


def create_owner():
    st.markdown(f'<div class="onway-hero"><h1>🧡 {APP_NAME}</h1><p>تهيئة المالك الأول — مرة واحدة فقط.</p></div>',unsafe_allow_html=True)
    with st.form("first_owner"):
        a,b=st.columns(2); name=a.text_input("اسم المالك"); email=b.text_input("البريد الإلكتروني").strip().lower(); c,d=st.columns(2); p1=c.text_input("PIN الدخول",type="password",max_chars=8); p2=d.text_input("تأكيد PIN",type="password",max_chars=8)
        if st.form_submit_button("بدء النظام",type="primary",use_container_width=True):
            if not name or "@" not in email: st.error("اكتب الاسم والبريد بشكل صحيح.")
            elif not p1.isdigit() or len(p1)<4 or p1!=p2: st.error("PIN يجب أن يكون أرقاماً من 4 إلى 8 أرقام ومتطابقاً.")
            else:
                uidv=uid("USR")
                with get_conn() as c: c.execute("INSERT INTO users(id,name,email,role,ref_id,pin_hash,active,created_at) VALUES (?,?,?,?,?,?,1,?)",(uidv,name.strip(),email,"OWNER",None,hash_pin(p1),now_iso()))
                audit(uidv,"create","user",uidv,after={"name":name,"email":email,"role":"OWNER"}); st.session_state.user={"id":uidv,"name":name,"email":email,"role":"OWNER","ref_id":None}; st.rerun()


def login():
    if df("SELECT id FROM users WHERE active=1").empty:
        create_owner(); return
    header("تسجيل الدخول","وصول آمن لكل مستخدم حسب اختصاصه وصلاحياته.")
    with st.form("login"):
        e=st.text_input("البريد الإلكتروني").strip().lower(); p=st.text_input("PIN",type="password",max_chars=8)
        if st.form_submit_button("دخول آمن",type="primary",use_container_width=True):
            u=one("SELECT * FROM users WHERE lower(email)=? AND active=1",(e,))
            if u and verify_pin(p,u["pin_hash"]):
                st.session_state.user={"id":u["id"],"name":u["name"],"email":u["email"],"role":u["role"],"ref_id":u["ref_id"]}; st.session_state["workspace_role"]="OWNER" if u["role"]=="OWNER" else u["role"]; audit(u["id"],"login","user",u["id"]); st.rerun()
            else: st.error("بيانات الدخول غير صحيحة.")


# =========================================================
# Dashboard / الخرائط
# =========================================================
def dashboard_data():
    t=today_str(); o=df("SELECT * FROM orders WHERE substr(created_at,1,10)=?",(t,))
    total=len(o); cash=int((o["billing_mode"]=="كاش").sum()) if not o.empty else 0; credit=int((o["billing_mode"]=="آجل").sum()) if not o.empty else 0; done=int((o["status"]=="تم التسليم").sum()) if not o.empty else 0
    service=float(o.loc[o["status"]=="تم التسليم","delivery_fee"].sum()) if not o.empty else 0
    commissions=float(o.loc[o["status"]=="تم التسليم","rider_commission"].sum()) if not o.empty else 0
    active=int(o["status"].isin(["جديد","تم التعيين","تم القبول","تم الاستلام","في الطريق"]).sum()) if not o.empty else 0
    overdue=0
    if not o.empty:
        for row in o[o["status"].isin(["تم التعيين","تم القبول","تم الاستلام","في الطريق"])].to_dict("records"):
            if row.get("eta_minutes") and row.get("created_at"):
                try:
                    if datetime.now() > datetime.strptime(row["created_at"],"%Y-%m-%d %H:%M:%S")+timedelta(minutes=int(row["eta_minutes"])+int(get_setting("order_overdue_grace_minutes",15))): overdue+=1
                except Exception: pass
    credit_due=float(df("SELECT COALESCE(SUM(o.delivery_fee-COALESCE((SELECT SUM(si.amount) FROM settlement_items si WHERE si.order_id=o.id),0)),0) x FROM orders o WHERE o.billing_mode='آجل' AND o.status='تم التسليم'")["x"][0])
    return {"total":total,"cash":cash,"credit":credit,"done":done,"service":service,"commissions":commissions,"active":active,"overdue":overdue,"credit_due":credit_due,"treasury":treasury_balance()}


def map_points_for(user):
    points=[]
    if user["role"] in ("OWNER","DISPATCHER","ACCOUNTANT"):
        riders=df("SELECT id,name,status,active_orders,last_lat,last_lng,gps_accuracy,last_gps_at FROM riders WHERE status!='غير نشط' AND last_lat IS NOT NULL AND last_lng IS NOT NULL")
        for _,r in riders.iterrows(): points.append({"id":r["id"],"kind":"rider","icon":"🚴","lat":r["last_lat"],"lng":r["last_lng"],"online":gps_fresh(r.to_dict()),"accuracy":r["gps_accuracy"],"title":r["name"],"meta":f"{r['status']} • {int(r['active_orders'])} طلبات • {r['last_gps_at'] or 'لا يوجد'}"})
        orders=df("SELECT id,order_no,status,delivery_address,delivery_lat,delivery_lng,rider_id FROM orders WHERE status NOT IN ('تم التسليم','ملغى') AND delivery_lat IS NOT NULL AND delivery_lng IS NOT NULL")
        for _,o in orders.iterrows(): points.append({"id":o["id"],"kind":"order","icon":"📦","lat":o["delivery_lat"],"lng":o["delivery_lng"],"online":True,"title":o["order_no"],"meta":f"{o['status']} • {o['delivery_address']}"})
    elif user["role"]=="RIDER":
        r=one("SELECT * FROM riders WHERE id=?",(user["ref_id"],))
        if r and r["last_lat"] is not None: points.append({"id":"self","kind":"self","icon":"🚴","lat":r["last_lat"],"lng":r["last_lng"],"online":gps_fresh(r),"title":"موقعي","meta":f"دقة {r['gps_accuracy'] or '—'} م"})
        orders=df("SELECT id,order_no,status,delivery_address,delivery_lat,delivery_lng FROM orders WHERE rider_id=? AND status NOT IN ('تم التسليم','ملغى') AND delivery_lat IS NOT NULL AND delivery_lng IS NOT NULL",(user["ref_id"],))
        for _,o in orders.iterrows(): points.append({"id":o["id"],"kind":"order","icon":"📦","lat":o["delivery_lat"],"lng":o["delivery_lng"],"online":True,"title":o["order_no"],"meta":f"{o['status']} • {o['delivery_address']}"})
    elif user["role"]=="RESTAURANT":
        bs=branches_for(user["ref_id"],False)
        for _,b in bs.iterrows():
            if b["lat"] is not None: points.append({"id":b["id"],"kind":"branch","icon":"🏪","lat":b["lat"],"lng":b["lng"],"online":True,"title":b["name"],"meta":b["address"] or "فرع المطعم"})
        orders=df("SELECT id,order_no,status,delivery_address,delivery_lat,delivery_lng FROM orders WHERE restaurant_id=? AND status NOT IN ('تم التسليم','ملغى') AND delivery_lat IS NOT NULL AND delivery_lng IS NOT NULL",(user["ref_id"],))
        for _,o in orders.iterrows(): points.append({"id":o["id"],"kind":"order","icon":"📦","lat":o["delivery_lat"],"lng":o["delivery_lng"],"online":True,"title":o["order_no"],"meta":f"{o['status']} • {o['delivery_address']}"})
    return points


@st.fragment(run_every="5s")
def live_map_fragment(user, navigation=False, route=None):
    points=map_points_for(user)
    current_sel=st.session_state.get("map_selection") if navigation else None
    search_result=st.session_state.pop("map_search_request",None) if navigation else None
    result=mount_map(points,center=[31.2001,29.9187],zoom=12,clickable=navigation,geolocation=(navigation or user["role"]=="RIDER"),route=route,key="live_map_navigation" if navigation else f"live_map_{user['role']}",selected=current_sel,search_result=search_result)
    if result:
        mc=getattr(result,"map_click",None); gps=getattr(result,"gps",None); rm=getattr(result,"route_meta",None); sr=getattr(result,"search_result",None); mk=getattr(result,"marker_click",None)
        if mc:
            try:
                st.session_state.map_selection=json.loads(mc)
                st.session_state.map_search_request=st.session_state.map_selection
                st.rerun()
            except Exception: pass
        if sr:
            try:
                st.session_state.map_selection=json.loads(sr)
                st.session_state.map_search_request=st.session_state.map_selection
                st.rerun()
            except Exception: pass
        if mk:
            try:
                st.session_state.map_marker=json.loads(mk)
            except Exception: pass
        if gps:
            try:
                payload=json.loads(gps)
                if user["role"]=="RIDER":
                    ts=payload.get("ts")
                    if ts!=st.session_state.get("last_gps_ts"):
                        st.session_state.last_gps_ts=ts
                        rid=user["ref_id"]; lat=float(payload["lat"]); lng=float(payload["lng"])
                        with get_conn() as c:
                            c.execute("UPDATE riders SET last_lat=?,last_lng=?,gps_accuracy=?,heading=?,speed=?,last_gps_at=? WHERE id=?",(lat,lng,payload.get("accuracy"),payload.get("heading"),payload.get("speed"),now_iso(),rid))
                            c.execute("INSERT INTO gps_log(rider_id,lat,lng,accuracy,heading,speed,recorded_at) VALUES (?,?,?,?,?,?,?)",(rid,lat,lng,payload.get("accuracy"),payload.get("heading"),payload.get("speed"),now_iso()))
                elif navigation:
                    st.session_state.navigation_origin=payload
            except Exception: pass
        if rm:
            try: st.session_state.route_meta=json.loads(rm)
            except Exception: pass
        gps_status=getattr(result,"gps_status",None)
        if gps_status:
            try:
                st.session_state.gps_status=json.loads(gps_status)
                if st.session_state.gps_status.get("code")==1 and user.get("role")=="RIDER":
                    st.warning("📍 إذن الموقع مرفوض. اسمح للموقع من إعدادات المتصفح ثم اضغط «السماح بالموقع». بدون الإذن لن تستطيع الإدارة رؤية موقعك.")
            except Exception: pass


def render_live_map(user):
    header("الخريطة الحية","الخريطة جزء من التشغيل وليست شاشة منفصلة: الأسطول والطلبات والحركة أمامك.")
    if user["role"] in ("OWNER","DISPATCHER"):
        a,b=st.columns([2,1]);
        with a: st.markdown('<div class="card-title">حركة الأسطول والطلبات</div><div class="card-sub">🟢 GPS حديث • 🟠 GPS قديم • 📦 طلب نشط</div>',unsafe_allow_html=True)
        with b:
            stale=df("SELECT COUNT(*) x FROM riders WHERE status!='غير نشط' AND last_lat IS NOT NULL AND last_gps_at IS NOT NULL")["x"][0]
            st.caption(f"الطيارون المتتبعون: {int(stale)}")
    live_map_fragment(user)


def render_navigation_center(user):
    header("مركز الملاحة","للمالك: اختر أي وجهة من الطلبات أو الفروع أو الطيارين أو انقر على الخريطة مباشرة.")
    if "map_selection" not in st.session_state: st.session_state.map_selection={}
    st.markdown('<div class="highlight"><b>🎯 هدف الشاشة:</b> تحويل أي نقطة تشغيلية إلى وجهة ملاحة فوراً، مع الاحتفاظ بالمسار في نفس الجلسة.</div>',unsafe_allow_html=True)
    c1,c2,c3=st.columns(3)
    with c1:
        types=["من الخريطة","طلب","فرع","طيار"]
        target_type=st.selectbox("مصدر الوجهة",types,key="nav_type")
    target=None
    if target_type=="طلب":
        o=df("SELECT id,order_no,delivery_address,delivery_lat,delivery_lng FROM orders WHERE delivery_lat IS NOT NULL AND delivery_lng IS NOT NULL ORDER BY created_at DESC LIMIT 300")
        if not o.empty:
            sel=st.selectbox("الطلب",o["order_no"].tolist()); target=o[o["order_no"]==sel].iloc[0].to_dict()
            target={"lat":target["delivery_lat"],"lng":target["delivery_lng"],"address":target["delivery_address"],"title":sel}
    elif target_type=="فرع":
        b=df("SELECT b.*,r.name restaurant FROM branches b JOIN restaurants r ON r.id=b.restaurant_id WHERE b.lat IS NOT NULL AND b.lng IS NOT NULL ORDER BY r.name,b.name")
        if not b.empty:
            names=[f"{x['restaurant']} — {x['name']}" for _,x in b.iterrows()]; sel=st.selectbox("الفرع",names); x=b.iloc[names.index(sel)].to_dict(); target={"lat":x["lat"],"lng":x["lng"],"address":x["address"],"title":sel}
    elif target_type=="طيار":
        r=df("SELECT id,name,last_lat,last_lng,status FROM riders WHERE last_lat IS NOT NULL AND last_lng IS NOT NULL ORDER BY name")
        if not r.empty:
            names=r["name"].tolist(); sel=st.selectbox("الطيار",names); x=r[r["name"]==sel].iloc[0].to_dict(); target={"lat":x["last_lat"],"lng":x["last_lng"],"address":f"موقع الطيار — {x['status']}","title":x["name"]}
    else:
        q=st.text_input("بحث عن أي وجهة",placeholder="اكتب شارعاً أو منطقة أو مكاناً")
        if st.button("تحديد من البحث",use_container_width=True):
            g=geocode_address(q)
            if g: st.session_state.map_selection=g; st.success("تم تحديد الوجهة.")
            else: st.error("لم يتم العثور على الوجهة.")
    if target: st.session_state.map_selection=target; st.session_state.map_search_request=target
    live_map_fragment(user,navigation=True)
    sel=st.session_state.get("map_selection") or {}
    if sel.get("lat") is not None:
        st.success(f"الوجهة الحالية: {sel.get('title') or 'نقطة محددة'} — {sel.get('address','')}")
        origin=st.session_state.get("navigation_origin")
        if origin and origin.get("lat") is not None:
            route=f"https://www.google.com/maps/dir/?api=1&origin={origin['lat']},{origin['lng']}&destination={sel['lat']},{sel['lng']}"
            st.link_button("🧭 ابدأ الملاحة من موقعي",route,use_container_width=True)
        else:
            route=f"https://www.google.com/maps/dir/?api=1&destination={sel['lat']},{sel['lng']}"
            st.link_button("🧭 ابدأ الملاحة إلى الوجهة",route,use_container_width=True)
        if st.button("مسح الوجهة",use_container_width=True): st.session_state.map_selection={}; st.rerun()


# =========================================================
# Dashboard حسب الدور
# =========================================================
def render_dashboard(user):
    if user["role"]=="RIDER": return render_rider(user)
    if user["role"]=="RESTAURANT":
        rs=df("SELECT * FROM orders WHERE restaurant_id=? ORDER BY created_at DESC LIMIT 100",(user["ref_id"],))
        header("لوحة المطعم","حالة الطلبات والحساب في مساحة بسيطة.")
        active=int(rs["status"].isin(["جديد","تم التعيين","تم القبول","تم الاستلام","في الطريق"]).sum()) if not rs.empty else 0
        done=int((rs["status"]=="تم التسليم").sum()) if not rs.empty else 0
        due=float(df("SELECT COALESCE(SUM(o.delivery_fee-COALESCE((SELECT SUM(si.amount) FROM settlement_items si WHERE si.order_id=o.id),0)),0) x FROM orders o WHERE o.restaurant_id=? AND o.billing_mode='آجل' AND o.status='تم التسليم'",(user["ref_id"],))["x"][0])
        metric_grid([("إجمالي الطلبات",len(rs),"آخر السجلات","info"),("قيد التنفيذ",active,"نشطة","info"),("تم التسليم",done,"مكتملة","good"),("آجل مستحق",f"{due:,.2f} ج","جاهز للتسوية","warn")])
        st.markdown('<div class="section-title">🗺️ حركة طلبات المطعم</div>',unsafe_allow_html=True); live_map_fragment(user)
        if not rs.empty: st.dataframe(rs[["order_no","status","billing_mode","delivery_address","delivery_fee","created_at"]].rename(columns={"order_no":"الطلب","status":"الحالة","billing_mode":"التحصيل","delivery_address":"العنوان","delivery_fee":"خدمة التوصيل","created_at":"الوقت"}),use_container_width=True,hide_index=True)
        return

    d=dashboard_data(); header("غرفة العمليات","هذه الشاشة تقول لك أين تحتاج أن تتدخل الآن — لا تحتاج البحث عن المعلومة.")
    period=month_key(); payroll=0.0; riders=df("SELECT id FROM riders")
    if not riders.empty:
        for _,x in riders.iterrows(): payroll += payroll_summary(x["id"],period)["remaining"]
    metric_grid([("طلبات اليوم",d["total"],f"كاش {d['cash']} • آجل {d['credit']}","info"),("قيد التنفيذ",d["active"],"في الميدان","info"),("تحتاج تدخل",d["overdue"],"متأخرة","danger" if d["overdue"] else "good"),("تم التسليم",d["done"],"اليوم","good"),("آجل مستحق",f"{d['credit_due']:,.0f} ج","يحتاج تحصيل","warn"),("الخزينة",f"{d['treasury']:,.0f} ج",f"دخل اليوم {cash_receipts_today():,.0f} ج","good")])

    # إجراءات سريعة للمالك والديسباتشر
    if user["role"] in ("OWNER","DISPATCHER"):
        q1,q2,q3,q4=st.columns(4,gap="small")
        if q1.button("＋ طلب جديد",type="primary",use_container_width=True): st.session_state.page="orders"; st.rerun()
        if q2.button("🚴 تعيين / تغيير طيار",use_container_width=True): st.session_state.page="orders"; st.rerun()
        if q3.button("🗺️ افتح الخريطة",use_container_width=True): st.session_state.page="map"; st.rerun()
        if q4.button("🧭 الملاحة",use_container_width=True) and user["role"]=="OWNER": st.session_state.page="navigation"; st.rerun()

    if d["overdue"]:
        st.markdown(f'<div class="cockpit-alert" style="border-color:rgba(255,77,77,.35);background:rgba(255,77,77,.07)"><b>🔴 {d["overdue"]} طلب يحتاج تدخلك الآن</b><br><span>ابدأ من الطلبات أو الخريطة لتحديد الطيار ومعالجة التأخير.</span></div>',unsafe_allow_html=True)

    left,right=st.columns([1.55,1],gap="small")
    with left:
        st.markdown('<div class="section-title">🗺️ الخريطة الحية</div><div class="section-sub">موقع الطيارين والطلبات النشطة • التحديث كل 5 ثوانٍ</div>',unsafe_allow_html=True)
        if user["role"] in ("OWNER","DISPATCHER","ACCOUNTANT"): live_map_fragment(user)
    with right:
        st.markdown('<div class="section-title">⚡ حالة الأسطول</div><div class="section-sub">ما يهمك الآن فقط</div>',unsafe_allow_html=True)
        rs=df("SELECT name,status,active_orders,last_gps_at FROM riders WHERE status!='غير نشط' ORDER BY active_orders DESC,name")
        if rs.empty: st.info("لا يوجد طيارون نشطون.")
        else:
            for _,r in rs.head(10).iterrows():
                fresh=gps_fresh(r.to_dict()); color="status-green" if fresh and r["status"]!="مشغول" else ("status-amber" if r["status"]!="غير نشط" else "status-red")
                gps="🟢 GPS" if fresh else "🟠 GPS"; st.markdown(f'<div class="cockpit-alert"><b>🚴 {r["name"]}</b> &nbsp; {badge(r["status"],"green" if r["status"]!="غير نشط" else "red")}<br><span>{gps} • {int(r["active_orders"])} طلبات • {r["last_gps_at"] or "لم يسجل موقعاً"}</span></div>',unsafe_allow_html=True)

    st.markdown('<div class="section-title">📦 الطلبات النشطة</div><div class="section-sub">الطلبات التي تحتاج متابعة أو إجراء</div>',unsafe_allow_html=True)
    o=df("SELECT o.order_no,r.name restaurant,b.name branch,o.status,o.billing_mode,COALESCE(ry.name,'—') rider,o.delivery_address,o.distance_km,o.rider_commission,o.created_at FROM orders o JOIN restaurants r ON r.id=o.restaurant_id JOIN branches b ON b.id=o.branch_id LEFT JOIN riders ry ON ry.id=o.rider_id WHERE o.status NOT IN ('تم التسليم','ملغى') ORDER BY o.created_at DESC LIMIT 60")
    if not o.empty:
        st.dataframe(o.rename(columns={"order_no":"الطلب","restaurant":"المطعم","branch":"الفرع","status":"الحالة","billing_mode":"التحصيل","rider":"الطيار","delivery_address":"العنوان","distance_km":"كم","rider_commission":"العمولة","created_at":"الوقت"}),use_container_width=True,hide_index=True)
    else: st.success("✅ لا توجد طلبات مفتوحة الآن.")


# =========================================================
# الطلبات
# =========================================================
def render_orders(user):
    header("الطلبات","إنشاء، تعيين، متابعة، تعديل، وإغلاق الطلب بدون لمس الحسابات يدوياً.")
    can_create=user["role"] in ("OWNER","DISPATCHER")
    if can_create:
        with st.expander("＋ إنشاء طلب",expanded=False):
            if user["role"]=="RESTAURANT":
                rid=user["ref_id"]; rest_name=one("SELECT name,billing_mode FROM restaurants WHERE id=?",(rid,)); st.info(f"المطعم: {rest_name['name']} • التحصيل: {rest_name['billing_mode']}")
            else:
                rs=active_restaurants();
                if rs.empty: st.warning("أضف مطعماً نشطاً أولاً."); return
                rn=st.selectbox("المطعم",rs["name"].tolist(),key="ord_rest"); rid=rs[rs["name"]==rn].iloc[0]["id"]
            bs=branches_for(rid)
            if bs.empty: st.warning("أضف فرعاً نشطاً أولاً."); return
            bn=st.selectbox("الفرع",bs["name"].tolist(),key="ord_branch"); br=bs[bs["name"]==bn].iloc[0].to_dict()
            if "order_point" not in st.session_state: st.session_state.order_point={}
            point=st.session_state.order_point
            center=[br.get("lat") or 31.2001,br.get("lng") or 29.9187]
            route={"from":[center[0],center[1]],"to":[point["lat"],point["lng"]]} if point.get("lat") is not None else None
            res=mount_map(points=[{"id":br["id"],"kind":"branch","icon":"🏪","lat":br.get("lat"),"lng":br.get("lng"),"online":True,"title":bn,"meta":br.get("address","")}],center=center,zoom=14,clickable=True,route=route,key="new_order_map")
            click=getattr(res,"map_click",None) if res else None; rm=getattr(res,"route_meta",None) if res else None
            if click:
                try: st.session_state.order_point=json.loads(click); st.rerun()
                except Exception: pass
            if rm:
                try: st.session_state.order_distance=round(json.loads(rm)["distance_m"]/1000,2)
                except Exception: pass
            point=st.session_state.order_point
            a,b=st.columns(2); order_no=a.text_input("رقم الطلب"); address=b.text_input("عنوان التسليم",value=point.get("address", ""))
            c,d,e=st.columns(3); distance=c.number_input("المسافة (كم)",min_value=0.0,value=float(st.session_state.get("order_distance",3.0)),step=.1); eta=d.number_input("الوقت المتوقع (دقيقة)",min_value=0,value=25,step=1)
            if user["role"]=="RESTAURANT": billing=rest_name["billing_mode"]
            else: billing=e.selectbox("التحصيل",["كاش","آجل"])
            f,g,h=st.columns(3); fee=f.number_input("خدمة التوصيل",min_value=0.0,value=30.0,step=1.0); reward=g.number_input("مكافأة",min_value=0.0,value=0.0,step=1.0); discount=h.number_input("خصم",min_value=0.0,value=0.0,step=1.0)
            comm=commission_for_distance(distance); st.markdown(f"**العمولة المحسوبة تلقائياً:** `{comm:.2f} ج`",unsafe_allow_html=False)
            notes=st.text_area("ملاحظات")
            rider_id=None
            if user["role"] in ("OWNER","DISPATCHER"):
                rr=ranked_riders(br.get("lat"),br.get("lng")); names=["تعيين لاحقاً"]+rr["name"].tolist() if not rr.empty else ["تعيين لاحقاً"]; sel=st.selectbox("الطيار — اقتراح ذكي",names); 
                if sel!="تعيين لاحقاً": rider_id=rr[rr["name"]==sel].iloc[0]["id"]
            if st.button("🚀 إنشاء الطلب",type="primary",use_container_width=True):
                try:
                    create_order({"order_no":order_no,"restaurant_id":rid,"branch_id":br["id"],"delivery_address":address,"delivery_lat":point.get("lat"),"delivery_lng":point.get("lng"),"distance_km":distance,"eta_minutes":eta,"billing_mode":billing,"rider_id":rider_id,"delivery_fee":fee,"reward":reward,"discount":discount,"notes":notes},user)
                    st.session_state.order_point={}; st.session_state.pop("order_distance",None); st.success("تم إنشاء الطلب بنجاح."); st.rerun()
                except Exception as ex: st.error(str(ex))
    q="SELECT o.*,r.name restaurant,b.name branch,COALESCE(ry.name,'—') rider FROM orders o JOIN restaurants r ON r.id=o.restaurant_id JOIN branches b ON b.id=o.branch_id LEFT JOIN riders ry ON ry.id=o.rider_id WHERE 1=1"; params=[]
    if user["role"]=="RESTAURANT": q+=" AND o.restaurant_id=?"; params.append(user["ref_id"])
    if user["role"]=="RIDER": q+=" AND o.rider_id=?"; params.append(user["ref_id"])
    if user["role"]=="ACCOUNTANT": pass
    s=st.text_input("🔎 بحث سريع",placeholder="رقم الطلب أو العنوان أو اسم المطعم"); status=st.selectbox("الحالة",["الكل","جديد","تم التعيين","تم القبول","تم الاستلام","في الطريق","تم التسليم","ملغى"])
    if s: q+=" AND (o.order_no LIKE ? OR o.delivery_address LIKE ? OR r.name LIKE ?)"; params += [f"%{s}%",f"%{s}%",f"%{s}%"]
    if status!="الكل": q+=" AND o.status=?"; params.append(status)
    q+=" ORDER BY o.created_at DESC LIMIT 400"; orders=df(q,tuple(params))
    if orders.empty: st.info("لا توجد طلبات مطابقة."); return
    st.dataframe(orders[["order_no","restaurant","branch","status","billing_mode","rider","delivery_address","distance_km","delivery_fee","rider_commission","created_at"]].rename(columns={"order_no":"الطلب","restaurant":"المطعم","branch":"الفرع","status":"الحالة","billing_mode":"التحصيل","rider":"الطيار","delivery_address":"العنوان","distance_km":"كم","delivery_fee":"الخدمة","rider_commission":"العمولة","created_at":"الوقت"}),use_container_width=True,hide_index=True)
    selectable=orders["order_no"].tolist(); selected=st.selectbox("فتح الطلب",selectable,key="open_order")
    o=order_with_names(selected)
    if not o: return
    metric_grid([("الحالة",o["status"],o["rider"],"info"),("خدمة التوصيل",f"{o['delivery_fee']:,.2f} ج","القيمة التشغيلية","good"),("العمولة",f"{o['rider_commission']:,.2f} ج",f"{o['distance_km']} كم","warn"),("التحصيل",o["billing_mode"],"طريقة الحساب","info")])
    if user["role"] in ("OWNER","DISPATCHER"):
        rr=available_riders(); names=["بدون طيار"]+(rr["name"].tolist() if not rr.empty else []); current=o["rider"] if o["rider"] in names else "بدون طيار"; sel=st.selectbox("تعيين الطيار",names,index=names.index(current),key="assign_order")
        if st.button("حفظ التعيين",use_container_width=True):
            try:
                assign_rider(o["id"], None if sel=="بدون طيار" else rr[rr["name"]==sel].iloc[0]["id"], user)
                st.success("تم تحديث التعيين.")
                st.rerun()
            except Exception as ex:
                st.error(str(ex))
    allowed=transitions(o["status"])
    if allowed and user["role"] in ("OWNER","DISPATCHER","RIDER"):
        actions=allowed
        action=st.selectbox("الإجراء التالي",actions,key=f"next_{o['id']}")
        if st.button("تنفيذ الإجراء",type="primary",use_container_width=True):
            try: change_order_status(o["id"],action,user); st.success("تم تحديث حالة الطلب."); st.rerun()
            except Exception as ex: st.error(str(ex))
    if user["role"] in ("OWNER","DISPATCHER") and order_active(o["status"]):
        with st.expander("✏️ تعديل بيانات الطلب"):
            if "edit_point" not in st.session_state: st.session_state.edit_point={"lat":o["delivery_lat"],"lng":o["delivery_lng"],"address":o["delivery_address"]}
            p=st.session_state.edit_point
            res=mount_map(points=[],center=[o["delivery_lat"] or 31.2001,o["delivery_lng"] or 29.9187],zoom=14,clickable=True,key=f"edit_map_{o['id']}")
            click=getattr(res,"map_click",None) if res else None
            if click:
                try: st.session_state.edit_point=json.loads(click); st.rerun()
                except Exception: pass
            p=st.session_state.edit_point
            a,b=st.columns(2); addr=a.text_input("العنوان",value=p.get("address",o["delivery_address"])); dist=b.number_input("المسافة",value=float(o["distance_km"]),min_value=0.0,step=.1)
            c,d=st.columns(2); eta=c.number_input("الوقت المتوقع",value=int(o["eta_minutes"]),min_value=0,step=1); fee=d.number_input("خدمة التوصيل",value=float(o["delivery_fee"]),min_value=0.0,step=1.0)
            notes=st.text_area("ملاحظات",value=o["notes"] or "")
            if st.button("حفظ التعديل",use_container_width=True):
                try: update_order(o["id"],{"order_no_old":o["order_no"],"delivery_address":addr,"delivery_lat":p.get("lat"),"delivery_lng":p.get("lng"),"distance_km":dist,"eta_minutes":eta,"delivery_fee":fee,"billing_mode":o["billing_mode"],"notes":notes},user); st.session_state.edit_point={}; st.success("تم حفظ التعديل."); st.rerun()
                except Exception as ex: st.error(str(ex))
    ticket=f"🚚 {APP_NAME}\nالطلب: {o['order_no']}\nالاستلام: {o['restaurant']} — {o['branch']}\nالتسليم: {o['delivery_address']}\nالتحصيل: {o['billing_mode']}\nالمسافة: {o['distance_km']} كم\nعمولة الطيار: {o['rider_commission']:.2f} ج\nالحالة: {o['status']}"
    st.code(ticket,language="text")
    if o["delivery_lat"] is not None: st.link_button("🧭 ملاحة للعنوان",f"https://www.google.com/maps/dir/?api=1&destination={o['delivery_lat']},{o['delivery_lng']}",use_container_width=True)


# =========================================================
# الطيارون / المستخدمون / المطاعم
# =========================================================
def render_riders(user):
    header("الطيارون","التحكم في النشاط، الراتب، GPS، والطلبات النشطة.")
    rs=df("SELECT * FROM riders ORDER BY active_orders,name")
    for _,r in rs.iterrows():
        fresh=gps_fresh(r.to_dict())
        with st.container(border=True):
            a,b,c,d=st.columns([2.2,1.2,1.1,1.5]); a.markdown(f"**{r['name']}**<br><span style='color:#6B7280;font-size:.7rem'>{r['phone'] or 'بدون هاتف'}</span>",unsafe_allow_html=True); b.markdown(badge("نشط" if r["status"]!="غير نشط" else "غير نشط","green" if r["status"]!="غير نشط" else "red"),unsafe_allow_html=True); c.write(f"{int(r['active_orders'])} طلبات"); d.write("🟢 GPS" if fresh else "🟠 GPS قديم")
            if user["role"]=="OWNER":
                x,y,z=st.columns(3)
                if x.button("تعطيل" if r["status"]!="غير نشط" else "تفعيل",key=f"ra_{r['id']}"):
                    try: set_active("rider",r["id"],r["status"]=="غير نشط",user); st.rerun()
                    except Exception as ex: st.error(str(ex))
                if y.button("تعديل بيانات",key=f"re_{r['id']}"): st.session_state[f"edit_rider_{r['id']}"]=not st.session_state.get(f"edit_rider_{r['id']}",False)
                if z.button("راتب الشهر",key=f"rp_{r['id']}"): st.session_state.payroll_rider=r["id"]; st.session_state.page="payroll"; st.rerun()
                if st.session_state.get(f"edit_rider_{r['id']}"):
                    a,b=st.columns(2); ph=a.text_input("الهاتف",value=r["phone"] or "",key=f"rph_{r['id']}"); sal=b.number_input("المرتب الأساسي",value=float(r["salary"]),step=100.0,key=f"rsal_{r['id']}")
                    if st.button("حفظ بيانات الطيار",key=f"rsave_{r['id']}"):
                        update_rider(r["id"],ph,sal,user); st.success("تم الحفظ."); st.rerun()
    if user["role"]=="OWNER":
        with st.expander("＋ إضافة طيار"):
            with st.form("add_rider"):
                a,b,c=st.columns(3); n=a.text_input("الاسم"); ph=b.text_input("الهاتف"); sal=c.number_input("المرتب الأساسي",min_value=0.0,value=float(get_setting("salary_basic",6000)),step=100.0)
                if st.form_submit_button("إضافة الطيار",type="primary",use_container_width=True):
                    try: create_rider({"name":n,"phone":ph,"salary":sal},user); st.success("تمت إضافة الطيار."); st.rerun()
                    except Exception as ex: st.error(str(ex))


def render_restaurants(user):
    header("المطاعم والفروع","الحالة، الحساب، والفروع مع تحديد المواقع بالنقر على الخريطة.")
    rs=all_restaurants()
    for _,r in rs.iterrows():
        bs=branches_for(r["id"],False)
        with st.container(border=True):
            a,b,c=st.columns([2,1,1.3]); a.markdown(f"**{r['name']}**<br><span style='color:#6B7280;font-size:.7rem'>{r['phone'] or ''}</span>",unsafe_allow_html=True); b.markdown(badge("نشط" if r["active"] else "غير نشط","green" if r["active"] else "red"),unsafe_allow_html=True); c.write(f"{r['billing_mode']} • {len(bs)} فروع")
            if user["role"]=="OWNER":
                x,y=st.columns(2)
                if x.button("تعطيل" if r["active"] else "تفعيل",key=f"restact_{r['id']}"):
                    try: set_active("restaurant",r["id"],not bool(r["active"]),user); st.rerun()
                    except Exception as ex: st.error(str(ex))
                if y.button("تعديل المطعم",key=f"restedit_{r['id']}"): st.session_state[f"rest_edit_{r['id']}"]=not st.session_state.get(f"rest_edit_{r['id']}",False)
                if st.session_state.get(f"rest_edit_{r['id']}",False):
                    a,b=st.columns(2); ph=a.text_input("الهاتف",value=r["phone"] or "",key=f"rphone_{r['id']}"); mode=b.selectbox("التحصيل",["كاش","آجل"],index=0 if r["billing_mode"]=="كاش" else 1,key=f"rmode_{r['id']}")
                    if st.button("حفظ المطعم",key=f"rsave_{r['id']}"): update_restaurant(r["id"],ph,mode,user); st.success("تم الحفظ."); st.rerun()
                if st.button("＋ إضافة/إدارة فرع",key=f"branch_{r['id']}"): st.session_state[f"branch_open_{r['id']}"]=not st.session_state.get(f"branch_open_{r['id']}",False)
            for _,br in bs.iterrows():
                x,y=st.columns([4,1]); x.markdown(f"• **{br['name']}** — {br['address'] or 'بدون عنوان'} — {('نشط' if br['active'] else 'غير نشط')}",unsafe_allow_html=True)
                if user["role"]=="OWNER" and y.button("تعطيل" if br["active"] else "تفعيل",key=f"bract_{br['id']}"):
                    try: set_active("branch",br["id"],not bool(br["active"]),user); st.rerun()
                    except Exception as ex: st.error(str(ex))
            if user["role"]=="OWNER" and st.session_state.get(f"branch_open_{r['id']}",False):
                if "branch_pick" not in st.session_state: st.session_state.branch_pick={}
                p=st.session_state.branch_pick
                res=mount_map(center=[31.2001,29.9187],zoom=12,clickable=True,key=f"branch_pick_map_{r['id']}"); click=getattr(res,"map_click",None) if res else None
                if click:
                    try: st.session_state.branch_pick=json.loads(click); st.rerun()
                    except Exception: pass
                p=st.session_state.branch_pick
                if p.get("lat") is not None: st.success(f"موقع الفرع: {p.get('address','')} — {p['lat']}, {p['lng']}")
                with st.form(f"add_branch_{r['id']}"):
                    a,b=st.columns(2); n=a.text_input("اسم الفرع"); addr=b.text_input("العنوان",value=p.get("address",""))
                    if st.form_submit_button("حفظ الفرع",type="primary",use_container_width=True):
                        try: create_branch({"restaurant_id":r["id"],"name":n,"address":addr,"lat":p.get("lat"),"lng":p.get("lng")},user); st.session_state.branch_pick={}; st.success("تمت إضافة الفرع."); st.rerun()
                        except Exception as ex: st.error(str(ex))
    if user["role"]=="OWNER":
        with st.expander("＋ إضافة مطعم"):
            with st.form("add_restaurant"):
                a,b,c=st.columns(3); n=a.text_input("اسم المطعم"); ph=b.text_input("الهاتف"); mode=c.selectbox("التحصيل",["كاش","آجل"])
                if st.form_submit_button("إضافة المطعم",type="primary",use_container_width=True):
                    try: create_restaurant({"name":n,"phone":ph,"billing_mode":mode},user); st.success("تمت إضافة المطعم."); st.rerun()
                    except Exception as ex: st.error(str(ex))


def render_users(user):
    header("المستخدمون والأمان","لا نعرض PIN القديم؛ المالك يستطيع إعادة تعيينه وإظهاره مرة واحدة.")
    us=df("SELECT id,name,email,role,ref_id,active,created_at FROM users ORDER BY name")
    for _,u in us.iterrows():
        with st.container(border=True):
            a,b,c,d=st.columns([2,1,1,1.5]); a.markdown(f"**{u['name']}**<br><span style='color:#6B7280;font-size:.7rem'>{u['email']}</span>",unsafe_allow_html=True); b.write(role_label(u["role"])); c.markdown(badge("نشط" if u["active"] else "غير نشط","green" if u["active"] else "red"),unsafe_allow_html=True); d.write("PIN: ••••••")
            if user["role"]=="OWNER" and u["id"]!=user["id"]:
                x,y=st.columns(2)
                if x.button("تعطيل" if u["active"] else "تفعيل",key=f"uact_{u['id']}"):
                    try: set_active("user",u["id"],not bool(u["active"]),user); st.rerun()
                    except Exception as ex: st.error(str(ex))
                if y.button("توليد PIN جديد",key=f"upin_{u['id']}"): st.session_state.generated_pin={"name":u["name"],"pin":reset_user_pin(u["id"],user)}; st.rerun()
    if st.session_state.get("generated_pin"):
        x=st.session_state.generated_pin; st.success(f"PIN الجديد لـ {x['name']}: {x['pin']} — سيظهر هنا مرة واحدة.")
        if st.button("إخفاء PIN",use_container_width=True): st.session_state.pop("generated_pin",None); st.rerun()
    with st.expander("＋ إنشاء مستخدم"):
        with st.form("create_user"):
            a,b=st.columns(2); n=a.text_input("الاسم"); e=b.text_input("البريد الإلكتروني"); c,d=st.columns(2); role=c.selectbox("الدور",["DISPATCHER","ACCOUNTANT","RIDER","RESTAURANT"]); pin=d.text_input("PIN أولي",type="password",max_chars=8); ref=None
            if role=="RIDER":
                rr=df("SELECT id,name FROM riders ORDER BY name")
                if rr.empty: st.warning("أضف الطيار أولاً.")
                else: rn=st.selectbox("ربط الطيار",rr["name"].tolist()); ref=rr[rr["name"]==rn].iloc[0]["id"]
            if role=="RESTAURANT":
                rr=all_restaurants()
                if rr.empty: st.warning("أضف المطعم أولاً.")
                else: rn=st.selectbox("ربط المطعم",rr["name"].tolist()); ref=rr[rr["name"]==rn].iloc[0]["id"]
            if st.form_submit_button("إنشاء المستخدم",type="primary",use_container_width=True):
                try: create_user({"name":n,"email":e,"role":role,"pin":pin,"ref_id":ref},user); st.success("تم إنشاء المستخدم."); st.rerun()
                except Exception as ex: st.error(str(ex))


# =========================================================
# حضور ومرتبات
# =========================================================
def render_attendance(user):
    header("الحضور وساعات العمل","الساعات تُحسب من الدخول إلى الخروج مع خصم وقت الراحة المسجل.")
    period=st.date_input("اختر الشهر",value=date.today().replace(day=1),key="attendance_month").strftime("%Y-%m")
    if user["role"]=="RIDER":
        rid=user["ref_id"]
        r=one("SELECT * FROM riders WHERE id=?",(rid,)); att=one("SELECT * FROM attendance WHERE rider_id=? AND work_date=?",(rid,today_str()))
        if not att or not att["clock_in"]:
            if st.button("🟢 تسجيل دخول الآن",type="primary",use_container_width=True): upsert_attendance({"rider_id":rid,"work_date":today_str(),"clock_in":now_iso(),"clock_out":None,"break_minutes":0,"status":"حاضر","reason":""},user); st.rerun()
        elif not att["clock_out"]:
            st.success(f"تم تسجيل الدخول: {att['clock_in']}")
            if st.button("🔴 تسجيل خروج الآن",type="primary",use_container_width=True): upsert_attendance({"rider_id":rid,"work_date":today_str(),"clock_in":att["clock_in"],"clock_out":now_iso(),"break_minutes":int(att.get("break_minutes") or 0),"status":"حاضر","reason":att.get("reason","")},user); st.rerun()
        stats=attendance_for_month(rid,period); hours=sum(attendance_hours(x) for x in stats.to_dict("records")) if not stats.empty else 0
        metric_grid([("ساعات الشهر",f"{hours:.2f}",f"المتوقع {float(get_setting('working_days',26))*float(get_setting('daily_work_hours',8)):.0f} ساعة","info"),("أيام حضور",int((stats["status"]=="حاضر").sum()) if not stats.empty else 0,"هذا الشهر","good"),("بعذر",int((stats["status"]=="إجازة بعذر").sum()) if not stats.empty else 0,"يوم","warn"),("بدون عذر",int((stats["status"]=="إجازة بدون عذر").sum()) if not stats.empty else 0,"يوم","danger")])
        if not stats.empty:
            view=stats.copy(); view["ساعات العمل"]=[attendance_hours(x) for x in stats.to_dict("records")]; st.dataframe(view[["work_date","status","clock_in","clock_out","break_minutes","ساعات العمل","reason"]].rename(columns={"work_date":"التاريخ","status":"الحالة","clock_in":"دخول","clock_out":"خروج","break_minutes":"راحة/دقيقة","reason":"السبب"}),use_container_width=True,hide_index=True)
        return
    riders=df("SELECT id,name FROM riders ORDER BY name")
    if user["role"]=="OWNER" and not riders.empty:
        with st.expander("＋ تسجيل/تعديل يوم"):
            with st.form("attendance_edit"):
                rn=st.selectbox("الطيار",riders["name"].tolist()); rid=riders[riders["name"]==rn].iloc[0]["id"]; wd=st.date_input("اليوم",value=date.today()); a,b=st.columns(2); ci=a.text_input("دخول (YYYY-MM-DD HH:MM:SS)"); co=b.text_input("خروج (YYYY-MM-DD HH:MM:SS)"); c,d,e=st.columns(3); br=c.number_input("راحة بالدقائق",min_value=0,value=0,step=5); status=d.selectbox("الحالة",["حاضر","إجازة بعذر","إجازة بدون عذر","غياب"]); reason=e.text_input("السبب")
                if st.form_submit_button("حفظ",type="primary",use_container_width=True):
                    try: upsert_attendance({"rider_id":rid,"work_date":wd.isoformat(),"clock_in":ci.strip() or None,"clock_out":co.strip() or None,"break_minutes":br,"status":status,"reason":reason},user); st.success("تم تسجيل الحضور."); st.rerun()
                    except Exception as ex: st.error(str(ex))
    rows=[]
    for _,r in riders.iterrows():
        stt=attendance_for_month(r["id"],period); rows.append({"الطيار":r["name"],"أيام الحضور":int((stt["status"]=="حاضر").sum()) if not stt.empty else 0,"بعذر":int((stt["status"]=="إجازة بعذر").sum()) if not stt.empty else 0,"بدون عذر":int((stt["status"]=="إجازة بدون عذر").sum()) if not stt.empty else 0,"ساعات العمل":round(sum(attendance_hours(x) for x in stt.to_dict("records")),2) if not stt.empty else 0})
    if rows: st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)


def render_payroll(user):
    header("القبض الشهري والمرتبات","المرتب الأساسي + العمولات + المكافآت − خصومات الإجازات − الخصومات/السلف، مع تسجيل كل دفعة في الخزينة.")
    period=st.date_input("الشهر",value=date.today().replace(day=1),key="payroll_month").strftime("%Y-%m")
    riders=df("SELECT id,name,salary FROM riders ORDER BY name")
    if riders.empty: st.info("لا يوجد طيارون."); return
    sel_id=st.session_state.get("payroll_rider",riders.iloc[0]["id"]); names=riders["name"].tolist(); idx=next((i for i,n in enumerate(names) if riders.iloc[i]["id"]==sel_id),0); rn=st.selectbox("الطيار",names,index=idx,key="payroll_select"); rid=riders[riders["name"]==rn].iloc[0]["id"]; st.session_state.payroll_rider=rid
    p=payroll_summary(rid,period)
    metric_grid([("الأساسي",f"{p['basic']:,.2f} ج","شهري","info"),("ساعات العمل",f"{p['hours']:.2f}",f"المتوقع {p['expected_hours']:.0f}","info"),("العمولات",f"{p['commissions']:,.2f} ج","طلبات مسلمة","good"),("خصم الإجازات",f"{p['leave_deduction']:,.2f} ج",f"بعذر {p['excused']} • بدون {p['unexcused']}","warn"),("صافي المستحق",f"{p['net']:,.2f} ج","قبل الدفعات","good"),("المتبقي",f"{p['remaining']:,.2f} ج",f"مدفوع {p['paid']:,.2f} ج","danger" if p['remaining']>0 else "good")])
    with st.expander("🧾 تفاصيل طريقة الحساب",expanded=True):
        st.write(f"المرتب الأساسي: {p['basic']:,.2f} ج"); st.write(f"خصم الإجازات: {p['leave_deduction']:,.2f} ج"); st.write(f"العمولات: +{p['commissions']:,.2f} ج"); st.write(f"المكافآت: +{p['rewards']:,.2f} ج"); st.write(f"خصومات الطلبات: -{p['discounts']:,.2f} ج"); st.write(f"إضافات: +{p['adjust_add']:,.2f} ج"); st.write(f"خصومات/سلف: -{p['adjust_deduct']:,.2f} ج"); st.write(f"**الصافي: {p['net']:,.2f} ج**")
    if user["role"] in ("OWNER","ACCOUNTANT"):
        a,b=st.columns(2)
        with a:
            with st.form("pay_salary"):
                amount=st.number_input("مبلغ القبض",min_value=0.0,max_value=max(0.0,p["remaining"]),value=0.0,step=100.0); method=st.selectbox("طريقة الدفع",["كاش","تحويل بنكي","محفظة إلكترونية"]); ref=st.text_input("مرجع/إيصال"); notes=st.text_input("ملاحظات")
                if st.form_submit_button("💸 تسجيل قبض المرتب",type="primary",use_container_width=True):
                    try: record_payroll_payment({"rider_id":rid,"period":period,"amount":amount,"method":method,"reference":ref,"notes":notes},user); st.success("تم تسجيل قبض المرتب وربطه بالخزينة."); st.rerun()
                    except Exception as ex: st.error(str(ex))
        with b:
            with st.form("payroll_adjust"):
                typ=st.selectbox("نوع التسوية",["إضافة","خصم","سلفة"]); amount=st.number_input("المبلغ",min_value=0.0,step=50.0); desc=st.text_input("الوصف")
                if st.form_submit_button("إضافة تسوية",use_container_width=True):
                    try: add_payroll_adjustment({"rider_id":rid,"period":period,"type":typ,"amount":amount,"description":desc},user); st.success("تمت الإضافة."); st.rerun()
                    except Exception as ex: st.error(str(ex))
    pay=df("SELECT paid_at,amount,method,reference,notes FROM payroll_payments WHERE rider_id=? AND period=? ORDER BY paid_at DESC",(rid,period))
    if not pay.empty: st.dataframe(pay.rename(columns={"paid_at":"وقت الدفع","amount":"المبلغ","method":"الطريقة","reference":"المرجع","notes":"ملاحظات"}),use_container_width=True,hide_index=True)


def render_settlements(user):
    header("التسويات والخزينة","افصل بين تصفية كاش الطيار، تحصيل الآجل من المطاعم، وصرف الرواتب.")
    if user["role"] in ("OWNER","DISPATCHER","ACCOUNTANT"):
        with st.container(border=True):
            st.markdown("### تصفية كاش الطيار")
            riders=df("SELECT id,name FROM riders ORDER BY name")
            if not riders.empty:
                rn=st.selectbox("الطيار",riders["name"].tolist(),key="sett_rider"); rid=riders[riders["name"]==rn].iloc[0]["id"]; a,b=st.columns(2); start=a.date_input("من",value=date.today()); end=b.date_input("إلى",value=date.today()); os=rider_unsettled_orders(rid,start.isoformat(),(end+timedelta(days=1)).isoformat()); gross=float(os["cash_collected"].sum()) if not os.empty else 0; comm=float(os["rider_commission"].sum()) if not os.empty else 0; rew=float(os["reward"].sum()) if not os.empty else 0; dis=float(os["discount"].sum()) if not os.empty else 0; due=gross-comm-rew+dis
                metric_grid([("عدد الطلبات",len(os),"غير مصفاة","info"),("الكاش",f"{gross:,.2f} ج","المتحصل","info"),("العمولات",f"{comm:,.2f} ج","لصالح الطيار","warn"),("التوريد",f"{due:,.2f} ج","المبلغ المطلوب للخزينة","good")])
                if st.button("إغلاق التصفية وتسجيل الخزينة",type="primary",use_container_width=True):
                    try: sid,due,n=create_rider_settlement(rid,start.isoformat(),(end+timedelta(days=1)).isoformat(),user); st.success(f"تمت التصفية: {n} طلب • صافي التوريد {due:,.2f} ج"); st.rerun()
                    except Exception as ex: st.error(str(ex))
        with st.container(border=True):
            st.markdown("### تحصيل مطعم آجل")
            rs=all_restaurants(); credit=rs[rs["billing_mode"]=="آجل"] if not rs.empty else rs
            if not credit.empty:
                rn=st.selectbox("المطعم",credit["name"].tolist(),key="sett_rest"); rid=credit[credit["name"]==rn].iloc[0]["id"]; a,b=st.columns(2); start=a.date_input("من",value=date.today(),key="rsstart"); end=b.date_input("إلى",value=date.today(),key="rsend"); os=restaurant_unsettled_orders(rid,start.isoformat(),(end+timedelta(days=1)).isoformat()); due=float(os["delivery_fee"].sum()) if not os.empty else 0; paid=st.number_input("المبلغ المحصل",min_value=0.0,max_value=due,value=due,step=10.0)
                st.markdown(f"**المديونية غير المسددة:** `{due:,.2f} ج`")
                if st.button("تسجيل تحصيل المطعم",type="primary",use_container_width=True):
                    try: create_restaurant_settlement(rid,start.isoformat(),(end+timedelta(days=1)).isoformat(),paid,user); st.success("تم تسجيل التحصيل."); st.rerun()
                    except Exception as ex: st.error(str(ex))
    st.markdown("### آخر الحركات المالية")
    ledger=df("SELECT created_at,txn_type,account_type,amount,direction,reference_id,description FROM ledger ORDER BY id DESC LIMIT 200")
    if not ledger.empty: st.dataframe(ledger.rename(columns={"created_at":"الوقت","txn_type":"نوع الحركة","account_type":"الحساب","amount":"المبلغ","direction":"الاتجاه","reference_id":"المرجع","description":"الوصف"}),use_container_width=True,hide_index=True)


# =========================================================
# التحليل
# =========================================================
def render_analysis(user):
    header("التحليل والأداء","قراءة تشغيلية ومالية من نفس البيانات — بدون إخفاء الأرقام المهمة.")
    start=st.date_input("من",value=date.today()-timedelta(days=29),key="an_start"); end=st.date_input("إلى",value=date.today(),key="an_end")
    orders=df("SELECT * FROM orders WHERE created_at>=? AND created_at<?",(start.isoformat()+" 00:00:00",(end+timedelta(days=1)).isoformat()+" 00:00:00"))
    if orders.empty: st.info("لا توجد بيانات للفترة."); return
    delivered=orders[orders["status"]=="تم التسليم"]; cancel=orders[orders["status"]=="ملغى"]; avg_time=0
    if not delivered.empty:
        vals=[]
        for _,o in delivered.iterrows():
            try: vals.append((datetime.strptime(o["delivered_at"],"%Y-%m-%d %H:%M:%S")-datetime.strptime(o["created_at"],"%Y-%m-%d %H:%M:%S")).total_seconds()/60)
            except Exception: pass
        avg_time=round(sum(vals)/len(vals),1) if vals else 0
    metric_grid([("إجمالي الطلبات",len(orders),"الفترة","info"),("نسبة التسليم",f"{len(delivered)/len(orders)*100:.1f}%","من إجمالي الطلبات","good"),("الإلغاء",len(cancel),f"{len(cancel)/len(orders)*100:.1f}%","من إجمالي الطلبات","danger"),("متوسط زمن التنفيذ",f"{avg_time:.1f} د","إنشاء → تسليم","info")])
    st.markdown("### أداء الطيارين")
    rrows=[]
    for _,r in df("SELECT id,name,salary FROM riders ORDER BY name").iterrows():
        od=delivered[delivered["rider_id"]==r["id"]]; att=attendance_for_month(r["id"],start.strftime("%Y-%m")); hrs=round(sum(attendance_hours(x) for x in att.to_dict("records")),2) if not att.empty else 0
        rrows.append({"الطيار":r["name"],"تم التسليم":len(od),"العمولات":round(float(od["rider_commission"].sum()),2) if not od.empty else 0,"الساعات":hrs,"متوسط العمولة/طلب":round(float(od["rider_commission"].mean()),2) if not od.empty else 0})
    if rrows: st.dataframe(pd.DataFrame(rrows),use_container_width=True,hide_index=True)
    st.markdown("### أداء المطاعم")
    rr=orders.groupby(["restaurant_id"])["id"].count().reset_index(name="طلبات"); names=df("SELECT id,name FROM restaurants")
    if not names.empty: rr=rr.merge(names,left_on="restaurant_id",right_on="id"); st.dataframe(rr[["name","طلبات"]].rename(columns={"name":"المطعم"}),use_container_width=True,hide_index=True)
    daily=orders.assign(التاريخ=orders["created_at"].str[:10]).groupby("التاريخ")["id"].count().reset_index(name="الطلبات")
    if not daily.empty: st.bar_chart(daily.set_index("التاريخ"))


# =========================================================
# الأدوات / backup / settings
# =========================================================
def render_tools(user):
    header("الأدوات والإعدادات","كل الإعدادات التي تؤثر في التشغيل والرواتب في مكان واحد.")
    if user["role"]=="OWNER":
        a,b,c=st.columns(3); salary=a.number_input("المرتب الأساسي الافتراضي",value=float(get_setting("salary_basic",6000)),step=100.0); work=b.number_input("أيام العمل الشهري",value=float(get_setting("working_days",26)),min_value=1.0,step=1.0); hours=c.number_input("ساعات العمل/اليوم",value=float(get_setting("daily_work_hours",8)),min_value=.5,step=.5)
        d,e,f=st.columns(3); gps=d.number_input("اعتبار GPS حديث حتى (ثانية)",value=float(get_setting("gps_fresh_seconds",30)),min_value=5.0,step=5.0); base=e.number_input("عمولة حتى 3 كم",value=float(get_setting("commission_base",10)),step=1.0); extra=f.number_input("إضافة لكل كم زائد",value=float(get_setting("commission_extra_per_km",5)),step=.5)
        if st.button("حفظ إعدادات التشغيل",type="primary",use_container_width=True):
            for k,v in [("salary_basic",salary),("working_days",work),("daily_work_hours",hours),("gps_fresh_seconds",gps),("commission_base",base),("commission_extra_per_km",extra)]: set_setting(k,v)
            st.success("تم حفظ الإعدادات.")
    mem=io.BytesIO()
    with zipfile.ZipFile(mem,"w",zipfile.ZIP_DEFLATED) as z:
        for t in SCHEMA: z.writestr(f"{t}.csv",df(f"SELECT * FROM {t}").to_csv(index=False,encoding="utf-8-sig"))
    st.download_button("📦 تنزيل نسخة بيانات ONWAY",data=mem.getvalue(),file_name=f"ONWAY_Backup_{today_str()}.zip",mime="application/zip",use_container_width=True)
    if user["role"] in ("OWNER","ACCOUNTANT"):
        with st.expander("سجل التدقيق"): st.dataframe(df("SELECT created_at,actor_id,action,entity,entity_id FROM audit_log ORDER BY id DESC LIMIT 500").rename(columns={"created_at":"الوقت","actor_id":"المستخدم","action":"العملية","entity":"الكيان","entity_id":"المعرف"}),use_container_width=True,hide_index=True)


# =========================================================
# شاشة الطيار
# =========================================================
def render_rider(user):
    r=one("SELECT * FROM riders WHERE id=?",(user["ref_id"],))
    if not r: st.error("حساب الطيار غير مرتبط بسجل صالح."); return
    header(f"🛵 {r['name']}","واجهة ميدانية: الطلب الحالي، الملاحة، GPS، والحضور — أقل عدد ممكن من الخطوات.")
    fresh=gps_fresh(r); metric_grid([("الحالة",r["status"],"الأسطول","info"),("طلبات نشطة",int(r["active_orders"]),"حالية","info"),("GPS","🟢 حديث" if fresh else "🟠 غير حديث","آخر تحديث","good" if fresh else "warn"),("المرتب الأساسي",f"{float(r['salary']):,.0f} ج","شهري","good")])
    gps_state=st.session_state.get("gps_status") or {}
    gps_hint="إذا كان الإذن مرفوضاً: من إعدادات المتصفح > أذونات الموقع > السماح لهذا الموقع، ثم أعد تحميل الصفحة." if gps_state.get("code")==1 else "اضغط «تشغيل موقعي» داخل الخريطة. أول مرة سيطلب المتصفح إذن الموقع."
    st.markdown(f'<div class="gps-panel"><div class="gps-title">📍 تتبع الموقع</div><div class="gps-sub">{gps_hint}<br>يُطلب إذن الموقع من الهاتف عند فتح الخريطة. بعد السماح، تُرسل النقاط بدقة مناسبة وبمعدل ذكي لتقليل استهلاك البطارية والاتصال.</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="section-title">🗺️ خريطتك ومسار المهمة</div>',unsafe_allow_html=True)
    my=df("SELECT o.*,rs.name restaurant,b.name branch,b.lat branch_lat,b.lng branch_lng FROM orders o JOIN restaurants rs ON rs.id=o.restaurant_id JOIN branches b ON b.id=o.branch_id WHERE o.rider_id=? AND o.status NOT IN ('تم التسليم','ملغى') ORDER BY o.created_at",(r["id"],))
    current_route=None
    if not my.empty and r.get("last_lat") is not None and r.get("last_lng") is not None:
        preview=my.iloc[0].to_dict()
        target=None
        if preview["status"] in ("جديد","تم التعيين","تم القبول") and preview.get("branch_lat") is not None:
            target=[float(preview["branch_lat"]),float(preview["branch_lng"])]
        elif preview.get("delivery_lat") is not None:
            target=[float(preview["delivery_lat"]),float(preview["delivery_lng"])]
        if target:
            current_route={"from":[float(r["last_lat"]),float(r["last_lng"])],"to":target}
    live_map_fragment(user, route=current_route)
    if my.empty:
        st.success("لا يوجد طلب نشط الآن — أنت جاهز للتوجيه.")
    else:
        current=my.iloc[0].to_dict(); st.markdown(f'<div class="highlight"><div class="card-title">{current["order_no"]} • {current["restaurant"]} — {current["branch"]}</div><div class="card-sub">📍 {current["delivery_address"]}<br>التحصيل: {current["billing_mode"]} • العمولة: {current["rider_commission"]:.2f} ج</div></div>',unsafe_allow_html=True)
        allowed=transitions(current["status"])
        if allowed:
            actions=allowed
            action=st.selectbox("الخطوة التالية",actions,key=f"r_action_{current['id']}")
            st.markdown('<div class="rider-action">',unsafe_allow_html=True)
            if st.button(f"✅ {action}",type="primary",use_container_width=True):
                try: change_order_status(current["id"],action,user); st.success("تم تحديث الطلب."); st.rerun()
                except Exception as ex: st.error(str(ex))
            st.markdown('</div>',unsafe_allow_html=True)
        if current["delivery_lat"] is not None: st.link_button("🧭 ابدأ الملاحة للعميل",f"https://www.google.com/maps/dir/?api=1&destination={current['delivery_lat']},{current['delivery_lng']}",use_container_width=True)
    # حضور سريع اليوم
    att=one("SELECT * FROM attendance WHERE rider_id=? AND work_date=?",(r["id"],today_str()))
    st.markdown("### ⏱️ يوم العمل")
    if not att or not att["clock_in"]:
        if st.button("🟢 تسجيل دخول",type="primary",use_container_width=True): upsert_attendance({"rider_id":r["id"],"work_date":today_str(),"clock_in":now_iso(),"clock_out":None,"break_minutes":0,"status":"حاضر","reason":""},user); st.rerun()
    elif not att["clock_out"]:
        st.info(f"دخلت الساعة {att['clock_in']}")
        if st.button("🔴 تسجيل خروج",type="primary",use_container_width=True): upsert_attendance({"rider_id":r["id"],"work_date":today_str(),"clock_in":att["clock_in"],"clock_out":now_iso(),"break_minutes":int(att.get("break_minutes") or 0),"status":"حاضر","reason":""},user); st.rerun()
    else: st.success(f"ساعات اليوم: {attendance_hours(att):.2f} ساعة")
    p=payroll_summary(r["id"],month_key()); st.caption(f"المرتب المستحق حتى الآن هذا الشهر: {p['net']:,.2f} ج • المدفوع: {p['paid']:,.2f} ج • المتبقي: {p['remaining']:,.2f} ج")


# =========================================================
# الملاحة / Sidebar
# =========================================================
def nav_menu(user):
    role=user["role"]
    if role=="OWNER": return [("الرئيسية","dashboard"),("الطلبات","orders"),("🗺️ الخريطة الحية","map"),("🧭 مركز الملاحة","navigation"),("الطيارون","riders"),("المطاعم والفروع","restaurants"),("الحضور والساعات","attendance"),("💰 القبض والمرتبات","payroll"),("التسويات والخزينة","settlements"),("التحليل والأداء","analysis"),("المستخدمون","users"),("الإعدادات والأدوات","tools")]
    if role=="DISPATCHER": return [("الرئيسية","dashboard"),("الطلبات","orders"),("🗺️ الخريطة الحية","map"),("الطيارون","riders"),("المطاعم والفروع","restaurants")]
    if role=="ACCOUNTANT": return [("الرئيسية","dashboard"),("الطلبات","orders"),("🗺️ الخريطة الحية","map"),("الحضور والساعات","attendance"),("💰 القبض والمرتبات","payroll"),("التسويات والخزينة","settlements"),("التحليل والأداء","analysis"),("الأدوات","tools")]
    if role=="RIDER": return [("مهمتي الآن","rider"),("🗺️ خريطتي","map"),("الحضور والساعات","attendance")]
    return [("الرئيسية","dashboard"),("طلبات المطعم","orders"),("🗺️ خريطة المطعم","map")]


def sidebar(user):
    st.sidebar.markdown(f'<div class="sidebar-title">🧡 {APP_NAME}</div><div class="sidebar-sub">{user["name"]} • {role_label(user["role"])}</div>',unsafe_allow_html=True)
    menu=nav_menu(user); labels=[x[0] for x in menu]
    current=st.session_state.get("page",menu[0][1]); current_label=next((x[0] for x in menu if x[1]==current),labels[0]); choice=st.sidebar.radio("القائمة",labels,index=labels.index(current_label)); st.session_state.page=dict(menu)[choice]
    st.sidebar.markdown("---")
    st.sidebar.caption(f"آخر تحديث للواجهة: {datetime.now().strftime('%H:%M:%S')}")
    if st.sidebar.button("تسجيل خروج كامل",use_container_width=True): st.session_state.clear(); st.rerun()


# =========================================================
# تنقل علوي بدلاً من Sidebar — يحافظ على كامل الشاشة
# =========================================================
def top_navigation(user):
    menu=nav_menu(user)
    if not menu: return
    current=st.session_state.get("page",menu[0][1])
    primary=menu[:5]
    extra=menu[5:]
    st.markdown('<div class="top-nav-panel"><div class="top-nav-label">التشغيل</div></div>',unsafe_allow_html=True)
    cols=st.columns(len(primary),gap="small")
    for i,(label,key) in enumerate(primary):
        if cols[i].button(label,type="primary" if current==key else "secondary",use_container_width=True,key=f"nav_top_{key}"):
            st.session_state.page=key; st.rerun()
    if extra:
        labels=[x[0] for x in extra]
        cur_label=next((x[0] for x in extra if x[1]==current), "المزيد…")
        choice=st.selectbox("",["المزيد…"]+labels,index=(labels.index(cur_label)+1 if cur_label in labels else 0),label_visibility="collapsed",key="top_nav_more")
        if choice!="المزيد…":
            st.session_state.page=dict(extra)[choice]; st.rerun()

# =========================================================
# تشغيل التطبيق
# =========================================================
setup_db()

if "user" not in st.session_state:
    login(); st.stop()

base_user=st.session_state.user
user=effective_user()
top_navigation(user)
page=st.session_state.get("page",nav_menu(user)[0][1])
try:
    if page=="dashboard": render_dashboard(user)
    elif page=="orders": render_orders(user)
    elif page=="map": render_live_map(user)
    elif page=="navigation": render_navigation_center(user)
    elif page=="riders": render_riders(user)
    elif page=="restaurants": render_restaurants(user)
    elif page=="attendance": render_attendance(user)
    elif page=="payroll": render_payroll(user)
    elif page=="settlements": render_settlements(user)
    elif page=="analysis": render_analysis(user)
    elif page=="users": render_users(user)
    elif page=="tools": render_tools(user)
    elif page=="rider": render_rider(user)
    else: render_dashboard(user)
except Exception as ex:
    st.error("حدث خطأ داخل الواجهة وتم حمايتك من توقف النظام.")
    if user.get("role")=="OWNER": st.exception(ex)
