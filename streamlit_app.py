import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time
import io

# ==========================================
# 1. إعدادات الواجهة والهوية البصرية (Dark & Gold)
# ==========================================
st.set_page_config(page_title="ONWAY Delivery - V9 Core", page_icon="📦", layout="wide")
st.markdown("""
    <style>
    :root { --primary-gold: #FFD700; --dark-bg: #121212; }
    .stApp { background-color: var(--dark-bg); color: #FFFFFF; }
    h1, h2, h3, h4 { color: var(--primary-gold); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: bold;}
    .stButton>button { background-color: var(--primary-gold); color: #000000; border: none; border-radius: 8px; font-weight: bold; transition: all 0.3s; width: 100%;}
    .stButton>button:hover { background-color: #E5C100; transform: scale(1.02); box-shadow: 0 4px 8px rgba(255, 215, 0, 0.3); }
    .metric-card { background-color: #1E1E1E; padding: 15px; border-radius: 10px; border-left: 4px solid var(--primary-gold); box-shadow: 0 2px 4px rgba(0,0,0,0.5);}
    .stDataFrame { border: 1px solid #333; border-radius: 10px; overflow: hidden; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. هندسة قاعدة البيانات العلائقية (Relational DB)
# ==========================================
def init_db():
    conn = sqlite3.connect('onway_core_v9.db', check_same_thread=False)
    c = conn.cursor()
    # جدول الطلبات الشامل
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        order_number TEXT PRIMARY KEY, branch_name TEXT, pickup_zone TEXT, dropoff_zone TEXT, 
        status TEXT, delivery_fee REAL, rider_commission REAL, cash_collected REAL, 
        rider_name TEXT, created_at TEXT, delivered_at TEXT)''')
    # جدول الطيارين
    c.execute('''CREATE TABLE IF NOT EXISTS riders (
        name TEXT PRIMARY KEY, status TEXT, total_balance REAL, active_orders INTEGER)''')
    # جدول الخزينة (Ledger)
    c.execute('''CREATE TABLE IF NOT EXISTS ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT, transaction_type TEXT, amount REAL, reference TEXT, created_at TEXT)''')
    
    # إدخال بيانات افتراضية إذا كانت الجداول فارغة (للتجربة)
    c.execute("SELECT count(*) FROM riders")
    if c.fetchone()[0] == 0:
        riders_data = [("أحمد محمود", "Available", 0.0, 0), ("خالد سيد", "Available", 0.0, 0)]
        c.executemany("INSERT INTO riders VALUES (?, ?, ?, ?)", riders_data)
    conn.commit()
    return conn, c

conn, c = init_db()

# ==========================================
# 3. واجهة المستخدم (التقسيم المتقدم)
# ==========================================
st.title("📦 ONWAY Command Center - Alexandria")
st.markdown("*النظام اللوجستي الأذكى لإدارة أسطول التوصيل*")
st.markdown("---")

tab_dash, tab_dispatch, tab_ops, tab_finance, tab_settings = st.tabs([
    "📊 لوحة القيادة (Dashboard)", 
    "🚀 التوجيه السريع (Dispatch)", 
    "🛠 إدارة العمليات (Operations)", 
    "💰 الخزينة والتسويات (Finance)",
    "⚙️ أدوات النظام (Tools)"
])

# ------------------------------------------
# الشاشة الأولى: لوحة القيادة الذكية (Dashboard)
# ------------------------------------------
with tab_dash:
    df_orders = pd.read_sql_query("SELECT * FROM orders", conn)
    df_riders = pd.read_sql_query("SELECT * FROM riders", conn)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card"><h3>إجمالي الطلبات</h3><h2>{len(df_orders)}</h2></div>""", unsafe_allow_html=True)
    with col2:
        completed = len(df_orders[df_orders['status'] == 'تم التسليم']) if not df_orders.empty else 0
        st.markdown(f"""<div class="metric-card"><h3>الطلبات المكتملة</h3><h2>{completed}</h2></div>""", unsafe_allow_html=True)
    with col3:
        active_riders = len(df_riders[df_riders['status'] == 'Busy']) if not df_riders.empty else 0
        st.markdown(f"""<div class="metric-card"><h3>طيارون في مهمة</h3><h2>{active_riders} / {len(df_riders)}</h2></div>""", unsafe_allow_html=True)
    with col4:
        total_cash = df_orders['cash_collected'].sum() if not df_orders.empty else 0
        st.markdown(f"""<div class="metric-card"><h3>كاش متوقع بالشارع</h3><h2>{total_cash} ج.م</h2></div>""", unsafe_allow_html=True)
    
    st.write("")
    st.subheader("📍 حالة الأسطول اللحظية")
    if not df_riders.empty:
        st.dataframe(df_riders.style.applymap(lambda x: 'color: green' if x == 'Available' else 'color: orange' if x == 'Busy' else '', subset=['status']), use_container_width=True)

# ------------------------------------------
# الشاشة الثانية: نظام التوجيه الذكي (Auto-Dispatch)
# ------------------------------------------
with tab_dispatch:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("إصدار تيكيت جديد (Smart Dispatch)")
        with st.form("dispatch_form"):
            order_num = st.text_input("رقم الطلب (مثال: ONW-5001)")
            branch = st.text_input("اسم الفرع / المطعم")
            
            c1, c2 = st.columns(2)
            pickup = c1.selectbox("نقطة الاستلام", ["جليم", "سموحة", "الإبراهيمية", "محطة الرمل", "محرم بك"])
            dropoff = c2.selectbox("نقطة التسليم", ["محرم بك", "جليم", "سموحة", "الإبراهيمية", "محطة الرمل", "المنتزه", "العجمي"])
            
            c3, c4, c5 = st.columns(3)
            del_fee = c3.number_input("رسوم التوصيل", value=30.0)
            rider_comm = c4.number_input("عمولة الطيار", value=20.0)
            cash = c5.number_input("إجمالي الكاش المتحصل", value=0.0)
            
            # محرك الذكاء الاصطناعي لاقتراح الطيار (يجلب الطيارين المتاحين)
            available_riders = pd.read_sql_query("SELECT name FROM riders WHERE status = 'Available'", conn)['name'].tolist()
            rider_options = available_riders + ["تعيين لاحقاً"]
            assigned_rider = st.selectbox("تعيين طيار (اقتراح ذكي)", rider_options)
            
            submit = st.form_submit_button("🚀 إطلاق الطلب")
            
            if submit and order_num:
                try:
                    c.execute("""INSERT INTO orders 
                        (order_number, branch_name, pickup_zone, dropoff_zone, status, delivery_fee, rider_commission, cash_collected, rider_name, created_at) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (order_num, branch, pickup, dropoff, "قيد التوصيل" if assigned_rider != "تعيين لاحقاً" else "قيد الانتظار", 
                         del_fee, rider_comm, cash, assigned_rider if assigned_rider != "تعيين لاحقاً" else None, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    
                    if assigned_rider != "تعيين لاحقاً":
                        c.execute("UPDATE riders SET status = 'Busy', active_orders = active_orders + 1 WHERE name = ?", (assigned_rider,))
                    
                    conn.commit()
                    st.success(f"تم توجيه الطلب بنجاح! {'الطيار ' + assigned_rider + ' في طريقه للاستلام' if assigned_rider != 'تعيين لاحقاً' else 'في انتظار تعيين طيار.'}")
                except sqlite3.IntegrityError:
                    st.error("رقم الطلب موجود مسبقاً! يرجى التأكد.")

# ------------------------------------------
# الشاشة الثالثة: إدارة العمليات (Operations)
# ------------------------------------------
with tab_ops:
    st.subheader("🛠 غرفة العمليات الحية")
    df_live = pd.read_sql_query("SELECT * FROM orders WHERE status IN ('قيد الانتظار', 'قيد التوصيل')", conn)
    
    if not df_live.empty:
        for _, row in df_live.iterrows():
            with st.expander(f"📦 {row['order_number']} | من {row['pickup_zone']} إلى {row['dropoff_zone']} | 🛵 {row['rider_name'] or 'بدون طيار'}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**المطعم:** {row['branch_name']}")
                    st.write(f"**الكاش المطلوب:** {row['cash_collected']} ج.م")
                with c2:
                    # زر الإغلاق الذكي (يقوم بالمحاسبة التلقائية)
                    if st.button(f"✅ إتمام التسليم للطلب {row['order_number']}", key=f"done_{row['order_number']}"):
                        # 1. تحديث حالة الطلب
                        c.execute("UPDATE orders SET status = 'تم التسليم', delivered_at = ? WHERE order_number = ?", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), row['order_number']))
                        
                        # 2. تحديث حالة الطيار وحسابه
                        if row['rider_name']:
                            # إضافة عمولة الطيار وخصم الكاش المتحصل منه (محاسبة دقيقة)
                            net_rider_impact = row['rider_commission'] - row['cash_collected']
                            c.execute("UPDATE riders SET status = 'Available', active_orders = active_orders - 1, total_balance = total_balance + ? WHERE name = ?", (net_rider_impact, row['rider_name']))
                        
                        # 3. تسجيل في الخزينة
                        c.execute("INSERT INTO ledger (transaction_type, amount, reference, created_at) VALUES (?, ?, ?, ?)", 
                                  ("إيراد توصيل", row['delivery_fee'], row['order_number'], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        
                        conn.commit()
                        st.success("تم إغلاق الطلب وتحديث الخزينة وحساب الطيار تلقائياً! يرجى تحديث الصفحة.")
    else:
        st.info("لا توجد طلبات معلقة في الميدان حالياً.")

# ------------------------------------------
# الشاشة الرابعة: الخزينة والتسويات (Finance)
# ------------------------------------------
with tab_finance:
    st.subheader("💰 النظام المحاسبي (Ledger & Settlements)")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**حسابات الطيارين (الرصيد النهائي)**")
        df_riders_fin = pd.read_sql_query("SELECT name as 'اسم الطيار', total_balance as 'الرصيد المستحق (سالب = مديونية للشركة)' FROM riders", conn)
        st.dataframe(df_riders_fin, use_container_width=True)
    
    with col2:
        st.markdown("**حركة الخزينة العامة**")
        df_ledger = pd.read_sql_query("SELECT * FROM ledger ORDER BY id DESC LIMIT 10", conn)
        if not df_ledger.empty:
            st.dataframe(df_ledger, use_container_width=True)
            st.metric("إجمالي إيرادات الخزينة (رسوم توصيل)", f"{df_ledger['amount'].sum()} ج.م")
        else:
            st.info("لا توجد حركات مالية بعد.")

# ------------------------------------------
# الشاشة الخامسة: أدوات النظام (Tools & Export)
# ------------------------------------------
with tab_settings:
    st.subheader("⚙️ أدوات التحكم المتقدمة")
    st.markdown("هنا يمكنك استخراج بيانات النظام لتتوافق مع ملفك الأصلي (نظام ONWAY شهرى.xlsx).")
    
    # تحويل قاعدة البيانات إلى Excel للتحميل
    if st.button("📥 تصدير قاعدة البيانات كملف Excel (نسخة احتياطية)"):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            pd.read_sql_query("SELECT * FROM orders", conn).to_excel(writer, sheet_name='الطلبات', index=False)
            pd.read_sql_query("SELECT * FROM riders", conn).to_excel(writer, sheet_name='الطيارون', index=False)
            pd.read_sql_query("SELECT * FROM ledger", conn).to_excel(writer, sheet_name='الخزينة', index=False)
        
        st.download_button(
            label="تحميل ملف ONWAY_Backup.xlsx",
            data=output.getvalue(),
            file_name=f"ONWAY_Backup_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
