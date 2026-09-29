import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ==========================================
# 1. إعدادات الصفحة الأساسية
# ==========================================
st.set_page_config(
    page_title="oN way Delivery",
    page_icon="🧡",
    layout="centered",
    initial_sidebar_state="expanded"
)

APP_NAME = "oN way Delivery"

# ==========================================
# 2. الهوية البصرية (ستايل مشابه لطلبات)
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&display=swap');

:root {
    /* ألوان الأساسية */
    --brand: #FF5A00;       
    --brand-hover: #E04D00;
    --brand-light: #FFF0E5;
    
    /* ألوان الخلفيات والنصوص */
    --page: #F8F9FA;
    --card: #FFFFFF;
    --ink: #1F2937;
    --muted: #6B7280;
    --line: #E5E7EB;
    
    /* ألوان الحالات */
    --good: #00B368;        
    --good-light: #E5F7ED;
    --warn: #FFB020;
    --warn-light: #FFF7E6;
    --danger: #FF3B30;
    --danger-light: #FFEBEA;
    --info: #007AFF;
    
    /* تأثيرات */
    --shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    --shadow-hover: 0 8px 24px rgba(255, 90, 0, 0.15);
    --radius: 16px;
    --radius-btn: 50px;
}

html, body, [class*="css"] {
    font-family: 'Cairo', sans-serif !important;
    direction: rtl;
    text-align: right;
}

[data-testid="stAppViewContainer"] { background: var(--page); }
[data-testid="stHeader"] { background: rgba(248, 249, 250, 0.8); backdrop-filter: blur(10px); }
[data-testid="stDecoration"], #MainMenu, footer { display: none; }

.block-container { max-width: 800px; padding: 2rem 1rem 5rem; }

/* الشريط الجانبي */
[data-testid="stSidebar"] { background: var(--card); border-left: 1px solid var(--line); box-shadow: var(--shadow); }
[data-testid="stSidebar"] * { color: var(--ink) !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    padding: 0.8rem 1rem !important; border-radius: 12px !important; margin: 0.2rem 0 !important;
    font-size: 0.95rem !important; font-weight: 700 !important; transition: all 0.2s ease;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background: var(--brand-light); color: var(--brand) !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"] {
    background: var(--brand-light); color: var(--brand) !important; border-right: 4px solid var(--brand);
}

/* الترويسة (Topbar) */
.app-topbar {
    display: flex; align-items: center; justify-content: space-between;
    background: var(--card); border: 1px solid var(--line);
    border-radius: var(--radius); padding: 12px 16px; margin-bottom: 15px;
    box-shadow: var(--shadow);
}
.app-brand { display: flex; align-items: center; gap: 10px; font-size: 1.1rem; font-weight: 900; color: var(--ink); }
.app-brand-mark {
    width: 40px; height: 40px; border-radius: 12px; display: grid; place-items: center;
    background: var(--brand); color: #fff; font-size: 1.2rem; box-shadow: var(--shadow-hover);
}
.user-chip {
    display: flex; align-items: center; gap: 8px; background: var(--page);
    border: 1px solid var(--line); border-radius: 50px; padding: 6px 12px;
    color: var(--ink); font-size: 0.8rem; font-weight: 700;
}
.user-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--good); }

/* الهيرو كارد */
.onway-hero {
    background: var(--card); border: 1px solid var(--line);
    border-radius: var(--radius); padding: 24px; margin-bottom: 20px;
    box-shadow: var(--shadow); border-right: 5px solid var(--brand);
}
.onway-hero h1 { margin: 0; font-size: 1.6rem; font-weight: 900; color: var(--ink); }
.onway-hero p { margin: 0.5rem 0 0; color: var(--muted); font-size: 0.9rem; font-weight: 500; }

/* الإحصائيات */
.metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 20px; }
.metric {
    background: var(--card); border: 1px solid var(--line);
    border-radius: var(--radius); padding: 16px; box-shadow: var(--shadow); text-align: center;
}
.metric .v { font-size: 1.5rem; font-weight: 900; color: var(--ink); }
.metric .l { font-size: 0.85rem; font-weight: 700; color: var(--muted); margin-top: 4px; }

/* الأزرار (دائرية) */
.stButton>button {
    min-height: 48px !important; border-radius: var(--radius-btn) !important;
    background: var(--brand) !important; color: white !important; border: none !important;
    font-weight: 800 !important; font-size: 1rem !important; box-shadow: var(--shadow) !important; width: 10px;
}
.stButton>button:hover { background: var(--brand-hover) !important; transform: scale(1.02); }

/* أزرار شاشة الطيار (عملاقة) */
.rider-btn-green>button { background: var(--good) !important; min-height: 60px !important; font-size: 1.2rem !important; width: 100% !important;}
.rider-btn-green>button:hover { background: #009955 !important; }

/* الحقول */
.stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox>div>div {
    min-height: 48px !important; border-radius: 12px !important; border: 1px solid var(--line) !important;
    background: var(--page) !important; font-weight: 600 !important;
}

/* البطاقات و الحالات */
.card { background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); padding: 16px; box-shadow: var(--shadow); margin-bottom: 15px; }
.status-pill { display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 50px; font-size: 0.75rem; font-weight: 800; background: var(--page); color: var(--ink); }
.status-done { background: var(--good-light); color: var(--good); }
.status-active { background: #E5F0FF; color: #007AFF; }
.status-warn { background: var(--warn-light); color: var(--warn); }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. دوال واجهة المستخدم (UI Helpers)
# ==========================================
def role_label(role):
    return {"admin": "مدير النظام", "rider": "طيار", "vendor": "متجر/تاجر"}.get(role, "مستخدم")

def header_v3(title, subtitle=''):
    user = st.session_state.get('user', {'name': 'زائر', 'role': ''})
    st.markdown(f'''
    <div class="app-topbar">
        <div class="app-brand">
            <div class="app-brand-mark">🧡</div>
            <div>{APP_NAME}</div>
        </div>
        <div class="user-chip">
            <span class="user-dot"></span>
            {user.get("name")} • {role_label(user.get("role"))}
        </div>
    </div>
    <div class="onway-hero">
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>
    ''', unsafe_allow_html=True)

def metric_v3(items):
    cards = "".join([f'<div class="metric"><div class="v">{v}</div><div class="l">{l}</div></div>' for l, v in items])
    st.markdown(f'<div class="metric-grid">{cards}</div>', unsafe_allow_html=True)

def badge_v3(text, kind='soft'):
    classes = {'green': 'status-done', 'blue': 'status-active', 'amber': 'status-warn', 'soft': 'status-pill'}
    css_class = classes.get(kind, "status-pill")
    return f'<span class="status-pill {css_class}">{text}</span>'

# ==========================================
# 4. محاكاة تسجيل الدخول والصلاحيات
# ==========================================
if 'user' not in st.session_state:
    # لتجربة التطبيق، يمكنك تغيير الـ role هنا إلى 'admin' أو 'rider'
    st.session_state['user'] = {'name': 'مصطفى', 'role': 'admin', 'id': 1} 

# ==========================================
# 5. شاشات التطبيق (Views)
# ==========================================

def admin_dashboard():
    header_v3("لوحة التحكم", "نظرة عامة على عمليات التوصيل في الإسكندرية اليوم")
    
    # إحصائيات سريعة
    metric_v3([
        ("الطلبات النشطة", "12"),
        ("تم التوصيل", "45"),
        ("الطيارين المتاحين", "8"),
        ("الإيرادات المتوقعة", "1,250 ج")
    ])
    
    st.markdown('### 📍 الطلبات الحالية (منطقة الالتقاط: جليم - محرم بك)')
    
    # بطاقة طلب تجريبية
    st.markdown(f'''
    <div class="card">
        <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
            <strong>طلب #1042</strong>
            {badge_v3("في الطريق", "blue")}
        </div>
        <p style="margin:5px 0; color:var(--muted); font-size:0.9rem;">📦 نقطة الاستلام: <strong>جليم</strong></p>
        <p style="margin:5px 0; color:var(--muted); font-size:0.9rem;">📍 نقطة التسليم: <strong>العصافرة</strong></p>
        <p style="margin:5px 0; color:var(--muted); font-size:0.9rem;">🛵 الطيار: <strong>أحمد محمود</strong></p>
    </div>
    ''', unsafe_allow_html=True)

    st.markdown(f'''
    <div class="card">
        <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
            <strong>طلب #1043</strong>
            {badge_v3("قيد الانتظار", "amber")}
        </div>
        <p style="margin:5px 0; color:var(--muted); font-size:0.9rem;">📦 نقطة الاستلام: <strong>محرم بك</strong></p>
        <p style="margin:5px 0; color:var(--muted); font-size:0.9rem;">📍 نقطة التسليم: <strong>سموحة</strong></p>
        <p style="margin:5px 0; color:var(--muted); font-size:0.9rem;">🛵 الطيار: <strong>غير محدد</strong></p>
    </div>
    ''', unsafe_allow_html=True)

def rider_dashboard():
    header_v3("شاشة الطيار", "تتبع الطلب الحالي وتحديث الحالة")
    
    # بطاقة معلومات الطلب للطيار (أرقام كبيرة، نصوص واضحة)
    st.markdown(f'''
    <div class="card" style="border-right: 5px solid var(--info);">
        <h3 style="margin-top:0; color:var(--ink);">طلب #1042</h3>
        <hr style="border:0; border-top:1px solid var(--line); margin: 10px 0;">
        <h4 style="margin:10px 0 5px; color:var(--muted);">نقطة الاستلام</h4>
        <p style="font-size:1.2rem; font-weight:800; margin:0;">مطعم كذا - جليم</p>
        
        <h4 style="margin:15px 0 5px; color:var(--muted);">نقطة التسليم</h4>
        <p style="font-size:1.2rem; font-weight:800; margin:0;">شارع 45 - العصافرة</p>
        
        <h4 style="margin:15px 0 5px; color:var(--muted);">المبلغ المطلوب تحصيله</h4>
        <p style="font-size:1.5rem; font-weight:900; color:var(--brand); margin:0;">350 ج.م</p>
    </div>
    ''', unsafe_allow_html=True)

    # أزرار تحكم ضخمة للطيار لسهولة الضغط أثناء القيادة
    st.markdown('<div class="rider-btn-green">', unsafe_allow_html=True)
    if st.button("✅ تم التسليم بنجاح", use_container_width=True):
        st.success("تم تحديث حالة الطلب وإرسال الموقع للإدارة.")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.write("")
    if st.button("🗺️ فتح الموقع على Google Maps", use_container_width=True):
        st.info("سيتم تحويلك لتطبيق الخرائط...")

# ==========================================
# 6. الملاحة الرئيسية (Routing)
# ==========================================
def main():
    user = st.session_state.get('user')
    role = user.get('role')
    
    # بناء الشريط الجانبي بناءً على الصلاحيات
    with st.sidebar:
        st.markdown(f'<div class="sidebar-title">ONWAY</div><div class="sidebar-sub">Delivery Services</div>', unsafe_allow_html=True)
        
        if role == 'admin':
            menu = ["لوحة التحكم", "إدارة الطلبات", "الطيارين", "الإعدادات"]
            choice = st.radio("القائمة الرئيسية:", menu)
            
            if choice == "لوحة التحكم":
                admin_dashboard()
            else:
                header_v3(choice, "جاري تطوير هذه الصفحة...")
                
        elif role == 'rider':
            menu = ["الطلب الحالي", "الطلبات المنجزة", "حسابي"]
            choice = st.radio("قائمة الطيار:", menu)
            
            if choice == "الطلب الحالي":
                rider_dashboard()
            else:
                header_v3(choice, "جاري تطوير هذه الصفحة...")

        st.write("---")
        # زر تبديل الصلاحية (لغرض التجربة فقط)
        new_role = st.selectbox("تبديل الصلاحية (للتجربة):", ["admin", "rider"], index=0 if role=="admin" else 1)
        if new_role != role:
            st.session_state['user']['role'] = new_role
            st.rerun()

if __name__ == '__main__':
    main()
