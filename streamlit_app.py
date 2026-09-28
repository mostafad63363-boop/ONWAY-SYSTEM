import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# إعدادات الواجهة (Dark Mode & Gold Accents)
st.set_page_config(page_title="ONWAY Delivery System", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    h1, h2, h3 { color: #FFD700; font-family: 'Arial', sans-serif; }
    .stButton>button { background-color: #FFD700; color: #000000; border-radius: 5px; font-weight: bold; }
    .stButton>button:hover { background-color: #E5C100; color: #000000; }
    .stDataFrame { border: 1px solid #FFD700; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# الاتصال بقاعدة البيانات (يتم إنشاؤها تلقائياً)
conn = sqlite3.connect('onway_database.db', check_same_thread=False)
c = conn.cursor()

# بناء الجداول تلقائياً إذا لم تكن موجودة
c.execute('''CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT, pickup_zone TEXT, dropoff_zone TEXT, 
    status TEXT, cash_collected REAL, created_at TEXT)''')
conn.commit()

# عنوان النظام
st.title("📦 ONWAY Delivery Management")
st.markdown("---")

# تقسيم الواجهة إلى شاشات
tab1, tab2, tab3 = st.tabs(["لوحة التحكم", "إضافة طلب جديد", "إدارة العمليات"])

with tab1:
    st.header("📊 ملخص العمليات اللحظي")
    df = pd.read_sql_query("SELECT * FROM orders", conn)
    if not df.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("إجمالي الطلبات", len(df))
        col2.metric("الكاش المتحصل", f"{df['cash_collected'].sum()} ج.م")
        col3.metric("الطلبات المكتملة", len(df[df['status'] == 'تم التسليم']))
        st.dataframe(df.tail(5), use_container_width=True) # عرض آخر 5 طلبات
    else:
        st.info("لا توجد طلبات مسجلة حتى الآن.")

with tab2:
    st.header("➕ إصدار تيكيت جديد")
    with st.form("new_order_form"):
        order_num = st.text_input("رقم الطلب (مثال: ONW-1001)")
        col1, col2 = st.columns(2)
        pickup = col1.selectbox("منطقة الاستلام", ["جليم", "سموحة", "الإبراهيمية", "محطة الرمل", "محرم بك", "أخرى"])
        dropoff = col2.selectbox("منطقة التسليم", ["محرم بك", "جليم", "سموحة", "الإبراهيمية", "محطة الرمل", "أخرى"])
        cash = st.number_input("الكاش المطلوب تحصيله", min_value=0.0, step=10.0)
        
        submitted = st.form_submit_button("إرسال الطلب للطيار")
        if submitted and order_num:
            c.execute("INSERT INTO orders (order_number, pickup_zone, dropoff_zone, status, cash_collected, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                      (order_num, pickup, dropoff, "قيد الانتظار", cash, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            st.success("تم إدراج الطلب بنجاح في قاعدة البيانات!")

with tab3:
    st.header("🛠 التحكم في الطلبات")
    df_ops = pd.read_sql_query("SELECT * FROM orders WHERE status != 'تم التسليم'", conn)
    if not df_ops.empty:
        for index, row in df_ops.iterrows():
            with st.expander(f"طلب رقم: {row['order_number']} | من {row['pickup_zone']} إلى {row['dropoff_zone']}"):
                new_status = st.selectbox("تحديث الحالة", ["قيد الانتظار", "مع الطيار", "تم التسليم", "ملغي"], key=f"status_{row['id']}")
                if st.button("تحديث السجل", key=f"update_{row['id']}"):
                    c.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, row['id']))
                    conn.commit()
                    st.success("تم التحديث! قم بتحديث الصفحة.")
    else:
        st.success("جميع العمليات مكتملة ولا يوجد طلبات معلقة.")
