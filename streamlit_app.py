import streamlit as st
import sqlite3
import base64
import pandas as pd
import json
import math
import hashlib
import hmac
import secrets
import io
import zipfile
import csv
from datetime import datetime, date, timedelta
from pathlib import Path

APP_NAME = "ONWAY DELIVERY"
DB_PATH = Path(st.secrets.get("ONWAY_DB_PATH", "onway_delivery.db")) if hasattr(st, "secrets") else Path("onway_delivery.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# =========================================================
# إعدادات التطبيق
# =========================================================
st.set_page_config(
    page_title=f"{APP_NAME} | نظام التشغيل",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@500;600;700;800;900&display=swap');
:root{--brand:#e53935;--brand2:#b71c1c;--navy:#0b1324;--navy2:#17233a;--page:#f5f7fa;--card:#fff;--ink:#101828;--muted:#667085;--line:#e4e7ec;--good:#12b76a;--warn:#f79009;--danger:#d92d20;--info:#2e90fa;--purple:#7a5af8;--shadow:0 8px 24px rgba(16,24,40,.065);--shadow2:0 18px 42px rgba(16,24,40,.11)}
html,body,[class*="css"]{font-family:'Cairo',Tahoma,Arial,sans-serif!important}*,*:before,*:after{box-sizing:border-box}
[data-testid="stAppViewContainer"]{background:linear-gradient(180deg,#fafbfd 0%,var(--page) 100%)}
[data-testid="stHeader"]{background:rgba(250,251,253,.78);backdrop-filter:blur(12px)}[data-testid="stDecoration"],#MainMenu,footer{display:none}
.block-container{max-width:1500px;padding:.65rem .8rem 4.6rem}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0a1020 0%,#101a2c 55%,#172338 100%);border-left:1px solid rgba(255,255,255,.06)}
[data-testid="stSidebar"] *{color:#f8fafc!important}[data-testid="stSidebar"] [data-testid="stRadio"] label{padding:.62rem .72rem!important;border-radius:12px!important;margin:.14rem 0!important;font-size:.88rem!important;font-weight:800!important;transition:.16s}[data-testid="stSidebar"] [data-testid="stRadio"] label:hover{background:rgba(255,255,255,.065)}
.sidebar-title{font-size:1.25rem;font-weight:900;text-align:center;letter-spacing:-.3px;margin:.55rem 0 .1rem}.sidebar-sub{font-size:.71rem!important;color:#cbd5e1!important;text-align:center;margin-bottom:1rem}
.app-topbar{display:flex;align-items:center;justify-content:space-between;gap:10px;background:rgba(255,255,255,.9);border:1px solid rgba(228,231,236,.9);border-radius:18px;padding:9px 12px;margin-bottom:10px;box-shadow:var(--shadow);backdrop-filter:blur(12px)}
.app-brand{display:flex;align-items:center;gap:9px;font-size:.92rem;font-weight:900;color:var(--ink)}.app-brand-mark{width:34px;height:34px;border-radius:11px;display:grid;place-items:center;background:linear-gradient(135deg,var(--brand),#ff6a63);color:#fff;box-shadow:0 7px 16px rgba(229,57,53,.22)}
.user-chip{display:flex;align-items:center;gap:7px;background:#f8fafc;border:1px solid var(--line);border-radius:999px;padding:5px 8px;color:var(--ink);font-size:.65rem;font-weight:900}.user-dot{width:8px;height:8px;border-radius:50%;background:var(--good);box-shadow:0 0 0 4px rgba(18,183,106,.10)}
.onway-hero{position:relative;overflow:hidden;background:linear-gradient(135deg,#0e1626 0%,#162135 58%,#8f1d1d 100%);color:#fff;border-radius:21px;padding:16px 18px;margin-bottom:11px;box-shadow:var(--shadow2)}
.onway-hero:after{content:"";position:absolute;left:-55px;bottom:-95px;width:180px;height:180px;border-radius:50%;background:rgba(255,255,255,.045)}.onway-hero h1{margin:0;font-size:1.38rem;font-weight:900;line-height:1.24;letter-spacing:-.45px}.onway-hero p{margin:.25rem 0 0;color:#d7deea;font-size:.73rem;line-height:1.65;max-width:850px}
.metric-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:9px;margin:0 0 12px}.metric{position:relative;overflow:hidden;background:var(--card);border:1px solid var(--line);border-radius:16px;min-height:88px;padding:12px 13px;box-shadow:var(--shadow)}.metric:before{content:"";position:absolute;right:0;top:0;width:4px;height:100%;background:var(--brand)}.metric.good:before{background:var(--good)}.metric.warn:before{background:var(--warn)}.metric.info:before{background:var(--info)}.metric.purple:before{background:var(--purple)}.metric .v{font-size:1.28rem;line-height:1.1;font-weight:900;color:var(--ink);letter-spacing:-.35px}.metric .l{font-size:.69rem;font-weight:900;color:#475467;margin-top:6px}.metric .small{font-size:.6rem;color:var(--muted);margin-top:1px}
.section-head{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:12px 0 7px}.section-title{font-size:.97rem;font-weight:900;color:var(--ink);margin:0}.section-sub{font-size:.69rem;color:var(--muted);line-height:1.55;margin:1px 0 0}.small-note{font-size:.63rem;color:var(--muted)}
.card,.soft-panel{background:#fff;border:1px solid var(--line);border-radius:17px;padding:12px 13px;box-shadow:var(--shadow)}.card + .card{margin-top:8px}.card-title{font-size:.84rem;font-weight:900;color:var(--ink);margin-bottom:3px}.card-muted{font-size:.68rem;color:var(--muted);line-height:1.7}
.order-list{display:grid;gap:8px}.order-item{background:#fff;border:1px solid var(--line);border-radius:15px;padding:10px 11px;box-shadow:0 4px 13px rgba(16,24,40,.04)}.order-row{display:flex;align-items:center;justify-content:space-between;gap:9px}.order-main{min-width:0}.order-no{font-size:.78rem;font-weight:900;color:var(--ink)}.order-route{font-size:.64rem;color:#475467;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.order-meta{display:flex;flex-wrap:wrap;gap:5px;margin-top:6px}
.status-pill,.status-active,.status-done,.status-cancel,.status-warn{display:inline-flex;align-items:center;gap:4px;padding:.22rem .58rem;border-radius:999px;font-size:.64rem;font-weight:900;white-space:nowrap}.status-pill{background:#f2f4f7;color:#344054}.status-active{background:#eff8ff;color:#175cd3}.status-done{background:#ecfdf3;color:#067647}.status-cancel{background:#fef3f2;color:#b42318}.status-warn{background:#fffaeb;color:#b54708}
.map-shell{background:#fff;border:1px solid var(--line);border-radius:18px;padding:6px;box-shadow:var(--shadow);overflow:hidden}.field-actions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.field-actions .stButton>button{min-height:60px!important;font-size:.95rem!important;border-radius:15px!important}
.stButton>button,.stDownloadButton>button,.stLinkButton>a{min-height:45px!important;border-radius:12px!important;border:1px solid var(--line)!important;font-weight:900!important;font-size:.8rem!important;box-shadow:none!important;transition:.12s!important}.stButton>button:hover,.stDownloadButton>button:hover,.stLinkButton>a:hover{transform:translateY(-1px);box-shadow:0 7px 16px rgba(16,24,40,.09)!important}
.stTextInput input,.stNumberInput input,.stTextArea textarea,.stDateInput input{min-height:45px!important;border-radius:12px!important;border:1px solid #d9dee7!important;background:#fff!important;font-size:15px!important}[data-baseweb="select"]>div{min-height:45px!important;border-radius:12px!important;border-color:#d9dee7!important;background:#fff!important}label{font-size:.72rem!important;font-weight:800!important;color:#344054!important}
[data-testid="stForm"]{border:1px solid var(--line)!important;border-radius:17px!important;padding:11px!important;background:#fff!important;box-shadow:var(--shadow)!important}[data-testid="stExpander"]{border:1px solid var(--line);border-radius:15px;background:#fff;overflow:hidden}.stAlert{border-radius:13px!important}[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#fff}
@media(max-width:1100px){.metric-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:700px){.block-container{padding:.4rem .48rem 5rem}.app-topbar{padding:8px 9px;border-radius:14px}.app-brand{font-size:.82rem}.app-brand-mark{width:31px;height:31px;border-radius:10px}.user-chip{font-size:.59rem;padding:5px 6px}.onway-hero{padding:14px 14px;border-radius:17px}.onway-hero h1{font-size:1.15rem}.onway-hero p{font-size:.66rem}.metric-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:7px}.metric{min-height:78px;padding:10px 11px;border-radius:14px}.metric .v{font-size:1.08rem}.metric .l{font-size:.62rem}.metric .small{font-size:.55rem}.section-title{font-size:.9rem}.section-sub{font-size:.64rem}.card{border-radius:14px;padding:10px}.stButton>button,.stDownloadButton>button,.stLinkButton>a{min-height:51px!important;font-size:.84rem!important}.stTextInput input,.stNumberInput input,.stTextArea textarea,[data-baseweb="select"]>div{min-height:50px!important;font-size:16px!important}.field-actions{grid-template-columns:1fr}.field-actions .stButton>button{min-height:62px!important;font-size:1rem!important}.order-no{font-size:.75rem}.order-route{font-size:.61rem}}
@media(max-width:390px){.user-chip{max-width:45%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.metric .v{font-size:1rem}.metric-grid{gap:6px}}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
""", unsafe_allow_html=True)

# توافق مع نسخ Streamlit الأقدم: إذا لم تتوفر fragments تعمل الشاشة بشكل عادي.
if not hasattr(st, 'fragment'):
    def _fragment_fallback(*args, **kwargs):
        return lambda f: f
    st.fragment = _fragment_fallback

# =========================================================
# قاعدة البيانات
# =========================================================
SCHEMA = {
    "settings": ["key TEXT PRIMARY KEY", "value TEXT NOT NULL"],
    "users": [
        "id TEXT PRIMARY KEY", "name TEXT NOT NULL", "email TEXT UNIQUE NOT NULL", "role TEXT NOT NULL",
        "ref_id TEXT", "pin_hash TEXT NOT NULL", "active INTEGER NOT NULL DEFAULT 1", "created_at TEXT NOT NULL"
    ],
    "restaurants": [
        "id TEXT PRIMARY KEY", "name TEXT NOT NULL", "phone TEXT", "billing_mode TEXT NOT NULL DEFAULT 'كاش'",
        "active INTEGER NOT NULL DEFAULT 1", "created_at TEXT NOT NULL"
    ],
    "branches": [
        "id TEXT PRIMARY KEY", "restaurant_id TEXT NOT NULL", "name TEXT NOT NULL", "address TEXT", "lat REAL", "lng REAL",
        "active INTEGER NOT NULL DEFAULT 1", "created_at TEXT NOT NULL"
    ],
    "riders": [
        "id TEXT PRIMARY KEY", "name TEXT NOT NULL", "phone TEXT", "salary REAL NOT NULL DEFAULT 6000",
        "status TEXT NOT NULL DEFAULT 'متاح'", "active_orders INTEGER NOT NULL DEFAULT 0",
        "last_lat REAL", "last_lng REAL", "gps_accuracy REAL", "heading REAL", "speed REAL", "last_gps_at TEXT",
        "created_at TEXT NOT NULL"
    ],
    "orders": [
        "id TEXT PRIMARY KEY", "order_no TEXT UNIQUE NOT NULL", "restaurant_id TEXT NOT NULL", "branch_id TEXT NOT NULL",
        "delivery_address TEXT NOT NULL", "delivery_lat REAL", "delivery_lng REAL", "distance_km REAL NOT NULL DEFAULT 0",
        "eta_minutes INTEGER NOT NULL DEFAULT 0", "billing_mode TEXT NOT NULL", "rider_id TEXT", "status TEXT NOT NULL",
        "delivery_fee REAL NOT NULL DEFAULT 0", "rider_commission REAL NOT NULL DEFAULT 0", "reward REAL NOT NULL DEFAULT 0",
        "discount REAL NOT NULL DEFAULT 0", "cash_collected REAL NOT NULL DEFAULT 0", "notes TEXT", "created_by TEXT NOT NULL",
        "created_at TEXT NOT NULL", "accepted_at TEXT", "picked_up_at TEXT", "delivered_at TEXT", "cancelled_at TEXT"
    ],
    "attendance": [
        "id TEXT PRIMARY KEY", "rider_id TEXT NOT NULL", "work_date TEXT NOT NULL", "clock_in TEXT", "clock_out TEXT",
        "status TEXT NOT NULL DEFAULT 'حاضر'", "reason TEXT", "created_at TEXT NOT NULL", "UNIQUE(rider_id, work_date)"
    ],
    "ledger": [
        "id INTEGER PRIMARY KEY AUTOINCREMENT", "txn_no TEXT UNIQUE NOT NULL", "txn_type TEXT NOT NULL", "account_type TEXT NOT NULL",
        "account_id TEXT", "amount REAL NOT NULL", "direction TEXT NOT NULL", "reference_id TEXT", "description TEXT",
        "created_by TEXT NOT NULL", "created_at TEXT NOT NULL"
    ],
    "settlements": [
        "id TEXT PRIMARY KEY", "kind TEXT NOT NULL", "party_id TEXT NOT NULL", "period_start TEXT NOT NULL", "period_end TEXT NOT NULL",
        "gross REAL NOT NULL DEFAULT 0", "commissions REAL NOT NULL DEFAULT 0", "rewards REAL NOT NULL DEFAULT 0",
        "discounts REAL NOT NULL DEFAULT 0", "cash_due REAL NOT NULL DEFAULT 0", "paid REAL NOT NULL DEFAULT 0",
        "created_by TEXT NOT NULL", "created_at TEXT NOT NULL"
    ],
    "settlement_items": [
        "id TEXT PRIMARY KEY", "settlement_id TEXT NOT NULL", "order_id TEXT NOT NULL", "amount REAL NOT NULL",
        "UNIQUE(settlement_id, order_id)"
    ],
    "gps_log": [
        "id INTEGER PRIMARY KEY AUTOINCREMENT", "rider_id TEXT NOT NULL", "lat REAL NOT NULL", "lng REAL NOT NULL",
        "accuracy REAL", "heading REAL", "speed REAL", "recorded_at TEXT NOT NULL"
    ],
    "audit_log": [
        "id INTEGER PRIMARY KEY AUTOINCREMENT", "actor_id TEXT", "action TEXT NOT NULL", "entity TEXT NOT NULL", "entity_id TEXT",
        "before_json TEXT", "after_json TEXT", "created_at TEXT NOT NULL"
    ],
}


def conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    return c


def now_iso():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_str():
    return date.today().isoformat()


def uid(prefix):
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"


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


def audit(actor_id, action, entity, entity_id=None, before=None, after=None):
    with conn() as c:
        c.execute(
            "INSERT INTO audit_log(actor_id,action,entity,entity_id,before_json,after_json,created_at) VALUES (?,?,?,?,?,?,?)",
            (actor_id, action, entity, entity_id, json.dumps(before, ensure_ascii=False, default=str) if before is not None else None,
             json.dumps(after, ensure_ascii=False, default=str) if after is not None else None, now_iso())
        )


def setup_db():
    with conn() as c:
        for table, cols in SCHEMA.items():
            c.execute(f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(cols)})")
        defaults = {
            "salary_basic": "6000",
            "working_days": "26",
            "excused_leave_days": "1",
            "unexcused_leave_days": "1.25",
            "commission_base_km": "3",
            "commission_base": "10",
            "commission_extra_per_km": "5",
            "gps_fresh_seconds": "30",
            "peak_gps_seconds": "15",
        }
        for k, v in defaults.items():
            c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES (?,?)", (k, v))
    with conn() as c:
        count = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    return count


def get_setting(key, default=None):
    with conn() as c:
        r = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return r[0] if r else default


def set_setting(key, value):
    with conn() as c:
        c.execute("INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))


def df(sql, params=()):
    with conn() as c:
        return pd.read_sql_query(sql, c, params=params)


def one(sql, params=()):
    with conn() as c:
        r = c.execute(sql, params).fetchone()
    return dict(r) if r else None


def exec_sql(sql, params=()):
    with conn() as c:
        cur = c.execute(sql, params)
        return cur.lastrowid


def commission_for_distance(distance):
    base_km = float(get_setting("commission_base_km", 3))
    base = float(get_setting("commission_base", 10))
    extra = float(get_setting("commission_extra_per_km", 5))
    d = max(0.0, float(distance or 0))
    # قاعدة الشركة كما طلبت: كل كيلومتر زائد يحسب فعلياً حسب الجزء العشري.
    if d <= base_km:
        return round(base, 2)
    return round(base + (d - base_km) * extra, 2)


def status_class(status):
    if status == "تم التسليم": return "status-done"
    if status == "ملغى": return "status-cancel"
    if status in ("في الطريق", "تم الاستلام", "تم القبول", "تم التعيين"): return "status-active"
    if status == "جديد": return "status-new"
    return "status-warn"


def transitions(status):
    return {
        "جديد": ["تم القبول", "ملغى"],
        "تم التعيين": ["تم القبول", "ملغى"],
        "تم القبول": ["تم الاستلام", "ملغى"],
        "تم الاستلام": ["في الطريق"],
        "في الطريق": ["تم التسليم"],
        "تم التسليم": [],
        "ملغى": [],
    }.get(status, [])


def role_label(role):
    return {
        "OWNER": "المالك",
        "DISPATCHER": "الديسباتشر",
        "ACCOUNTANT": "الحسابات",
        "RIDER": "الطيار",
        "RESTAURANT": "المطعم",
    }.get(role, role)


setup_db()

# =========================================================
# GPS component - يعمل داخل نفس ملف Python
# =========================================================
try:
    from streamlit.components.v2 import component as v2_component

    GPS_HTML = """
    <div id='gpsbox' style='font-family:Cairo,Arial;direction:rtl;padding:12px;border-radius:14px;background:#f7f7f8;border:1px solid #e5e7eb'>
      <div style='font-weight:800'>📍 التتبع الحي</div>
      <div id='gpsstatus' style='margin-top:6px;color:#6b7280;font-size:13px'>جاري تشغيل GPS...</div>
    </div>
    """
    GPS_JS = """
    export default function(component) {
      const { setTriggerValue } = component;
      let watch = null;
      const status = component.parentElement.querySelector('#gpsstatus');
      if (!navigator.geolocation) {
        status.textContent = 'الجهاز لا يدعم تحديد الموقع.';
        return;
      }
      const emit = (p) => {
        const c = p.coords;
        const payload = {
          lat: Number(c.latitude.toFixed(6)),
          lng: Number(c.longitude.toFixed(6)),
          accuracy: c.accuracy == null ? null : Number(c.accuracy.toFixed(1)),
          heading: c.heading == null ? null : Number(c.heading.toFixed(1)),
          speed: c.speed == null ? null : Number(c.speed.toFixed(1)),
          ts: Date.now()
        };
        setTriggerValue('location', JSON.stringify(payload));
        status.textContent = `🟢 GPS متصل • دقة ${payload.accuracy ?? '—'} م`;
      };
      watch = navigator.geolocation.watchPosition(emit, (e) => {
        status.textContent = '🔴 تعذر الحصول على الموقع: ' + e.message;
      }, { enableHighAccuracy:true, maximumAge:3000, timeout:10000 });
      return () => { if (watch !== null) navigator.geolocation.clearWatch(watch); };
    }
    """
    GPS_COMP = v2_component("onway_gps", html=GPS_HTML, js=GPS_JS, isolate_styles=True)
    HAS_GPS = True
except Exception:
    GPS_COMP = None
    HAS_GPS = False


def capture_gps(rider_id):
    if not HAS_GPS:
        st.info("ميزة GPS المباشرة تحتاج نسخة Streamlit حديثة. النظام يعمل بدونه.")
        return
    result = GPS_COMP(key=f"gps_{rider_id}")
    raw = getattr(result, "location", None)
    if raw:
        try:
            p = json.loads(raw)
            lat, lng = float(p["lat"]), float(p["lng"])
            if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                return
            with conn() as c:
                c.execute("UPDATE riders SET last_lat=?,last_lng=?,gps_accuracy=?,heading=?,speed=?,last_gps_at=?,status=CASE WHEN status='غير متصل' THEN 'متاح' ELSE status END WHERE id=?",
                          (lat,lng,p.get("accuracy"),p.get("heading"),p.get("speed"),now_iso(),rider_id))
                c.execute("INSERT INTO gps_log(rider_id,lat,lng,accuracy,heading,speed,recorded_at) VALUES (?,?,?,?,?,?,?)",
                          (rider_id,lat,lng,p.get("accuracy"),p.get("heading"),p.get("speed"),now_iso()))
        except Exception:
            pass

# =========================================================
# Bootstrap / login
# =========================================================
def create_owner():
    st.markdown('<div class="onway-hero"><h1>🚚 ONWAY DELIVERY</h1><p>إنشاء المالك الأول وتشغيل النظام من شاشة واحدة</p></div>', unsafe_allow_html=True)
    st.info("هذه الشاشة تظهر مرة واحدة فقط عند تشغيل قاعدة بيانات جديدة.")
    with st.form("first_owner"):
        name = st.text_input("اسم المالك")
        email = st.text_input("البريد الإلكتروني").strip().lower()
        p1 = st.text_input("PIN الدخول", type="password", max_chars=8)
        p2 = st.text_input("تأكيد PIN", type="password", max_chars=8)
        ok = st.form_submit_button("إنشاء النظام وبدء التشغيل", use_container_width=True)
        if ok:
            if not name or "@" not in email:
                st.error("اكتب الاسم والبريد بشكل صحيح.")
            elif not p1.isdigit() or len(p1) < 4:
                st.error("الـPIN يجب أن يكون أرقاماً لا تقل عن 4 أرقام.")
            elif p1 != p2:
                st.error("تأكيد الـPIN غير متطابق.")
            else:
                uidv = uid("USR")
                with conn() as c:
                    c.execute("INSERT INTO users(id,name,email,role,ref_id,pin_hash,active,created_at) VALUES (?,?,?,?,?,?,1,?)",
                              (uidv,name,email,"OWNER",None,hash_pin(p1),now_iso()))
                audit(uidv,"create","user",uidv,after={"name":name,"email":email,"role":"OWNER"})
                st.session_state.user = {"id":uidv,"name":name,"email":email,"role":"OWNER","ref_id":None}
                st.rerun()


def login():
    st.markdown('<div class="onway-hero"><h1>🚚 ONWAY DELIVERY</h1><p>نظام تشغيل وإدارة الدليفري — تسجيل الدخول</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="mobile-note">على الموبايل استخدم القائمة الجانبية للتنقل بين الوظائف.</div>', unsafe_allow_html=True)
    users = df("SELECT id,name,email,role,active FROM users WHERE active=1 ORDER BY name")
    if users.empty:
        create_owner()
        return False
    with st.form("login"):
        email = st.text_input("البريد الإلكتروني").strip().lower()
        pin = st.text_input("PIN", type="password", max_chars=8)
        if st.form_submit_button("دخول آمن", use_container_width=True):
            u = one("SELECT * FROM users WHERE lower(email)=? AND active=1", (email,))
            if u and verify_pin(pin, u["pin_hash"]):
                st.session_state.user = {"id":u["id"],"name":u["name"],"email":u["email"],"role":u["role"],"ref_id":u["ref_id"]}
                audit(u["id"],"login","user",u["id"])
                st.rerun()
            else:
                st.error("بيانات الدخول غير صحيحة.")
    return False


# =========================================================
# خدمات الطلبات / الحسابات
# =========================================================
def haversine_km(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return 9999.0
    r=6371.0
    p1=math.radians(float(lat1)); p2=math.radians(float(lat2))
    dp=math.radians(float(lat2)-float(lat1)); dl=math.radians(float(lon2)-float(lon1))
    a=math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.asin(math.sqrt(a))


def rider_score(r, pickup_lat=None, pickup_lng=None):
    active=float(r.get('active_orders') or 0)
    gps_age=9999.0
    if r.get('last_gps_at'):
        try: gps_age=max(0.0,(datetime.now()-datetime.strptime(r['last_gps_at'],'%Y-%m-%d %H:%M:%S')).total_seconds())
        except Exception: pass
    dist=haversine_km(r.get('last_lat'),r.get('last_lng'),pickup_lat,pickup_lng)
    freshness=min(gps_age/60.0,10.0)
    gps_penalty=10 if gps_age>float(get_setting('gps_fresh_seconds',30)) else freshness
    distance_penalty=min(dist,20.0)
    return active*12 + distance_penalty*2 + gps_penalty


def ranked_riders(pickup_lat=None, pickup_lng=None):
    r=available_riders()
    if r.empty: return r
    r=r.copy(); r['score']=[rider_score(row.to_dict(),pickup_lat,pickup_lng) for _,row in r.iterrows()]
    return r.sort_values(['score','active_orders','name']).reset_index(drop=True)


def get_restaurants(active_only=True):
    return df("SELECT * FROM restaurants WHERE active=1 ORDER BY name" if active_only else "SELECT * FROM restaurants ORDER BY name")


def get_branches(restaurant_id, active_only=True):
    q = "SELECT * FROM branches WHERE restaurant_id=? " + ("AND active=1 " if active_only else "") + "ORDER BY name"
    return df(q, (restaurant_id,))


def available_riders():
    return df("SELECT * FROM riders WHERE status IN ('متاح','في مهمة') ORDER BY active_orders ASC, name")


def order_amount_due(order_row):
    return float(order_row["cash_collected"] or 0)


def create_order(data, actor):
    oid = uid("ORD")
    with conn() as c:
        exists = c.execute("SELECT 1 FROM orders WHERE order_no=?", (data["order_no"],)).fetchone()
        if exists:
            raise ValueError("رقم الطلب موجود بالفعل.")
        branch = c.execute("SELECT * FROM branches WHERE id=? AND restaurant_id=? AND active=1", (data["branch_id"],data["restaurant_id"])).fetchone()
        if not branch:
            raise ValueError("الفرع غير تابع للمطعم المختار.")
        rider_comm = commission_for_distance(data["distance_km"])
        if data["billing_mode"] == "كاش":
            cash = float(data["delivery_fee"])
        else:
            cash = 0.0
        c.execute("""INSERT INTO orders(id,order_no,restaurant_id,branch_id,delivery_address,delivery_lat,delivery_lng,distance_km,eta_minutes,
                     billing_mode,rider_id,status,delivery_fee,rider_commission,reward,discount,cash_collected,notes,created_by,created_at)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (oid,data["order_no"],data["restaurant_id"],data["branch_id"],data["delivery_address"],data.get("delivery_lat"),data.get("delivery_lng"),
                   float(data["distance_km"]),int(data["eta_minutes"]),data["billing_mode"],data.get("rider_id"),
                   "تم التعيين" if data.get("rider_id") else "جديد",float(data["delivery_fee"]),rider_comm,float(data.get("reward",0)),float(data.get("discount",0)),cash,data.get("notes","") or "",actor["id"],now_iso()))
        if data.get("rider_id"):
            c.execute("UPDATE riders SET status='في مهمة', active_orders=active_orders+1 WHERE id=?", (data["rider_id"],))
    audit(actor["id"],"create","order",oid,after=data|{"order_id":oid,"rider_commission":rider_comm})
    return oid


def assign_rider(order_id, rider_id, actor):
    with conn() as c:
        old = c.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not old: raise ValueError("الطلب غير موجود.")
        old = dict(old)
        if old["status"] in ("تم التسليم","ملغى"): raise ValueError("لا يمكن تعيين طلب مغلق.")
        if old["rider_id"] == rider_id: return
        if old["rider_id"]:
            c.execute("UPDATE riders SET active_orders=MAX(0,active_orders-1) WHERE id=?", (old["rider_id"],))
            c.execute("UPDATE riders SET status=CASE WHEN active_orders=0 THEN 'متاح' ELSE status END WHERE id=?", (old["rider_id"],))
        if rider_id:
            r = c.execute("SELECT status FROM riders WHERE id=? AND status!='غير نشط'", (rider_id,)).fetchone()
            if not r: raise ValueError("الطيار غير متاح.")
            c.execute("UPDATE riders SET active_orders=active_orders+1,status='في مهمة' WHERE id=?", (rider_id,))
            c.execute("UPDATE orders SET rider_id=?,status=CASE WHEN status='جديد' THEN 'تم التعيين' ELSE status END WHERE id=?", (rider_id,order_id))
        else:
            c.execute("UPDATE orders SET rider_id=NULL,status='جديد' WHERE id=?", (order_id,))
        new = dict(c.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone())
    audit(actor["id"],"assign_rider","order",order_id,before=old,after=new)


def change_order_status(order_id, new_status, actor):
    with conn() as c:
        oldr = c.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not oldr: raise ValueError("الطلب غير موجود.")
        old = dict(oldr)
        if new_status not in transitions(old["status"]):
            raise ValueError(f"الانتقال من {old['status']} إلى {new_status} غير مسموح.")
        stamp = now_iso()
        cols = ["status=?"]
        vals = [new_status]
        if new_status == "تم القبول": cols.append("accepted_at=?"); vals.append(stamp)
        if new_status == "تم الاستلام": cols.append("picked_up_at=?"); vals.append(stamp)
        if new_status == "تم التسليم": cols.append("delivered_at=?"); vals.append(stamp)
        if new_status == "ملغى": cols.append("cancelled_at=?"); vals.append(stamp)
        vals.append(order_id)
        c.execute(f"UPDATE orders SET {', '.join(cols)} WHERE id=?", vals)
        if new_status in ("تم التسليم","ملغى") and old["rider_id"]:
            c.execute("UPDATE riders SET active_orders=MAX(0,active_orders-1) WHERE id=?", (old["rider_id"],))
            c.execute("UPDATE riders SET status=CASE WHEN active_orders=0 THEN 'متاح' ELSE status END WHERE id=?", (old["rider_id"],))
        if new_status == "تم التسليم":
            c.execute("INSERT INTO ledger(txn_no,txn_type,account_type,account_id,amount,direction,reference_id,description,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                      (uid("TXN"),"إيراد خدمة توصيل","خزينة",None,float(old["delivery_fee"]),"داخل",order_id,"إيراد خدمة توصيل",actor["id"],stamp))
        new = dict(c.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone())
    audit(actor["id"],"status_change","order",order_id,before=old,after=new)


def dashboard_data():
    t = today_str()
    o = df("SELECT * FROM orders WHERE substr(created_at,1,10)=?", (t,))
    if o.empty:
        total = cash = credit = completed = commission = rewards = discount = 0
    else:
        total = len(o)
        cash = int((o["billing_mode"] == "كاش").sum())
        credit = int((o["billing_mode"] == "آجل").sum())
        completed = int((o["status"] == "تم التسليم").sum())
        commission = float(o["rider_commission"].sum())
        rewards = float(o["reward"].sum())
        discount = float(o["discount"].sum())
    due_credit = float(df("SELECT COALESCE(SUM(delivery_fee),0) x FROM orders WHERE billing_mode='آجل' AND status='تم التسليم'")["x"][0]) if not o.empty else 0
    paid_credit = float(df("SELECT COALESCE(SUM(paid),0) x FROM settlements WHERE kind='مطعم'")["x"][0])
    restaurant_due = max(0, due_credit - paid_credit)
    treasury = float(df("SELECT COALESCE(SUM(CASE WHEN direction='داخل' THEN amount ELSE -amount END),0) x FROM ledger")["x"][0])
    riders = df("SELECT * FROM riders")
    gps_stale = 0
    if not riders.empty:
        cutoff = datetime.now() - timedelta(seconds=int(get_setting("gps_fresh_seconds",30)))
        for x in riders["last_gps_at"].dropna().tolist():
            try:
                if datetime.strptime(x,"%Y-%m-%d %H:%M:%S") < cutoff: gps_stale += 1
            except: pass
    return {"total":total,"cash_orders":cash,"credit_orders":credit,"completed":completed,"commission":commission,
            "rewards":rewards,"discount":discount,"restaurant_due":restaurant_due,"treasury":treasury,"gps_stale":gps_stale}


# =========================================================
# أدوات V3 المساندة — لا تغيّر Schema أو معادلات الحساب
# =========================================================
def gps_fresh(rider):
    raw = rider.get('last_gps_at') if isinstance(rider, dict) else None
    if not raw:
        return False
    try:
        age = (datetime.now() - datetime.strptime(raw, '%Y-%m-%d %H:%M:%S')).total_seconds()
        return age <= float(get_setting('gps_fresh_seconds', 30))
    except Exception:
        return False


def active_restaurants():
    return get_restaurants(True)


def all_restaurants():
    return get_restaurants(False)


def branches_for(restaurant_id, active_only=True):
    return get_branches(restaurant_id, active_only)


def order_with_names(order_no):
    return one(
        "SELECT o.*,r.name restaurant,b.name branch,COALESCE(ry.name,'—') rider "
        "FROM orders o JOIN restaurants r ON r.id=o.restaurant_id "
        "JOIN branches b ON b.id=o.branch_id LEFT JOIN riders ry ON ry.id=o.rider_id "
        "WHERE o.order_no=?", (order_no,)
    )


def notify_v3(kind, message):
    if kind == 'green':
        st.success(message)
    elif kind == 'red':
        st.error(message)
    elif kind == 'amber':
        st.warning(message)
    else:
        st.info(message)


def set_active(entity, entity_id, active, actor):
    table_map = {'rider':'riders', 'restaurant':'restaurants', 'branch':'branches', 'user':'users'}
    table = table_map.get(entity)
    if not table:
        raise ValueError('نوع السجل غير معروف.')
    old = one(f'SELECT * FROM {table} WHERE id=?', (entity_id,))
    if not old:
        raise ValueError('السجل غير موجود.')
    with conn() as c:
        if entity == 'rider':
            if active:
                c.execute("UPDATE riders SET status=CASE WHEN status='غير نشط' THEN 'متاح' ELSE status END WHERE id=?", (entity_id,))
            else:
                if int(old.get('active_orders') or 0) > 0:
                    raise ValueError('لا يمكن تعطيل طيار لديه طلبات نشطة.')
                c.execute("UPDATE riders SET status='غير نشط' WHERE id=?", (entity_id,))
        else:
            c.execute(f'UPDATE {table} SET active=? WHERE id=?', (1 if active else 0, entity_id))
    new = one(f'SELECT * FROM {table} WHERE id=?', (entity_id,))
    audit(actor['id'], 'activate' if active else 'deactivate', entity, entity_id, before=old, after=new)


def reset_user_pin(user_id, actor):
    u = one('SELECT * FROM users WHERE id=?', (user_id,))
    if not u:
        raise ValueError('المستخدم غير موجود.')
    pin = ''.join(secrets.choice('0123456789') for _ in range(6))
    with conn() as c:
        c.execute('UPDATE users SET pin_hash=? WHERE id=?', (hash_pin(pin), user_id))
    audit(actor['id'], 'reset_pin', 'user', user_id, after={'pin_reset': True})
    return pin


def create_user(data, actor):
    email = data['email'].strip().lower()
    pin = data['pin'].strip()
    if not data['name'].strip() or '@' not in email or len(pin) < 4 or not pin.isdigit():
        raise ValueError('الاسم والبريد وPIN صحيح مطلوبة.')
    uidv = uid('USR')
    with conn() as c:
        c.execute(
            'INSERT INTO users(id,name,email,role,ref_id,pin_hash,active,created_at) VALUES (?,?,?,?,?,?,1,?)',
            (uidv, data['name'].strip(), email, data['role'], data.get('ref_id'), hash_pin(pin), now_iso())
        )
    audit(actor['id'], 'create', 'user', uidv, after={k:v for k,v in data.items() if k != 'pin'} | {'id': uidv})
    return uidv


def create_restaurant(data, actor):
    if not data['name'].strip():
        raise ValueError('اسم المطعم مطلوب.')
    rid = uid('RST')
    with conn() as c:
        c.execute(
            'INSERT INTO restaurants(id,name,phone,billing_mode,active,created_at) VALUES (?,?,?,?,1,?)',
            (rid, data['name'].strip(), data.get('phone','').strip(), data['billing_mode'], now_iso())
        )
    audit(actor['id'], 'create', 'restaurant', rid, after=data | {'id': rid})
    return rid


def create_branch(data, actor):
    if not data['name'].strip():
        raise ValueError('اسم الفرع مطلوب.')
    if data.get('lat') is None or data.get('lng') is None:
        raise ValueError('اختَر موقع الفرع على الخريطة أولاً.')
    bid = uid('BRN')
    with conn() as c:
        c.execute(
            'INSERT INTO branches(id,restaurant_id,name,address,lat,lng,active,created_at) VALUES (?,?,?,?,?,?,1,?)',
            (bid, data['restaurant_id'], data['name'].strip(), data.get('address','').strip(), float(data['lat']), float(data['lng']), now_iso())
        )
    audit(actor['id'], 'create', 'branch', bid, after=data | {'id': bid})
    return bid


def create_rider(data, actor):
    if not data['name'].strip():
        raise ValueError('اسم الطيار مطلوب.')
    rid = uid('RYD')
    with conn() as c:
        c.execute(
            'INSERT INTO riders(id,name,phone,salary,status,created_at) VALUES (?,?,?,?,?,?)',
            (rid, data['name'].strip(), data.get('phone','').strip(), float(data.get('salary') or get_setting('salary_basic',6000)), 'متاح', now_iso())
        )
    audit(actor['id'], 'create', 'rider', rid, after=data | {'id': rid})
    return rid


def record_gps(rider_id, payload):
    lat = float(payload['lat']); lng = float(payload['lng'])
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return False
    stamp = now_iso()
    with conn() as c:
        c.execute(
            'UPDATE riders SET last_lat=?,last_lng=?,gps_accuracy=?,heading=?,speed=?,last_gps_at=? WHERE id=?',
            (lat, lng, payload.get('accuracy'), payload.get('heading'), payload.get('speed'), stamp, rider_id)
        )
        c.execute(
            'INSERT INTO gps_log(rider_id,lat,lng,accuracy,heading,speed,recorded_at) VALUES (?,?,?,?,?,?,?)',
            (rider_id, lat, lng, payload.get('accuracy'), payload.get('heading'), payload.get('speed'), stamp)
        )
    return True
# =========================================================
# ONWAY UI V3 — غرفة عمليات مرئية + خريطة + إدارة حالات
# هذا القسم يستبدل طبقة العرض فقط؛ لا يغير SCHEMA أو الحسابات الأساسية.
# =========================================================

# خريطة Leaflet تفاعلية: اختيار نقطة + علامات + مسار + GPS
MAP_COMPONENT_V3 = None
try:
    from streamlit.components.v2 import component as _onway_component

    MAP_HTML_V3 = '''
    <div id="ow-root" style="height:100%;min-height:430px;position:relative;border-radius:18px;overflow:hidden;background:#dde5ec">
      <div id="ow-map" style="position:absolute;inset:0"></div>
      <div id="ow-msg" style="display:none;position:absolute;top:12px;right:12px;z-index:1200;background:rgba(17,24,39,.93);color:#fff;border-radius:999px;padding:7px 11px;font:700 12px Cairo,Arial"></div>
    </div>
    '''
    MAP_CSS_V3 = '''
      @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@600;700;800;900&display=swap');
      .leaflet-container{background:#dfe6ec}.leaflet-popup-content{direction:rtl;font-family:Cairo,Arial;font-size:12px;line-height:1.65}
      .leaflet-control{font-family:Cairo,Arial}.ow-pin{display:flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:50%;border:2px solid #fff;box-shadow:0 3px 12px rgba(0,0,0,.3);font-size:18px}
    '''
    MAP_JS_V3 = '''
    export default function(component){
      const {data,setTriggerValue,setStateValue,parentElement}=component;
      const mapEl=parentElement.querySelector('#ow-map'); const msg=parentElement.querySelector('#ow-msg');
      if(!mapEl) return;
      let cfg={}; try{ cfg=JSON.parse(atob(data)); }catch(e){ return; }
      const load=src=>new Promise((resolve,reject)=>{ if(window.L){resolve();return;} const s=document.createElement('script');s.src=src;s.onload=resolve;s.onerror=reject;document.head.appendChild(s); });
      const safeText=(v)=>String(v??'').replace(/[<>&"']/g, ch=>({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;',"'":'&#39;'}[ch]));
      (async()=>{
        try{ await load('https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'); }catch(e){ msg.style.display='block';msg.textContent='تعذر تحميل الخريطة';return; }
        if(mapEl.__owMap){ try{mapEl.__owMap.remove();}catch(e){} mapEl.__owMap=null; }
        mapEl.innerHTML='';
        const center=cfg.center||[31.2001,29.9187];
        const map=L.map(mapEl,{zoomControl:false,preferCanvas:true}).setView(center,cfg.zoom||12);
        mapEl.__owMap=map;
        L.control.zoom({position:'bottomleft'}).addTo(map);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(map);
        const bounds=[];
        const marker=(p)=>{
          if(p.lat==null||p.lng==null) return;
          const colors={rider:p.online?'#16a34a':'#6b7280',order:'#dc2626',branch:'#c62828',self:'#2563eb'};
          const color=colors[p.kind]||'#c62828';
          const icon=L.divIcon({className:'',html:`<div class="ow-pin" style="background:${color}">${safeText(p.icon||'📍')}</div>`,iconSize:[34,34],iconAnchor:[17,17]});
          const m=L.marker([p.lat,p.lng],{icon}).addTo(map);
          let body=`<b>${safeText(p.title||'')}</b>`; if(p.meta) body+=`<br>${safeText(p.meta)}`;
          if(p.kind==='rider' && p.accuracy!=null) body+=`<br>دقة GPS: ${safeText(p.accuracy)} م`;
          m.bindPopup(body); m.on('click',()=>setTriggerValue('marker_click',JSON.stringify({id:p.id,kind:p.kind})));
          bounds.push([p.lat,p.lng]);
        };
        (cfg.points||[]).forEach(marker);
        if(cfg.route && cfg.route.from && cfg.route.to){
          const f=cfg.route.from,t=cfg.route.to;
          const url=`https://router.project-osrm.org/route/v1/driving/${f[1]},${f[0]};${t[1]},${t[0]}?overview=full&geometries=geojson`;
          fetch(url).then(r=>r.json()).then(d=>{
            if(d.routes&&d.routes[0]){
              const route=d.routes[0],coords=route.geometry.coordinates.map(x=>[x[1],x[0]]);
              L.polyline(coords,{color:'#c62828',weight:6,opacity:.9,lineCap:'round'}).addTo(map);
              setStateValue('route_meta',JSON.stringify({distance_m:route.distance,duration_s:route.duration}));
              map.fitBounds(coords,{padding:[35,35]});
            }
          }).catch(()=>{});
        } else if(bounds.length){ map.fitBounds(bounds,{padding:[35,35],maxZoom:15}); }
        if(cfg.clickable){
          map.on('click',(e)=>{
            const lat=Number(e.latlng.lat.toFixed(6)),lng=Number(e.latlng.lng.toFixed(6));
            msg.style.display='block';msg.textContent='جاري تحديد العنوان…';
            fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}&zoom=18&accept-language=ar`)
              .then(r=>r.json()).then(d=>{msg.style.display='none';const address=d.display_name||'موقع محدد';L.marker([lat,lng]).addTo(map).bindPopup(`<b>📍 الموقع المختار</b><br>${safeText(address)}`).openPopup();setTriggerValue('map_click',JSON.stringify({lat,lng,address}));})
              .catch(()=>{msg.style.display='none';setTriggerValue('map_click',JSON.stringify({lat,lng,address:''}));});
          });
        }
        if(cfg.geolocation && navigator.geolocation){
          let last=0;
          navigator.geolocation.watchPosition(pos=>{
            const now=Date.now(); if(now-last<4000) return; last=now; const c=pos.coords;
            setTriggerValue('gps',JSON.stringify({lat:Number(c.latitude.toFixed(6)),lng:Number(c.longitude.toFixed(6)),accuracy:c.accuracy==null?null:Number(c.accuracy.toFixed(1)),heading:c.heading==null?null:Number(c.heading.toFixed(1)),speed:c.speed==null?null:Number((c.speed||0).toFixed(1)),ts:now}));
          },e=>{msg.style.display='block';msg.textContent='🔴 GPS: '+e.message;},{enableHighAccuracy:true,maximumAge:3000,timeout:10000});
        }
      })();
      return ()=>{};
    }
    '''
    MAP_COMPONENT_V3 = _onway_component('onway_operational_map_v3',html=MAP_HTML_V3,css=MAP_CSS_V3,js=MAP_JS_V3,isolate_styles=True)
except Exception:
    MAP_COMPONENT_V3=None


def mount_map_v3(points=None, center=None, zoom=12, clickable=False, geolocation=False, route=None, key='mapv3'):
    cfg={'points':points or [],'center':center or [31.2001,29.9187],'zoom':zoom,'clickable':clickable,'geolocation':geolocation,'route':route}
    if MAP_COMPONENT_V3:
        payload=base64.b64encode(json.dumps(cfg,ensure_ascii=False).encode('utf-8')).decode('ascii')
        return MAP_COMPONENT_V3(key=key,data=payload)
    pts=[{'lat':p['lat'],'lon':p['lng']} for p in (points or []) if p.get('lat') is not None and p.get('lng') is not None]
    if pts: st.map(pd.DataFrame(pts),latitude='lat',longitude='lon',zoom=zoom,height=470)
    else: st.info('الخريطة التفاعلية تحتاج إصدار Streamlit حديثاً.')
    return None


def header_v3(title, subtitle=''):
    user=st.session_state.get('user',{})
    today=datetime.now().strftime('%Y/%m/%d')
    st.markdown(f'<div class="app-topbar"><div class="app-brand"><div class="app-brand-mark">🚚</div><div>{APP_NAME}</div></div><div class="user-chip"><span class="user-dot"></span>{user.get("name","مستخدم")} • {role_label(user.get("role",""))} • {today}</div></div>',unsafe_allow_html=True)
    st.markdown(f'<div class="onway-hero"><h1>{title}</h1><p>{subtitle}</p></div>',unsafe_allow_html=True)


def metric_v3(items):
    cards=[]
    for label,value,accent in items:
        low=(str(label)+' '+str(accent)).lower()
        kind='good' if any(x in low for x in ('خزينة','تم التسليم','حديث','جاهز')) else 'warn' if any(x in low for x in ('مديون','قديم','متأخر')) else 'info' if any(x in low for x in ('طلبات','كاش','تحصيل')) else 'purple' if 'عمول' in low else ''
        cards.append(f'<div class="metric {kind}"><div class="v">{value}</div><div class="l">{label}</div><div class="small">{accent}</div></div>')
    st.markdown('<div class="metric-grid">'+''.join(cards)+'</div>',unsafe_allow_html=True)


def badge_v3(text,kind='soft'):
    classes={'green':'status-done','red':'status-cancel','blue':'status-active','amber':'status-warn','soft':'status-pill'}
    return f'<span class="{classes.get(kind,"status-pill")}">{text}</span>'


def render_live_map_v3(user, compact=False):
    @st.fragment(run_every='5s')
    def block():
        riders=df("SELECT id,name,status,active_orders,last_lat,last_lng,gps_accuracy,last_gps_at FROM riders WHERE status!='غير نشط' AND last_lat IS NOT NULL AND last_lng IS NOT NULL")
        orders=df("SELECT id,order_no,status,delivery_address,delivery_lat,delivery_lng,rider_id FROM orders WHERE status NOT IN ('تم التسليم','ملغى') AND delivery_lat IS NOT NULL AND delivery_lng IS NOT NULL")
        if user['role']=='RIDER': orders=orders[orders['rider_id']==user['ref_id']]
        selected_rider=None
        if not compact and user['role']!='RIDER' and not riders.empty:
            names={'الكل':None}; names.update(dict(zip(riders['name'],riders['id']))); sel=st.selectbox('متابعة طيار',list(names),key='live_filter_rider'); selected_rider=names[sel]
        points=[]; route=None
        for _,r in riders.iterrows():
            if selected_rider and r['id']!=selected_rider: continue
            fresh=gps_fresh(r.to_dict())
            points.append({'id':r['id'],'kind':'rider','icon':'🚴','lat':r['last_lat'],'lng':r['last_lng'],'online':fresh,'accuracy':r['gps_accuracy'],'title':r['name'],'meta':f"{r['status']} • {int(r['active_orders'])} طلبات • آخر تحديث {r['last_gps_at'] or '—'}"})
        for _,o in orders.iterrows():
            if selected_rider and o['rider_id']!=selected_rider: continue
            points.append({'id':o['id'],'kind':'order','icon':'📦','lat':o['delivery_lat'],'lng':o['delivery_lng'],'online':True,'title':o['order_no'],'meta':f"{o['status']} • {o['delivery_address']}"})
            if selected_rider and not route:
                r=riders[riders['id']==selected_rider]
                if not r.empty and r.iloc[0]['last_lat'] is not None: route={'from':[r.iloc[0]['last_lat'],r.iloc[0]['last_lng']],'to':[o['delivery_lat'],o['delivery_lng']]}
        if points:
            result=mount_map_v3(points,center=[31.2001,29.9187],zoom=12,route=route,geolocation=False,key='owner_live_map_v3' if compact else 'owner_live_map_full_v3')
            if result:
                marker_click=getattr(result,'marker_click',None)
                if marker_click:
                    try: st.session_state.map_selected=json.loads(marker_click)
                    except Exception: pass
        else: st.info('لا يوجد GPS حي أو طلبات ذات موقع مسجل حتى الآن.')
        if not riders.empty and not compact:
            view=riders.copy(); view['الحالة الحالية']=[('🟢 GPS حديث' if gps_fresh(x.to_dict()) else '🟠 GPS قديم') for _,x in riders.iterrows()]
            st.dataframe(view[['name','status','active_orders','gps_accuracy','last_gps_at','الحالة الحالية']].rename(columns={'name':'الطيار','status':'الحالة','active_orders':'طلبات نشطة','gps_accuracy':'دقة GPS','last_gps_at':'آخر تحديث'}),use_container_width=True,hide_index=True)
    block()


def render_dashboard_v3(user):
    if user['role']=='RIDER':
        return render_rider_v3(user)
    if user['role']=='RESTAURANT':
        rs=df("SELECT * FROM orders WHERE restaurant_id=? ORDER BY created_at DESC LIMIT 60",(user.get('ref_id'),))
        header_v3('مرحباً بك','لوحة المطعم — الطلبات والحالة المالية بدون تفاصيل تشغيلية لا تحتاجها.')
        metric_v3([('طلبات',len(rs),'إجمالي المعروض'),('قيد التنفيذ',int(rs['status'].isin(['جديد','تم التعيين','تم القبول','تم الاستلام','في الطريق']).sum()) if not rs.empty else 0,'نشطة'),('تم التسليم',int((rs['status']=='تم التسليم').sum()) if not rs.empty else 0,'مكتملة')])
        st.dataframe(rs[['order_no','status','billing_mode','delivery_address','delivery_fee','created_at']].rename(columns={'order_no':'الطلب','status':'الحالة','billing_mode':'التحصيل','delivery_address':'العنوان','delivery_fee':'خدمة التوصيل','created_at':'الوقت'}),use_container_width=True,hide_index=True)
        return
    header_v3('غرفة العمليات','المعلومات المهمة أمامك أولاً: الطلبات، الأسطول، السيولة، والاستثناءات.')
    d=dashboard_data()
    metric_v3([('طلبات اليوم',d['total'],'كل الطلبات'),('كاش / آجل',f"{d['cash_orders']} / {d['credit_orders']}",'تحصيل'),('تم التسليم',d['completed'],'مغلقة'),('عمولات الطيارين',f"{d['commission']:,.2f} ج",'اليوم'),('مديونية آجل',f"{d['restaurant_due']:,.2f} ج",'تحتاج تحصيل'),('الخزينة',f"{d['treasury']:,.2f} ج",'الرصيد الدفتري')])
    if user['role']=='OWNER':
        st.markdown('<div class="section-title">🗺️ الخريطة الرئيسية</div>',unsafe_allow_html=True)
        render_live_map_v3(user,compact=True)
    o=df("SELECT o.order_no,r.name restaurant,b.name branch,o.status,o.billing_mode,COALESCE(ry.name,'—') rider,o.delivery_address,o.created_at FROM orders o JOIN restaurants r ON r.id=o.restaurant_id JOIN branches b ON b.id=o.branch_id LEFT JOIN riders ry ON ry.id=o.rider_id ORDER BY o.created_at DESC LIMIT 40")
    if not o.empty:
        st.markdown('<div class="section-title">آخر حركة</div>',unsafe_allow_html=True)
        st.dataframe(o.rename(columns={'order_no':'الطلب','restaurant':'المطعم','branch':'الفرع','status':'الحالة','billing_mode':'التحصيل','rider':'الطيار','delivery_address':'العنوان','created_at':'الوقت'}),use_container_width=True,hide_index=True)


def render_orders_v3(user):
    header_v3('الطلبات','مركز التشغيل: الطلب من إنشائه حتى التسليم — بدون إدخال إحداثيات يدوياً.')
    if user['role'] in ('OWNER','DISPATCHER'):
        with st.expander('＋ إنشاء طلب',expanded=False):
            rs=active_restaurants()
            if rs.empty: st.warning('أضف مطعماً نشطاً أولاً.')
            else:
                rmap=dict(zip(rs['name'],rs['id'])); rn=st.selectbox('المطعم',list(rmap),key='newv3_rest'); rid=rmap[rn]
                bs=branches_for(rid)
                if bs.empty: st.warning('أضف فرعاً أولاً.')
                else:
                    bmap=dict(zip(bs['name'],bs['id'])); bn=st.selectbox('الفرع',list(bmap),key='newv3_branch'); br=bs[bs['id']==bmap[bn]].iloc[0].to_dict()
                    st.markdown('<div class="section-sub">اختر عنوان العميل بالنقر على الخريطة. سيظهر العنوان تلقائياً، ولا تحتاج لكتابة خطوط الطول والعرض.</div>',unsafe_allow_html=True)
                    if 'newv3_point' not in st.session_state: st.session_state.newv3_point={}
                    point=st.session_state.newv3_point
                    center=[br.get('lat') or 31.2001,br.get('lng') or 29.9187]
                    route={'from':[br.get('lat') or 31.2001,br.get('lng') or 29.9187],'to':[point['lat'],point['lng']]} if point.get('lat') is not None else None
                    res=mount_map_v3(points=[{'id':'branch','kind':'branch','icon':'🏪','lat':br.get('lat'),'lng':br.get('lng'),'online':True,'title':bn,'meta':br.get('address','')}],center=center,zoom=14,clickable=True,route=route,key='newv3_pick_map')
                    click=getattr(res,'map_click',None) if res else None
                    if click:
                        try: st.session_state.newv3_point=json.loads(click); st.rerun()
                        except Exception: pass
                    point=st.session_state.newv3_point
                    if point.get('lat') is not None:
                        route_meta=getattr(res,'route_meta',None) if res else None
                        if route_meta:
                            try: st.session_state.newv3_distance=round(float(json.loads(route_meta)['distance_m'])/1000,2)
                            except Exception: pass
                        elif 'newv3_distance' not in st.session_state:
                            st.session_state.newv3_distance=round(haversine_km(center[0],center[1],point['lat'],point['lng']),2)
                        notify='تم اختيار موقع التسليم: ' + (point.get('address') or f"{point['lat']}, {point['lng']}")
                        st.success(notify)
                    with st.form('newv3_order_form'):
                        a,b=st.columns(2); order_no=a.text_input('رقم الطلب'); address=b.text_input('عنوان التسليم',value=point.get('address',''))
                        c,d,e=st.columns(3); distance=c.number_input('المسافة التشغيلية (كم)',min_value=0.0,value=float(st.session_state.get('newv3_distance',3.0)),step=.1); eta=d.number_input('الوقت المتوقع',min_value=0,value=20,step=1); billing=e.selectbox('التحصيل',['كاش','آجل'],index=0 if rs[rs['id']==rid].iloc[0]['billing_mode']=='كاش' else 1)
                        f,g,h=st.columns(3); fee=f.number_input('خدمة التوصيل',min_value=0.0,value=30.0,step=1.0); reward=g.number_input('مكافأة',min_value=0.0,value=0.0,step=1.0); discount=h.number_input('خصم',min_value=0.0,value=0.0,step=1.0)
                        rr=ranked_riders(br.get('lat'),br.get('lng')); opts={'تعيين لاحقاً':None};
                        if not rr.empty: opts.update(dict(zip(rr['name'],rr['id'])))
                        rider_name=st.selectbox('الطيار',list(opts),index=1 if len(opts)>1 else 0)
                        comm=commission_for_distance(distance); st.markdown(f'<div class="card"><b>عمولة الطيار المحسوبة:</b> {comm:,.2f} ج</div>',unsafe_allow_html=True)
                        notes=st.text_area('ملاحظات')
                        if st.form_submit_button('🚀 حفظ وإطلاق الطلب',use_container_width=True):
                            if not order_no.strip() or not address.strip(): st.error('رقم الطلب والعنوان مطلوبان.')
                            else:
                                try:
                                    oid=create_order({'order_no':order_no.strip(),'restaurant_id':rid,'branch_id':bmap[bn],'delivery_address':address,'delivery_lat':point.get('lat'),'delivery_lng':point.get('lng'),'distance_km':distance,'eta_minutes':eta,'billing_mode':billing,'rider_id':opts[rider_name],'delivery_fee':fee,'reward':reward,'discount':discount,'notes':notes},user)
                                    st.session_state.pop('newv3_point',None); st.session_state.pop('newv3_distance',None); st.success(f'تم إنشاء {order_no} بنجاح.'); st.rerun()
                                except Exception as ex: st.error(str(ex))
    q="SELECT o.*,r.name restaurant,b.name branch,COALESCE(ry.name,'—') rider FROM orders o JOIN restaurants r ON r.id=o.restaurant_id JOIN branches b ON b.id=o.branch_id LEFT JOIN riders ry ON ry.id=o.rider_id WHERE 1=1"; params=[]
    if user['role']=='RESTAURANT': q+=' AND o.restaurant_id=?'; params.append(user['ref_id'])
    if user['role']=='RIDER': q+=' AND o.rider_id=?'; params.append(user['ref_id'])
    s=st.text_input('🔎 ابحث عن طلب أو عنوان'); sf=st.selectbox('الحالة',['الكل','جديد','تم التعيين','تم القبول','تم الاستلام','في الطريق','تم التسليم','ملغى'])
    if s: q+=' AND (o.order_no LIKE ? OR o.delivery_address LIKE ?)'; params += [f'%{s}%',f'%{s}%']
    if sf!='الكل': q+=' AND o.status=?'; params.append(sf)
    q+=' ORDER BY o.created_at DESC LIMIT 300'; orders=df(q,tuple(params))
    if orders.empty: st.info('لا توجد طلبات مطابقة.') ; return
    st.dataframe(orders[['order_no','restaurant','branch','status','billing_mode','rider','delivery_address','distance_km','delivery_fee','rider_commission','created_at']].rename(columns={'order_no':'الطلب','restaurant':'المطعم','branch':'الفرع','status':'الحالة','billing_mode':'التحصيل','rider':'الطيار','delivery_address':'العنوان','distance_km':'كم','delivery_fee':'الخدمة','rider_commission':'العمولة','created_at':'الوقت'}),use_container_width=True,hide_index=True)
    if user['role'] in ('OWNER','DISPATCHER','ACCOUNTANT','RIDER'):
        selected=st.selectbox('فتح الطلب',orders['order_no'].tolist(),key='open_order_v3'); o=order_with_names(selected)
        if not o: return
        metric_v3([('الحالة',o['status'],o['rider']),('الخدمة',f"{o['delivery_fee']:,.2f} ج",'قيمة التوصيل'),('العمولة',f"{o['rider_commission']:,.2f} ج",'قاعدة المسافة'),('التحصيل',o['billing_mode'],'طريقة الحساب')])
        if user['role'] in ('OWNER','DISPATCHER'):
            rr=df("SELECT id,name,status,active_orders FROM riders WHERE status!='غير نشط' ORDER BY active_orders,name"); names={'بدون طيار':None}; names.update(dict(zip(rr['name'],rr['id']))) if not rr.empty else None
            current=o['rider'] if o['rider'] in names else 'بدون طيار'; sel=st.selectbox('تعيين الطيار',list(names),index=list(names).index(current),key='assignv3')
            if st.button('حفظ التعيين',use_container_width=True):
                try: assign_rider(o['id'],names[sel],user); st.success('تم تحديث التعيين.'); st.rerun()
                except Exception as ex: st.error(str(ex))
        allowed=transitions(o['status'])
        if user['role'] in ('OWNER','DISPATCHER','RIDER') and allowed:
            ns=st.selectbox('الإجراء التالي',allowed,key=f'nextv3_{o["id"]}')
            if st.button('تأكيد الإجراء',use_container_width=True):
                try: change_order_status(o['id'],ns,user); st.success('تم تحديث الحالة.'); st.rerun()
                except Exception as ex: st.error(str(ex))
        ticket=f"🚚 ONWAY\nالطلب: {o['order_no']}\nالاستلام: {o['restaurant']} — {o['branch']}\nالتسليم: {o['delivery_address']}\nالتحصيل: {o['billing_mode']}\nالمسافة: {o['distance_km']} كم\nعمولة الطيار: {o['rider_commission']:.2f} ج\nالحالة: {o['status']}"
        st.code(ticket,language='text')
        if o['delivery_lat'] is not None: st.link_button('🧭 فتح الملاحة',f"https://www.google.com/maps/dir/?api=1&destination={o['delivery_lat']},{o['delivery_lng']}")


def render_rider_v3(user):
    rider=one('SELECT * FROM riders WHERE id=?',(user['ref_id'],))
    if not rider: st.error('حساب الطيار غير مرتبط بسجل طيار صالح.'); return
    header_v3(f"🚴 {rider['name']}","شاشة الميدان — الأزرار كبيرة والمعلومات الضرورية فقط.")
    metric_v3([('الحالة',rider['status'],'الأسطول'),('طلبات نشطة',rider['active_orders'],'حالية'),('GPS','🟢 حديث' if gps_fresh(rider) else '🟠 غير حديث','آخر تحديث')])
    my=df("SELECT o.*,r.name restaurant,b.name branch FROM orders o JOIN restaurants r ON r.id=o.restaurant_id JOIN branches b ON b.id=o.branch_id WHERE o.rider_id=? AND o.status NOT IN ('تم التسليم','ملغى') ORDER BY o.created_at",(rider['id'],))
    current=my.iloc[0].to_dict() if not my.empty else None
    route={'from':[rider['last_lat'],rider['last_lng']],'to':[current['delivery_lat'],current['delivery_lng']]} if current and rider['last_lat'] is not None and current['delivery_lat'] is not None else None
    points=[]
    if rider['last_lat'] is not None: points.append({'id':'self','kind':'self','icon':'🚴','lat':rider['last_lat'],'lng':rider['last_lng'],'online':gps_fresh(rider),'title':'موقعي','meta':f"دقة {rider['gps_accuracy'] or '—'} م"})
    if current and current['delivery_lat'] is not None: points.append({'id':current['id'],'kind':'order','icon':'📦','lat':current['delivery_lat'],'lng':current['delivery_lng'],'online':True,'title':current['order_no'],'meta':current['delivery_address']})
    res=mount_map_v3(points,center=[rider['last_lat'] or 31.2001,rider['last_lng'] or 29.9187],zoom=14,route=route,geolocation=True,key='rider_map_v3')
    gps=getattr(res,'gps',None) if res else None
    if gps:
        try: record_gps(rider['id'],json.loads(gps)); st.rerun()
        except Exception: pass
    if current:
        st.markdown(f'<div class="card"><div class="list-main">{current["order_no"]} — {current["restaurant"]} / {current["branch"]}</div><div class="list-meta">{current["delivery_address"]}</div><div style="margin-top:8px">{badge_v3(current["status"],"blue")} {badge_v3(current["billing_mode"],"soft")}</div></div>',unsafe_allow_html=True)
        allowed=transitions(current['status'])
        if allowed:
            ns=st.selectbox('الإجراء التالي',allowed,key='rider_next_v3');
            if st.button('تنفيذ الإجراء',use_container_width=True):
                try: change_order_status(current['id'],ns,user); st.rerun()
                except Exception as ex: st.error(str(ex))
        if current['delivery_lat'] is not None: st.link_button('🧭 ابدأ الملاحة',f"https://www.google.com/maps/dir/?api=1&destination={current['delivery_lat']},{current['delivery_lng']}")
    else: st.success('لا يوجد طلب نشط الآن. أنت جاهز لاستقبال التوجيه.')
    att=one('SELECT * FROM attendance WHERE rider_id=? AND work_date=?',(rider['id'],today_str()))
    if not att or not att['clock_in']:
        if st.button('🟢 تسجيل دخول',use_container_width=True):
            with db() as c: c.execute('INSERT INTO attendance(id,rider_id,work_date,clock_in,status,created_at) VALUES (?,?,?,?,?,?)',(uid('ATT'),rider['id'],today_str(),now_iso(),'حاضر',now_iso()))
            st.rerun()
    elif not att['clock_out']:
        st.success(f"دخول: {att['clock_in']}")
        if st.button('🔴 تسجيل خروج',use_container_width=True):
            with db() as c: c.execute('UPDATE attendance SET clock_out=? WHERE id=?',(now_iso(),att['id']))
            st.rerun()


def render_riders_v3(user):
    header_v3('الطيارون','التحكم في النشاط والتشغيل وGPS — بلا تفاصيل محاسبية غير لازمة.')
    rs=df('SELECT * FROM riders ORDER BY active_orders,name')
    for _,r in rs.iterrows():
        fresh=gps_fresh(r.to_dict())
        with st.container(border=True):
            a,b,c,d=st.columns([2.2,1.2,1.2,1.4])
            a.markdown(f'**{r["name"]}**<br><span class="small-note">{r["phone"] or "بدون هاتف"}</span>',unsafe_allow_html=True)
            b.markdown(badge_v3('نشط' if r['status']!='غير نشط' else 'غير نشط','green' if r['status']!='غير نشط' else 'red'),unsafe_allow_html=True)
            c.write(f"{int(r['active_orders'])} طلبات")
            d.write('🟢 GPS' if fresh else '🟠 GPS')
            if user['role']=='OWNER':
                x,y=st.columns(2)
                if x.button('تعطيل الطيار' if r['status']!='غير نشط' else 'تفعيل الطيار',key=f'rider_active_v3_{r["id"]}'):
                    try: set_active('rider',r['id'],r['status']=='غير نشط',user); st.rerun()
                    except Exception as ex: st.error(str(ex))
                if y.button('تفاصيل',key=f'rider_detail_v3_{r["id"]}'): st.session_state[f'rd_{r["id"]}']=not st.session_state.get(f'rd_{r["id"]}',False)
                if st.session_state.get(f'rd_{r["id"]}',False): st.write(f"المرتب: {r['salary']:,.2f} ج • آخر GPS: {r['last_gps_at'] or '—'} • الدقة: {r['gps_accuracy'] or '—'} م")
    if user['role']=='OWNER':
        with st.expander('＋ إضافة طيار'):
            with st.form('rider_add_v3'):
                a,b,c=st.columns(3); n=a.text_input('الاسم'); p=b.text_input('الهاتف'); sal=c.number_input('المرتب',min_value=0.0,value=float(get_setting('salary_basic',6000)),step=100.0)
                if st.form_submit_button('إضافة الطيار',use_container_width=True):
                    try: rid=create_rider({'name':n,'phone':p,'salary':sal},user); st.success(f'تمت إضافة الطيار: {rid}'); st.rerun()
                    except Exception as ex: st.error(str(ex))


def render_restaurants_v3(user):
    header_v3('المطاعم والفروع','إدارة النشاط والحساب، واختيار موقع الفرع من الخريطة بالنقر المباشر.')
    rs=all_restaurants()
    for _,r in rs.iterrows():
        bs=branches_for(r['id'],False)
        with st.container(border=True):
            a,b,c=st.columns([2.3,1.2,1.5]); a.markdown(f'**{r["name"]}**<br><span class="small-note">{r["phone"] or ""}</span>',unsafe_allow_html=True); b.markdown(badge_v3('نشط' if r['active'] else 'غير نشط','green' if r['active'] else 'red'),unsafe_allow_html=True); c.write(f"{r['billing_mode']} • {len(bs)} فروع")
            if user['role']=='OWNER':
                x,y=st.columns(2)
                if x.button('تعطيل المطعم' if r['active'] else 'تفعيل المطعم',key=f'rest_act_v3_{r["id"]}'):
                    set_active('restaurant',r['id'],not bool(r['active']),user); st.rerun()
                if y.button('إضافة/إدارة فرع',key=f'branch_toggle_v3_{r["id"]}'): st.session_state[f'br_{r["id"]}']=not st.session_state.get(f'br_{r["id"]}',False)
            if not bs.empty:
                for _,br in bs.iterrows():
                    x,y=st.columns([3.5,1])
                    x.markdown(f'• **{br["name"]}** — {br["address"] or "بدون عنوان"} — {"نشط" if br["active"] else "غير نشط"}',unsafe_allow_html=True)
                    if user['role']=='OWNER' and y.button('تعطيل' if br['active'] else 'تفعيل',key=f'br_act_v3_{br["id"]}'):
                        set_active('branch',br['id'],not bool(br['active']),user); st.rerun()
            if st.session_state.get(f'br_{r["id"]}',False) and user['role']=='OWNER':
                st.markdown('<div class="section-sub">اضغط على موقع الفرع في الخريطة. العنوان والإحداثيات تُلتقطان تلقائياً.</div>',unsafe_allow_html=True)
                if 'branch_point_v3' not in st.session_state: st.session_state.branch_point_v3={}
                p=st.session_state.branch_point_v3; res=mount_map_v3(center=[31.2001,29.9187],zoom=12,clickable=True,key=f'branch_map_v3_{r["id"]}')
                click=getattr(res,'map_click',None) if res else None
                if click:
                    try: st.session_state.branch_point_v3=json.loads(click); st.rerun()
                    except Exception: pass
                p=st.session_state.branch_point_v3
                if p.get('lat') is not None: st.success('موقع الفرع: '+(p.get('address') or f"{p['lat']}, {p['lng']}"))
                with st.form(f'branch_form_v3_{r["id"]}'):
                    n=st.text_input('اسم الفرع'); addr=st.text_input('العنوان',value=p.get('address',''))
                    if st.form_submit_button('حفظ الفرع',use_container_width=True):
                        try: create_branch({'restaurant_id':r['id'],'name':n,'address':addr,'lat':p.get('lat'),'lng':p.get('lng')},user); st.session_state.branch_point_v3={}; st.success('تمت إضافة الفرع.'); st.rerun()
                        except Exception as ex: st.error(str(ex))
    if user['role']=='OWNER':
        with st.expander('＋ إضافة مطعم'):
            with st.form('restaurant_add_v3'):
                a,b=st.columns(2); n=a.text_input('اسم المطعم'); p=b.text_input('الهاتف'); mode=st.selectbox('طريقة التحصيل',['كاش','آجل'])
                if st.form_submit_button('حفظ المطعم',use_container_width=True):
                    try: create_restaurant({'name':n,'phone':p,'billing_mode':mode},user); st.success('تمت إضافة المطعم.'); st.rerun()
                    except Exception as ex: st.error(str(ex))


def render_users_v3(user):
    header_v3('المستخدمون والأمان','الحسابات تُعرض بالحالة والدور. PIN القديم لا يُكشف؛ يمكنك إعادة تعيينه وإظهار الجديد مرة واحدة.')
    us=df('SELECT id,name,email,role,ref_id,active,created_at FROM users ORDER BY name')
    for _,u in us.iterrows():
        with st.container(border=True):
            a,b,c,d=st.columns([2.1,1,1,1.5]); a.markdown(f'**{u["name"]}**<br><span class="small-note">{u["email"]}</span>',unsafe_allow_html=True); b.write(role_label(u['role'])); c.markdown(badge_v3('نشط' if u['active'] else 'غير نشط','green' if u['active'] else 'red'),unsafe_allow_html=True); d.write('PIN: ••••••')
            if user['role']=='OWNER' and u['id']!=user['id']:
                x,y=st.columns(2)
                if x.button('تعطيل الحساب' if u['active'] else 'تفعيل الحساب',key=f'user_act_v3_{u["id"]}'):
                    set_active('user',u['id'],not bool(u['active']),user); st.rerun()
                if y.button('توليد PIN جديد',key=f'user_pin_v3_{u["id"]}'):
                    pin=reset_user_pin(u['id'],user); st.session_state.generated_pin_v3={'name':u['name'],'pin':pin}; st.rerun()
    if st.session_state.get('generated_pin_v3'):
        x=st.session_state.generated_pin_v3; st.success(f"PIN جديد لـ {x['name']}: {x['pin']} — خزّنه الآن. لن نعرض الرقم السابق.")
        if st.button('إخفاء PIN',key='hide_pin_v3'): st.session_state.pop('generated_pin_v3',None); st.rerun()
    if user['role']=='OWNER':
        with st.expander('＋ إنشاء مستخدم'):
            with st.form('user_add_v3'):
                a,b=st.columns(2); n=a.text_input('الاسم'); e=b.text_input('البريد'); c,d=st.columns(2); role=c.selectbox('الدور',['DISPATCHER','ACCOUNTANT','RIDER','RESTAURANT']); pin=d.text_input('PIN أولي',type='password',max_chars=8); ref=None
                if role=='RIDER':
                    rr=df('SELECT id,name FROM riders ORDER BY name')
                    if not rr.empty: rn=st.selectbox('ربط الطيار',rr['name'].tolist()); ref=rr[rr['name']==rn].iloc[0]['id']
                if role=='RESTAURANT':
                    rr=all_restaurants()
                    if not rr.empty: rn=st.selectbox('ربط المطعم',rr['name'].tolist()); ref=rr[rr['name']==rn].iloc[0]['id']
                if st.form_submit_button('إنشاء المستخدم',use_container_width=True):
                    try: create_user({'name':n,'email':e,'role':role,'pin':pin,'ref_id':ref},user); st.success('تم إنشاء المستخدم.'); st.rerun()
                    except Exception as ex: st.error(str(ex))


def render_tools_v3(user):
    header_v3('الأدوات','النسخ الاحتياطي والإعدادات والمراجعة المتقدمة.')
    if user['role']=='OWNER':
        a,b,c=st.columns(3); salary=a.number_input('المرتب الأساسي',value=float(get_setting('salary_basic',6000)),step=100.0); work=b.number_input('أيام العمل',value=float(get_setting('working_days',26)),min_value=1.0); fresh=c.number_input('GPS حديث خلال (ثانية)',value=float(get_setting('gps_fresh_seconds',30)),min_value=5.0)
        if st.button('حفظ إعدادات التشغيل',use_container_width=True): set_setting('salary_basic',salary); set_setting('working_days',work); set_setting('gps_fresh_seconds',fresh); st.success('تم الحفظ.')
    mem=io.BytesIO()
    with zipfile.ZipFile(mem,'w',zipfile.ZIP_DEFLATED) as z:
        for t in SCHEMA: z.writestr(f'{t}.csv',df(f'SELECT * FROM {t}').to_csv(index=False,encoding='utf-8-sig'))
    st.download_button('📦 تنزيل نسخة احتياطية',data=mem.getvalue(),file_name=f'ONWAY_Backup_{today_str()}.zip',mime='application/zip',use_container_width=True)
    if user['role'] in ('OWNER','ACCOUNTANT'):
        with st.expander('سجل التدقيق'): st.dataframe(df("SELECT created_at as 'الوقت',actor_id as 'المستخدم',action as 'العملية',entity as 'الكيان',entity_id as 'المعرف' FROM audit_log ORDER BY id DESC LIMIT 500"),use_container_width=True,hide_index=True)
        with st.expander('دفتر الخزينة'): st.dataframe(df("SELECT created_at as 'الوقت',txn_no as 'الحركة',txn_type as 'النوع',amount as 'المبلغ',direction as 'الاتجاه',reference_id as 'المرجع' FROM ledger ORDER BY id DESC LIMIT 500"),use_container_width=True,hide_index=True)


def render_nav_v3(user):
    st.sidebar.markdown(f'<div class="sidebar-title">🚚 {APP_NAME}</div><div class="sidebar-sub">{user["name"]} • {role_label(user["role"])}</div>',unsafe_allow_html=True)
    role=user['role']
    if role=='OWNER': menu=[('الرئيسية','dashboard'),('الطلبات','orders'),('🗺️ الخريطة الحية','map'),('الطيارون','riders'),('المطاعم والفروع','restaurants'),('الحضور والمرتبات','attendance'),('التسويات','settlements'),('التحليل','analysis'),('المستخدمون','users'),('الأدوات','tools')]
    elif role=='DISPATCHER': menu=[('الرئيسية','dashboard'),('الطلبات','orders'),('🗺️ الخريطة الحية','map'),('الطيارون','riders'),('المطاعم والفروع','restaurants')]
    elif role=='ACCOUNTANT': menu=[('الرئيسية','dashboard'),('الطلبات','orders'),('الطيارون','riders'),('المطاعم والفروع','restaurants'),('الحضور والمرتبات','attendance'),('التسويات','settlements'),('التحليل','analysis'),('الأدوات','tools')]
    elif role=='RIDER': menu=[('مهمتي الآن','rider'),('خريطتي','map')]
    else: menu=[('الرئيسية','dashboard'),('طلبات المطعم','orders')]
    choice=st.sidebar.radio('التنقل', [x[0] for x in menu],index=0)
    st.sidebar.markdown('<div style="height:8px"></div>',unsafe_allow_html=True)
    if st.sidebar.button('تسجيل الخروج',use_container_width=True): st.session_state.pop('user',None); st.rerun()
    return dict(menu)[choice]


# =========================================================
# التشغيل النهائي — ONWAY V3
# =========================================================
if "user" not in st.session_state:
    login()
    st.stop()

user=st.session_state.user
page=render_nav_v3(user)
try:
    if page=="dashboard": render_dashboard_v3(user)
    elif page=="orders": render_orders_v3(user)
    elif page=="map": render_live_map_v3(user)
    elif page=="rider": render_rider_v3(user)
    elif page=="riders": render_riders_v3(user)
    elif page=="restaurants": render_restaurants_v3(user)
    elif page=="attendance": render_attendance(user)
    elif page=="settlements": render_settlements(user)
    elif page=="users": render_users_v3(user)
    elif page=="tools": render_tools_v3(user)
    elif page=="analysis": render_analysis(user)
except Exception as ex:
    st.error("حدث خطأ داخل النظام وتم منع توقف الواجهة.")
    if user.get("role")=="OWNER": st.exception(ex)
