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
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
:root{--onway:#d62828;--onway-dark:#8f1717;--ink:#17202a;--muted:#6b7280;--soft:#f6f7f9;--green:#1f9d55;--amber:#c98400;--blue:#2563eb}
html,body,[class*="css"]{font-family:'Cairo',sans-serif!important}
[data-testid="stAppViewContainer"]{background:#f5f7fa}
[data-testid="stHeader"]{background:rgba(255,255,255,.86)}
.block-container{padding-top:1rem;padding-bottom:5rem;max-width:1450px}
.onway-hero{background:linear-gradient(135deg,#111827 0%,#1f2937 60%,#7f1d1d 100%);color:#fff;border-radius:22px;padding:1.4rem 1.6rem;margin-bottom:1rem;box-shadow:0 12px 28px rgba(0,0,0,.10)}
.onway-hero h1{margin:0;font-size:2rem;font-weight:800}.onway-hero p{margin:.3rem 0 0;color:#d1d5db}
.card{background:#fff;border:1px solid #e5e7eb;border-radius:18px;padding:1rem 1.1rem;box-shadow:0 6px 18px rgba(17,24,39,.05)}
.metric{background:#fff;border:1px solid #e5e7eb;border-radius:18px;padding:1rem}.metric .v{font-size:1.7rem;font-weight:800}.metric .l{color:#6b7280;font-size:.88rem}
.status-pill{display:inline-block;padding:.18rem .55rem;border-radius:999px;font-size:.75rem;font-weight:700}
.status-new{background:#fff7ed;color:#c2410c}.status-active{background:#eff6ff;color:#1d4ed8}.status-done{background:#ecfdf5;color:#047857}.status-cancel{background:#fef2f2;color:#b91c1c}.status-warn{background:#fffbeb;color:#a16207}
.small{font-size:.8rem;color:#6b7280}.danger{color:#b91c1c}.ok{color:#047857}.warn{color:#a16207}
.stButton>button{border-radius:12px;font-weight:800;min-height:44px}.stTextInput input,.stNumberInput input,.stSelectbox div[data-baseweb="select"]>div,.stDateInput input{border-radius:12px!important}
[data-testid="stSidebar"]{background:#111827}.sidebar-title{color:#fff;font-size:1.35rem;font-weight:800;text-align:center;margin-bottom:1rem}.sidebar-sub{color:#cbd5e1;font-size:.78rem;text-align:center;margin-bottom:1rem}
.table-wrap{overflow-x:auto;border-radius:14px;border:1px solid #e5e7eb}
.mobile-note{display:none}
@media(max-width:760px){.block-container{padding:.7rem .7rem 4.5rem}.onway-hero{padding:1rem}.onway-hero h1{font-size:1.5rem}.mobile-note{display:block;background:#fff7ed;border:1px solid #fed7aa;padding:.7rem;border-radius:12px;font-size:.78rem;color:#9a3412;margin-bottom:.7rem}}
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
# واجهة إدارة العملية
# =========================================================
def header(title, subtitle=""):
    st.markdown(f'<div class="onway-hero"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def show_metrics(items):
    cols = st.columns(len(items))
    for col, (label, value) in zip(cols, items):
        with col:
            st.markdown(f'<div class="metric"><div class="v">{value}</div><div class="l">{label}</div></div>', unsafe_allow_html=True)


def render_dashboard(user):
    header("لوحة القيادة", "صورة تشغيلية سريعة للقرار، بدون تفاصيل زائدة.")
    if user["role"] == "RESTAURANT" and user.get("ref_id"):
        d_orders = df("SELECT * FROM orders WHERE restaurant_id=?", (user["ref_id"],))
        total=len(d_orders); cash=int((d_orders["billing_mode"]=="كاش").sum()) if not d_orders.empty else 0; credit=int((d_orders["billing_mode"]=="آجل").sum()) if not d_orders.empty else 0
        completed=int((d_orders["status"]=="تم التسليم").sum()) if not d_orders.empty else 0
        commission=float(d_orders["rider_commission"].sum()) if not d_orders.empty else 0
        due=float(d_orders.loc[d_orders["billing_mode"]=="آجل","delivery_fee"].sum()) if not d_orders.empty else 0
        st.write("")
        show_metrics([("إجمالي الطلبات",total),("كاش / آجل",f"{cash} / {credit}"),("تم التسليم",completed),("خدمات التوصيل الآجلة",f"{due:,.2f} ج"),("عمولات التشغيل",f"{commission:,.2f} ج")])
        st.subheader("آخر طلبات المطعم")
        st.dataframe(d_orders[["order_no","status","billing_mode","delivery_address","delivery_fee","created_at"]].sort_values("created_at",ascending=False).head(80),use_container_width=True,hide_index=True)
        return
    d = dashboard_data()
    show_metrics([
        ("طلبات اليوم", d["total"]),
        ("كاش / آجل", f'{d["cash_orders"]} / {d["credit_orders"]}'),
        ("تم التسليم", d["completed"]),
        ("عمولات الطيارين", f'{d["commission"]:,.2f} ج'),
        ("مديونية المطاعم", f'{d["restaurant_due"]:,.2f} ج'),
        ("الخزينة", f'{d["treasury"]:,.2f} ج'),
    ])
    st.write("")
    if d["gps_stale"]:
        st.warning(f'هناك {d["gps_stale"]} طيارين آخر تحديث GPS لهم قديم.')
    st.subheader("حركة الطلبات اليوم")
    o = df("""SELECT order_no as 'الطلب', status as 'الحالة', billing_mode as 'التحصيل', delivery_fee as 'الخدمة',
              rider_commission as 'العمولة', created_at as 'الوقت' FROM orders WHERE substr(created_at,1,10)=? ORDER BY created_at DESC LIMIT 80""", (today_str(),))
    if o.empty: st.info("لا توجد طلبات اليوم.")
    else: st.dataframe(o, use_container_width=True, hide_index=True)


def render_orders(user):
    header("الطلبات", "ابحث، أنشئ، عيّن، تابع، وعدّل الطلب من شاشة واحدة.")
    q1,q2,q3 = st.columns(3)
    search = q1.text_input("بحث برقم الطلب / العنوان")
    status_filter = q2.selectbox("الحالة", ["الكل","جديد","تم التعيين","تم القبول","تم الاستلام","في الطريق","تم التسليم","ملغى"])
    billing_filter = q3.selectbox("التحصيل", ["الكل","كاش","آجل"])
    query = "SELECT * FROM orders WHERE 1=1"
    params = []
    if user["role"] == "RESTAURANT" and user.get("ref_id"):
        query += " AND restaurant_id=?"; params.append(user["ref_id"])
    if search:
        query += " AND (order_no LIKE ? OR delivery_address LIKE ?)"; params += [f"%{search}%",f"%{search}%"]
    if status_filter != "الكل": query += " AND status=?"; params.append(status_filter)
    if billing_filter != "الكل": query += " AND billing_mode=?"; params.append(billing_filter)
    query += " ORDER BY created_at DESC LIMIT 300"
    orders = df(query, tuple(params))
    st.dataframe(orders[["order_no","status","billing_mode","delivery_address","distance_km","delivery_fee","rider_commission","created_at"]] if not orders.empty else orders,
                 use_container_width=True, hide_index=True)

    if user["role"] in ("OWNER","DISPATCHER","ACCOUNTANT"):
        with st.expander("＋ إنشاء طلب جديد", expanded=False):
            restaurants = get_restaurants()
            if restaurants.empty:
                st.warning("أضف مطعماً أولاً من شاشة المطاعم.")
            else:
                rmap = dict(zip(restaurants["name"], restaurants["id"]))
                restaurant_name = st.selectbox("المطعم", list(rmap))
                rid = rmap[restaurant_name]
                branches = get_branches(rid)
                if branches.empty:
                    st.warning("أضف فرعاً للمطعم أولاً.")
                else:
                    bmap = dict(zip(branches["name"], branches["id"]))
                    branch_name = st.selectbox("الفرع", list(bmap))
                    br = branches[branches["id"]==bmap[branch_name]].iloc[0].to_dict()
                    riders = ranked_riders(float(br["lat"] or 31.2001), float(br["lng"] or 29.9187))
                    rider_options = {"تعيين لاحقاً": None}
                    if not riders.empty: rider_options.update(dict(zip(riders["name"], riders["id"])))
                    if not riders.empty:
                        suggested=riders.iloc[0]
                        st.info(f"🤖 اقتراح التعيين الذكي: {suggested['name']} — طلبات نشطة {int(suggested['active_orders'])}")
                    with st.form("new_order"):
                        a,b = st.columns(2)
                        order_no = a.text_input("رقم الطلب")
                        delivery_address = b.text_input("عنوان التسليم")
                        c,d,e = st.columns(3)
                        distance = c.number_input("المسافة (كم)", min_value=0.0, step=0.1, value=3.0)
                        eta = d.number_input("الوقت المتوقع (دقيقة)", min_value=0, step=1, value=20)
                        billing = e.selectbox("نظام التحصيل", ["كاش","آجل"])
                        f,g = st.columns(2)
                        fee = f.number_input("قيمة خدمة التوصيل", min_value=0.0, step=1.0, value=30.0)
                        rider_name = g.selectbox("الطيار", list(rider_options.keys()))
                        h,i = st.columns(2)
                        lat = h.number_input("خط عرض العميل (اختياري)", value=float(br["lat"] or 31.2001), format="%.6f")
                        lng = i.number_input("خط طول العميل (اختياري)", value=float(br["lng"] or 29.9187), format="%.6f")
                        reward = st.number_input("مكافأة", min_value=0.0, step=1.0, value=0.0)
                        discount = st.number_input("خصم", min_value=0.0, step=1.0, value=0.0)
                        notes = st.text_area("ملاحظات")
                        submit = st.form_submit_button("حفظ وإطلاق الطلب", use_container_width=True)
                        if submit:
                            if billing == "كاش" and fee <= 0: st.error("خدمة التوصيل للكاش يجب أن تكون أكبر من صفر.")
                            elif not order_no or not delivery_address: st.error("رقم الطلب والعنوان مطلوبان.")
                            else:
                                try:
                                    oid = create_order({"order_no":order_no,"restaurant_id":rid,"branch_id":bmap[branch_name],"delivery_address":delivery_address,
                                                       "delivery_lat":lat,"delivery_lng":lng,"distance_km":distance,"eta_minutes":eta,"billing_mode":billing,
                                                       "rider_id":rider_options[rider_name],"delivery_fee":fee,"reward":reward,"discount":discount,"notes":notes},user)
                                    st.success(f"تم إنشاء الطلب {order_no} — العمولة {commission_for_distance(distance):,.2f} ج")
                                    st.rerun()
                                except Exception as ex: st.error(str(ex))

    if not orders.empty:
        st.divider(); st.subheader("إدارة الطلب المحدد")
        selected_no = st.selectbox("اختيار الطلب", orders["order_no"].tolist())
        order = one("SELECT * FROM orders WHERE order_no=?", (selected_no,))
        if order:
            c1,c2,c3,c4 = st.columns(4)
            c1.write(f"**الحالة:** {order['status']}")
            c2.write(f"**الخدمة:** {order['delivery_fee']:,.2f} ج")
            c3.write(f"**العمولة:** {order['rider_commission']:,.2f} ج")
            c4.write(f"**التحصيل:** {order['billing_mode']}")
            if user["role"] in ("OWNER","DISPATCHER"):
                with st.form("edit_order_details"):
                    ed_address=st.text_input("عنوان التسليم", value=order["delivery_address"] or "")
                    ed_distance=st.number_input("المسافة (كم)", min_value=0.0, value=float(order["distance_km"] or 0), step=0.1)
                    ed_fee=st.number_input("خدمة التوصيل", min_value=0.0, value=float(order["delivery_fee"] or 0), step=1.0)
                    ed_notes=st.text_area("الملاحظات", value=order["notes"] or "")
                    if st.form_submit_button("حفظ تعديل الطلب", use_container_width=True):
                        before=dict(order)
                        new_comm=commission_for_distance(ed_distance)
                        with conn() as c:
                            c.execute("UPDATE orders SET delivery_address=?,distance_km=?,delivery_fee=?,rider_commission=?,notes=? WHERE id=?",(ed_address,ed_distance,ed_fee,new_comm,ed_notes,order["id"]))
                            after=dict(c.execute("SELECT * FROM orders WHERE id=?",(order["id"],)).fetchone())
                        audit(user["id"],"update","order",order["id"],before=before,after=after)
                        st.success("تم تعديل الطلب وتحديث العمولة."); st.rerun()
                riders = df("SELECT id,name,status,active_orders FROM riders WHERE status!='غير نشط' ORDER BY active_orders,name")
                rmap = {"بدون طيار":None}
                if not riders.empty: rmap.update(dict(zip(riders["name"], riders["id"])))
                current_name = "بدون طيار"
                if order["rider_id"]:
                    rn = one("SELECT name FROM riders WHERE id=?", (order["rider_id"],)); current_name = rn["name"] if rn else "بدون طيار"
                sel = st.selectbox("الطيار", list(rmap), index=list(rmap).index(current_name) if current_name in rmap else 0)
                if st.button("حفظ تعيين الطيار", use_container_width=True):
                    try: assign_rider(order["id"],rmap[sel],user); st.success("تم تحديث التعيين."); st.rerun()
                    except Exception as ex: st.error(str(ex))
            allowed = transitions(order["status"])
            if allowed:
                ns = st.selectbox("الحالة التالية", allowed)
                if st.button("تأكيد تغيير الحالة", use_container_width=True):
                    try: change_order_status(order["id"],ns,user); st.success("تم تحديث الحالة."); st.rerun()
                    except Exception as ex: st.error(str(ex))
            if order["delivery_lat"] and order["delivery_lng"]:
                st.link_button("🧭 فتح الملاحة للعنوان", f"https://www.google.com/maps/dir/?api=1&destination={order['delivery_lat']},{order['delivery_lng']}")


def render_map(user):
    header("الخريطة الحية", "كل طيار يظهر بحالته وآخر GPS معروف، والطلبات تظهر حسب موقعها المسجل.")
    @st.fragment(run_every="5s")
    def live_block():
        riders = df("SELECT name,last_lat,last_lng,gps_accuracy,last_gps_at,status,active_orders FROM riders WHERE last_lat IS NOT NULL AND last_lng IS NOT NULL")
        orders = df("SELECT order_no,delivery_address,delivery_lat,delivery_lng,status,rider_id FROM orders WHERE status IN ('جديد','تم التعيين','تم القبول','تم الاستلام','في الطريق') AND delivery_lat IS NOT NULL AND delivery_lng IS NOT NULL")
        points = []
        if not riders.empty:
            for _,r in riders.iterrows(): points.append({"lat":r["last_lat"],"lon":r["last_lng"]})
        if not orders.empty:
            for _,r in orders.iterrows(): points.append({"lat":r["delivery_lat"],"lon":r["delivery_lng"]})
        if points:
            st.map(pd.DataFrame(points), latitude="lat", longitude="lon", zoom=12, height=520)
        else:
            st.info("لا توجد نقاط GPS أو طلبات بإحداثيات حتى الآن. على الطيار فتح شاشة التتبع والسماح بالموقع.")
        if not riders.empty:
            view = riders.rename(columns={"name":"الطيار","status":"الحالة","active_orders":"طلبات نشطة","gps_accuracy":"دقة GPS","last_gps_at":"آخر تحديث"})
            st.dataframe(view[["الطيار","الحالة","طلبات نشطة","دقة GPS","آخر تحديث"]], use_container_width=True, hide_index=True)
    live_block()


def render_rider(user):
    rider = one("SELECT * FROM riders WHERE id=?", (user["ref_id"],))
    if not rider:
        st.error("حساب الطيار غير مرتبط بطيار صالح."); return
    header(f"واجهة الطيار — {rider['name']}", "كل ما يخص الطيار في شاشة واحدة.")
    capture_gps(rider["id"])
    today_att = one("SELECT * FROM attendance WHERE rider_id=? AND work_date=?", (rider["id"],today_str()))
    c1,c2,c3 = st.columns(3)
    c1.metric("الحالة", rider["status"])
    c2.metric("طلبات نشطة", rider["active_orders"])
    c3.metric("عمولة النظام", f'{float(one("SELECT COALESCE(SUM(rider_commission),0) x FROM orders WHERE rider_id=? AND status=\'تم التسليم\' AND substr(delivered_at,1,10)=?",(rider["id"],today_str()))["x"]):,.2f} ج')
    st.subheader("الحضور")
    a,b = st.columns(2)
    if not today_att or not today_att["clock_in"]:
        if a.button("🟢 تسجيل دخول", use_container_width=True):
            aid=uid("ATT")
            with conn() as c: c.execute("INSERT INTO attendance(id,rider_id,work_date,clock_in,status,created_at) VALUES (?,?,?,?,?,?)",(aid,rider["id"],today_str(),now_iso(),"حاضر",now_iso()))
            st.rerun()
    else:
        a.success(f"دخل: {today_att['clock_in']}")
        if not today_att["clock_out"] and b.button("🔴 تسجيل خروج", use_container_width=True):
            with conn() as c: c.execute("UPDATE attendance SET clock_out=? WHERE id=?",(now_iso(),today_att["id"]))
            st.rerun()
        elif today_att["clock_out"]: b.info(f"خرج: {today_att['clock_out']}")
    st.subheader("طلباتي")
    my = df("SELECT order_no,status,delivery_address,distance_km,delivery_fee,rider_commission,created_at FROM orders WHERE rider_id=? AND status NOT IN ('تم التسليم','ملغى') ORDER BY created_at DESC",(rider["id"],))
    if my.empty: st.info("لا توجد طلبات حالياً.")
    else:
        st.dataframe(my,use_container_width=True,hide_index=True)
        selected = st.selectbox("الطلب الحالي", my["order_no"].tolist())
        o=one("SELECT * FROM orders WHERE order_no=?",(selected,))
        allowed = transitions(o["status"])
        if allowed:
            ns=st.selectbox("الإجراء التالي",allowed)
            if st.button("تأكيد الإجراء",use_container_width=True):
                try: change_order_status(o["id"],ns,user); st.success("تمت العملية."); st.rerun()
                except Exception as ex: st.error(str(ex))
        st.link_button("🧭 فتح الملاحة",f"https://www.google.com/maps/dir/?api=1&destination={o['delivery_lat']},{o['delivery_lng']}")
    st.subheader("تيكيت التشغيل")
    if not my.empty:
        o=one("SELECT o.*,r.name restaurant,b.name branch FROM orders o JOIN restaurants r ON r.id=o.restaurant_id JOIN branches b ON b.id=o.branch_id WHERE o.order_no=?",(my.iloc[0]["order_no"],))
        ticket=f"🚚 ONWAY\nالطلب: {o['order_no']}\nالاستلام: {o['restaurant']} — {o['branch']}\nالتسليم: {o['delivery_address']}\nالمسافة: {o['distance_km']} كم\nالتحصيل: {o['billing_mode']}\nالعمولة: {o['rider_commission']:.2f} ج\nالحالة: {o['status']}"
        st.code(ticket,language="text")


def render_riders(user):
    header("الطيارون", "إدارة حالة الأسطول، الحضور، الرصيد التشغيلي، وجودة GPS.")
    riders = df("SELECT id,name,phone,salary,status,active_orders,last_gps_at FROM riders ORDER BY name")
    st.dataframe(riders.rename(columns={"name":"الطيار","phone":"الهاتف","salary":"المرتب","status":"الحالة","active_orders":"طلبات نشطة","last_gps_at":"آخر GPS"}),use_container_width=True,hide_index=True)
    if user["role"] == "OWNER":
        with st.expander("＋ إضافة طيار"):
            with st.form("new_rider"):
                n=st.text_input("الاسم"); p=st.text_input("الهاتف"); sal=st.number_input("المرتب",value=float(get_setting("salary_basic",6000)))
                if st.form_submit_button("حفظ",use_container_width=True):
                    rid=uid("RYD")
                    with conn() as c: c.execute("INSERT INTO riders(id,name,phone,salary,status,created_at) VALUES (?,?,?,?,?,?)",(rid,n,p,sal,"متاح",now_iso()))
                    audit(user["id"],"create","rider",rid,after={"name":n}); st.rerun()


def render_restaurants(user):
    header("المطاعم والفروع", "كل فرع مستقل محاسبياً وتشغيلياً مع نظام كاش/آجل واضح.")
    rs=get_restaurants(False)
    st.dataframe(rs.rename(columns={"name":"المطعم","phone":"الهاتف","billing_mode":"النظام","active":"نشط"})[["المطعم","الهاتف","النظام","نشط"]],use_container_width=True,hide_index=True)
    if user["role"] == "OWNER":
        with st.expander("＋ إضافة مطعم"):
            with st.form("new_restaurant"):
                n=st.text_input("اسم المطعم"); p=st.text_input("الهاتف"); mode=st.selectbox("التحصيل",["كاش","آجل"])
                if st.form_submit_button("حفظ المطعم",use_container_width=True):
                    rid=uid("RST")
                    with conn() as c: c.execute("INSERT INTO restaurants(id,name,phone,billing_mode,created_at) VALUES (?,?,?,?,?)",(rid,n,p,mode,now_iso()))
                    audit(user["id"],"create","restaurant",rid,after={"name":n,"billing_mode":mode}); st.rerun()
        if not rs.empty:
            rname=st.selectbox("اختيار مطعم لإضافة فرع",rs["name"].tolist())
            rid=rs[rs["name"]==rname].iloc[0]["id"]
            with st.form("new_branch"):
                n=st.text_input("اسم الفرع"); addr=st.text_input("العنوان"); lat=st.number_input("خط العرض",value=31.2001,format="%.6f"); lng=st.number_input("خط الطول",value=29.9187,format="%.6f")
                if st.form_submit_button("إضافة الفرع",use_container_width=True):
                    bid=uid("BRN")
                    with conn() as c: c.execute("INSERT INTO branches(id,restaurant_id,name,address,lat,lng,created_at) VALUES (?,?,?,?,?,?,?)",(bid,rid,n,addr,lat,lng,now_iso()))
                    audit(user["id"],"create","branch",bid,after={"name":n,"restaurant_id":rid}); st.rerun()


def render_attendance(user):
    header("الحضور والانصراف والمرتبات", "المرتب الأساسي 6000 ج، وإجازة بعذر = يوم، وبدون عذر = 1.25 يوم.")
    riders=df("SELECT id,name,salary FROM riders ORDER BY name")
    if riders.empty: st.info("أضف طيارين أولاً."); return
    selected=st.selectbox("الطيار",riders["name"].tolist())
    rid=riders[riders["name"]==selected].iloc[0]["id"]
    month=st.date_input("بداية الشهر",date.today().replace(day=1))
    month_start=date(month.year,month.month,1); month_end=(month_start.replace(day=28)+timedelta(days=4)).replace(day=1)-timedelta(days=1)
    att=df("SELECT work_date,clock_in,clock_out,status,reason FROM attendance WHERE rider_id=? AND work_date BETWEEN ? AND ? ORDER BY work_date",(rid,month_start.isoformat(),month_end.isoformat()))
    absent_exc=int((att["status"]=="إجازة بعذر").sum()) if not att.empty else 0
    absent_unexc=int((att["status"]=="إجازة بدون عذر").sum()) if not att.empty else 0
    base=float(riders[riders["id"]==rid].iloc[0]["salary"])
    daily=base/float(get_setting("working_days",26))
    deduction=daily*(absent_exc*float(get_setting("excused_leave_days",1))+absent_unexc*float(get_setting("unexcused_leave_days",1.25)))
    net=max(0,base-deduction)
    show_metrics([("أيام بعذر",absent_exc),("بدون عذر",absent_unexc),("قيمة اليوم",f"{daily:,.2f} ج"),("الخصم",f"{deduction:,.2f} ج"),("صافي المرتب",f"{net:,.2f} ج")])
    if not att.empty: st.dataframe(att,use_container_width=True,hide_index=True)
    if user["role"] in ("OWNER","ACCOUNTANT"):
        with st.form("attendance_manual"):
            d=st.date_input("اليوم",date.today()); status=st.selectbox("الحالة",["حاضر","إجازة بعذر","إجازة بدون عذر","غياب"]); reason=st.text_input("السبب")
            if st.form_submit_button("حفظ الحالة",use_container_width=True):
                aid=uid("ATT")
                with conn() as c:
                    c.execute("INSERT INTO attendance(id,rider_id,work_date,status,reason,created_at) VALUES (?,?,?,?,?,?) ON CONFLICT(rider_id,work_date) DO UPDATE SET status=excluded.status,reason=excluded.reason",(aid,rid,d.isoformat(),status,reason,now_iso()))
                audit(user["id"],"upsert","attendance",aid,after={"rider_id":rid,"date":d.isoformat(),"status":status}); st.rerun()


def render_settlements(user):
    header("التسويات والحسابات", "كل حركة مالية مرتبطة بطلب ومرجع، مع منع إعادة التسوية لنفس الطلب.")
    tab1,tab2=st.tabs(["تصفية طيار","تصفية مطعم آجل"])
    with tab1:
        riders=df("SELECT id,name FROM riders WHERE status!='غير نشط' ORDER BY name")
        if not riders.empty:
            rn=st.selectbox("الطيار",riders["name"].tolist(),key="rs1"); rid=riders[riders["name"]==rn].iloc[0]["id"]
            start=st.date_input("من",date.today(),key="sd1"); end=st.date_input("إلى",date.today(),key="ed1")
            o=df("SELECT * FROM orders WHERE rider_id=? AND billing_mode='كاش' AND status='تم التسليم' AND substr(delivered_at,1,10) BETWEEN ? AND ? ORDER BY delivered_at",(rid,start.isoformat(),end.isoformat()))
            if o.empty: st.info("لا توجد طلبات كاش غير مسواة في الفترة.")
            else:
                already=df("SELECT si.order_id FROM settlement_items si JOIN settlements s ON s.id=si.settlement_id WHERE s.kind='طيار'",)
                done=set(already["order_id"].tolist()) if not already.empty else set()
                o=o[~o["id"].isin(done)]
                cash=float(o["cash_collected"].sum()); comm=float(o["rider_commission"].sum()); rew=float(o["reward"].sum()); disc=float(o["discount"].sum())
                due=cash-(comm+rew)+disc
                show_metrics([("الكاش المحصل",f"{cash:,.2f} ج"),("العمولات",f"{comm:,.2f} ج"),("المكافآت",f"{rew:,.2f} ج"),("الخصومات",f"{disc:,.2f} ج"),("المستحق للتوريد",f"{due:,.2f} ج")])
                st.dataframe(o[["order_no","cash_collected","rider_commission","reward","discount"]],use_container_width=True,hide_index=True)
                paid=st.number_input("المبلغ الذي تم توريده الآن",min_value=0.0,value=max(0.0,due),step=1.0,key="paid_rider")
                if st.button("إغلاق التصفية وتسجيل التوريد",use_container_width=True):
                    sid=uid("SET"); stamp=now_iso()
                    with conn() as c:
                        c.execute("INSERT INTO settlements(id,kind,party_id,period_start,period_end,gross,commissions,rewards,discounts,cash_due,paid,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",(sid,"طيار",rid,start.isoformat(),end.isoformat(),cash,comm,rew,disc,due,paid,user["id"],stamp))
                        for oid,amt in zip(o["id"],o["cash_collected"]): c.execute("INSERT INTO settlement_items(id,settlement_id,order_id,amount) VALUES (?,?,?,?)",(uid("ITM"),sid,oid,float(amt)))
                        if paid>0: c.execute("INSERT INTO ledger(txn_no,txn_type,account_type,account_id,amount,direction,reference_id,description,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",(uid("TXN"),"توريد طيار","خزينة",None,paid,"داخل",sid,f"توريد الطيار {rn}",user["id"],stamp))
                    audit(user["id"],"settle","rider",rid,after={"settlement":sid,"paid":paid}); st.success("تمت التصفية."); st.rerun()
    with tab2:
        rs=get_restaurants()
        credit=rs[rs["billing_mode"]=="آجل"] if not rs.empty else rs
        if credit.empty: st.info("لا توجد مطاعم آجلة.")
        else:
            rn=st.selectbox("المطعم",credit["name"].tolist(),key="cr1"); rid=credit[credit["name"]==rn].iloc[0]["id"]
            end=date.today(); start=end-timedelta(days=6)
            due=float(df("SELECT COALESCE(SUM(delivery_fee),0) x FROM orders WHERE restaurant_id=? AND billing_mode='آجل' AND status='تم التسليم' AND substr(delivered_at,1,10) BETWEEN ? AND ?",(rid,start.isoformat(),end.isoformat()))["x"][0])
            paid=float(df("SELECT COALESCE(SUM(paid),0) x FROM settlements WHERE kind='مطعم' AND party_id=?",(rid,))["x"][0])
            outstanding=max(0,due-paid)
            show_metrics([("خدمات الفترة",f"{due:,.2f} ج"),("المدفوع سابقاً",f"{paid:,.2f} ج"),("المستحق",f"{outstanding:,.2f} ج")])
            p=st.number_input("مبلغ التحصيل",min_value=0.0,value=outstanding,step=1.0,key="restpaid")
            if st.button("تسجيل تحصيل المطعم",use_container_width=True):
                sid=uid("SET")
                with conn() as c:
                    c.execute("INSERT INTO settlements(id,kind,party_id,period_start,period_end,gross,paid,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?)",(sid,"مطعم",rid,start.isoformat(),end.isoformat(),due,p,user["id"],now_iso()))
                    if p>0: c.execute("INSERT INTO ledger(txn_no,txn_type,account_type,account_id,amount,direction,reference_id,description,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",(uid("TXN"),"تحصيل مطعم آجل","خزينة",None,p,"داخل",sid,f"تحصيل {rn}",user["id"],now_iso()))
                audit(user["id"],"settle","restaurant",rid,after={"settlement":sid,"paid":p}); st.success("تم التسجيل."); st.rerun()


def render_users(user):
    header("المستخدمون والصلاحيات", "كل مستخدم يرى ما يخص اختصاصه، مع تسجيل الدخول والتعديلات في سجل التدقيق.")
    us=df("SELECT id,name,email,role,ref_id,active,created_at FROM users ORDER BY name")
    st.dataframe(us,use_container_width=True,hide_index=True)
    if user["role"]=="OWNER":
        with st.expander("＋ إضافة مستخدم"):
            riders=df("SELECT id,name FROM riders ORDER BY name")
            roles=["DISPATCHER","ACCOUNTANT","RIDER"] + (["RESTAURANT"] if not get_restaurants().empty else [])
            with st.form("new_user"):
                n=st.text_input("الاسم"); e=st.text_input("البريد").strip().lower(); role=st.selectbox("الدور",roles); pin=st.text_input("PIN",type="password")
                ref=None
                if role=="RIDER" and not riders.empty:
                    rn=st.selectbox("الطيار",riders["name"].tolist()); ref=riders[riders["name"]==rn].iloc[0]["id"]
                if role=="RESTAURANT":
                    rs=get_restaurants(); rn=st.selectbox("المطعم",rs["name"].tolist()); ref=rs[rs["name"]==rn].iloc[0]["id"]
                if st.form_submit_button("إنشاء المستخدم",use_container_width=True):
                    if not n or "@" not in e or len(pin)<4: st.error("راجع البيانات.")
                    else:
                        try:
                            uidv=uid("USR")
                            with conn() as c: c.execute("INSERT INTO users(id,name,email,role,ref_id,pin_hash,active,created_at) VALUES (?,?,?,?,?,?,1,?)",(uidv,n,e,role,ref,hash_pin(pin),now_iso()))
                            audit(user["id"],"create","user",uidv,after={"name":n,"email":e,"role":role,"ref_id":ref}); st.success("تم إنشاء المستخدم."); st.rerun()
                        except sqlite3.IntegrityError: st.error("البريد مستخدم بالفعل.")


def export_all():
    tables=list(SCHEMA.keys())
    mem=io.BytesIO()
    with zipfile.ZipFile(mem,"w",zipfile.ZIP_DEFLATED) as z:
        for t in tables:
            d=df(f"SELECT * FROM {t}")
            z.writestr(f"{t}.csv", d.to_csv(index=False,encoding="utf-8-sig"))
    return mem.getvalue()


def render_tools(user):
    header("أدوات النظام", "نسخ احتياطي، بيانات مرجعية، إعدادات أساسية، وفحص الصحة.")
    if user["role"]=="OWNER":
        st.subheader("إعدادات الحساب")
        a,b,c=st.columns(3)
        salary=a.number_input("المرتب الأساسي",value=float(get_setting("salary_basic",6000)))
        working=b.number_input("أيام العمل الشهرية",value=float(get_setting("working_days",26)),min_value=1.0)
        gps=a if False else c
        fresh=gps.number_input("اعتبار GPS جديداً خلال (ثانية)",value=float(get_setting("gps_fresh_seconds",30)),min_value=5.0)
        if st.button("حفظ الإعدادات",use_container_width=True):
            set_setting("salary_basic",salary); set_setting("working_days",working); set_setting("gps_fresh_seconds",fresh); st.success("تم حفظ الإعدادات.")
    st.subheader("النسخ الاحتياطي")
    st.download_button("📦 تنزيل كل بيانات النظام",data=export_all(),file_name=f"ONWAY_Backup_{today_str()}.zip",mime="application/zip",use_container_width=True)
    st.caption("النسخة تحتوي كل الجداول بصيغة CSV UTF-8 وتصلح للحفظ والمراجعة أو إعادة البناء.")
    if user["role"] in ("OWNER","ACCOUNTANT"):
        with st.expander("سجل التدقيق المالي والتشغيلي"):
            al=df("SELECT created_at as 'الوقت',actor_id as 'المستخدم',action as 'العملية',entity as 'الكيان',entity_id as 'المعرف' FROM audit_log ORDER BY id DESC LIMIT 200")
            st.dataframe(al,use_container_width=True,hide_index=True)
        with st.expander("دفتر الخزينة"):
            lg=df("SELECT created_at as 'الوقت',txn_no as 'الحركة',txn_type as 'النوع',amount as 'المبلغ',direction as 'الاتجاه',reference_id as 'المرجع' FROM ledger ORDER BY id DESC LIMIT 200")
            st.dataframe(lg,use_container_width=True,hide_index=True)
    st.subheader("فحص الصحة")
    checks=[]
    with conn() as c:
        for t in SCHEMA: 
            try: c.execute(f"SELECT 1 FROM {t} LIMIT 1"); checks.append((t,"OK"))
            except Exception as ex: checks.append((t,f"FAIL {ex}"))
    st.dataframe(pd.DataFrame(checks,columns=["الجدول","الحالة"]),use_container_width=True,hide_index=True)
    st.success("Health Check مكتمل.")


def render_analysis(user):
    header("التحليل والأداء", "المؤشرات المشتقة لمراجعة الإنتاجية، التغطية، والماليات.")
    orders=df("SELECT * FROM orders")
    if orders.empty: st.info("لا توجد بيانات كافية للتحليل بعد."); return
    orders["day"]=orders["created_at"].str[:10]
    daily=orders.groupby("day").agg(طلبات=("id","count"),خدمة=("delivery_fee","sum"),عمولات=("rider_commission","sum")).reset_index()
    completed=orders.dropna(subset=["delivered_at"]).copy()
    avg_minutes=0
    on_time=0
    if not completed.empty:
        vals=[]
        for _,r in completed.iterrows():
            try: vals.append((datetime.strptime(r["delivered_at"],"%Y-%m-%d %H:%M:%S")-datetime.strptime(r["created_at"],"%Y-%m-%d %H:%M:%S")).total_seconds()/60)
            except: pass
        if vals: avg_minutes=sum(vals)/len(vals)
    show_metrics([("متوسط زمن الطلب",f"{avg_minutes:,.1f} دقيقة"),("نسبة التسليم",f"{(len(completed)/len(orders)*100):,.1f}%"),("متوسط العمولة",f"{orders['rider_commission'].mean():,.2f} ج")])
    st.subheader("الطلبات والخدمة اليومية")
    st.line_chart(daily.set_index("day")[["طلبات","خدمة","عمولات"]])
    c1,c2=st.columns(2)
    with c1:
        top=orders.groupby("rider_id").size().reset_index(name="طلبات").sort_values("طلبات",ascending=False).head(10)
        if not top.empty:
            names={x["id"]:x["name"] for x in df("SELECT id,name FROM riders").to_dict("records")}
            top["الطيار"]=top["rider_id"].map(names).fillna("غير معين")
            st.dataframe(top[["الطيار","طلبات"]],use_container_width=True,hide_index=True)
    with c2:
        by_status=orders.groupby("status").size().reset_index(name="عدد")
        st.bar_chart(by_status.set_index("status"))


def sidebar(user):
    st.sidebar.markdown(f'<div class="sidebar-title">🚚 {APP_NAME}</div><div class="sidebar-sub">{user["name"]} • {role_label(user["role"])}</div>',unsafe_allow_html=True)
    role=user["role"]
    if role=="RIDER": menu=[("الرئيسية","rider"),("الخريطة","map")]
    elif role=="RESTAURANT": menu=[("الرئيسية","dashboard"),("طلبات المطعم","orders")]
    else:
        menu=[("الرئيسية","dashboard"),("الطلبات","orders"),("الخريطة الحية","map"),("الطيارون","riders"),("المطاعم والفروع","restaurants"),("الحضور والمرتبات","attendance"),("التسويات","settlements"),("التحليل","analysis"),("المستخدمون","users"),("أدوات النظام","tools")]
    labels=[x[0] for x in menu]
    choice=st.sidebar.radio("التنقل",labels,index=0)
    if st.sidebar.button("تسجيل الخروج",use_container_width=True):
        st.session_state.pop("user",None); st.rerun()
    return dict(menu)[choice]


# =========================================================
# نقطة التشغيل
# =========================================================
if "user" not in st.session_state:
    login()
    st.stop()

user=st.session_state.user
page=sidebar(user)

try:
    {
        "dashboard":render_dashboard,
        "orders":render_orders,
        "map":render_map,
        "rider":render_rider,
        "riders":render_riders,
        "restaurants":render_restaurants,
        "attendance":render_attendance,
        "settlements":render_settlements,
        "users":render_users,
        "tools":render_tools,
        "analysis":render_analysis,
    }[page](user)
except Exception as ex:
    st.error("حدث خطأ غير متوقع داخل الواجهة.")
    st.exception(ex)
