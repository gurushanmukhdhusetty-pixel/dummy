import streamlit as st
import pandas as pd
import uuid
import base64
from datetime import datetime
import streamlit.components.v1 as components
from PIL import Image
import io
import requests
import random
import time  # SMS ప్రాసెస్ పూర్తి అవ్వడానికి సమయం ఇవ్వడం కోసం

# --- COMPULSORY LIBRARIES VALIDATION ---
try:
    from fpdf import FPDF
    PDF_READY = True
except ImportError:
    PDF_READY = False

st.set_page_config(page_title="Titan Inventory & POS System", page_icon="🛒", layout="wide", initial_sidebar_state="expanded")

# -----------------------------
# BACKEND CORE PIPELINE: QUICK SMS API INTEGRATION
# -----------------------------
FAST2SMS_API_KEY = "UxoZARPvI9wTO2HksEmYLSp5KcthfzbXCQ10gdirnqNeVjlF7Jy2utkdHZ8hMVswOliInc59mYFBDUGT"
FAST2SMS_URL = "https://www.fast2sms.com/dev/bulkV2"

def trigger_sms_bill_delivery(phone_input, order_id, total_amount):
    if not FAST2SMS_API_KEY:
        st.error("SMS API Key కనుగొనబడలేదు.")
        return False

    # ఫోన్ నంబర్ క్లీన్ చేయడం
    clean_phone = "".join(filter(str.isdigit, str(phone_input)))
    
    if len(clean_phone) == 12 and clean_phone.startswith("91"):
        clean_phone = clean_phone[2:]
        
    if len(clean_phone) != 10:
        st.warning(f"⚠️ తప్పుడు ఫోన్ నంబర్: '{phone_input}'. నంబర్ 10 అంకెలు ఉండాలి ('Walk-in' కి మెసేజ్ వెళ్లదు).")
        return False

    message_text = (
        f"thanks for shopping at titan stores. reference {order_id} "
        f"for {int(total_amount)} inr has been processed smoothly."
    )
    
    payload = {
        "authorization": FAST2SMS_API_KEY,
        "route": "q",
        "message": message_text,
        "numbers": clean_phone
    }
    
    try:
        # టెలికాం గేట్‌వే కనెక్ట్ చేయడానికి అభ్యర్థన పంపడం
        with st.spinner("టెలికాం గేట్‌వేకి మెసేజ్ పంపుతోంది..."):
            response = requests.get(FAST2SMS_URL, params=payload, timeout=10)
            res_json = response.json()
            if res_json.get("return", False):
                st.success(f"📱 మెసేజ్ విజయవంతంగా పంపబడింది! Request ID: {res_json.get('request_id')}")
                return True
            else:
                st.error(f"❌ గేట్‌వే లోపం: {res_json.get('message')}")
                return False
    except Exception as e:
        st.error(f"🌐 నెట్‌వర్క్ కనెక్షన్ లోపం: {str(e)}")
        return False

# -----------------------------
# 1. STRICT SUPABASE ENVIRONMENT CONNECTION
# -----------------------------
try:
    from supabase import create_client
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    db = create_client(url, key)
    DB_CONNECTED = True
except Exception as e:
    db = None
    DB_CONNECTED = False
    CONNECTION_ERROR = str(e)

# -----------------------------
# 2. TRANSLATION INTERFACE MAP
# -----------------------------
T = {
    "English": {
        "dash": "📊 Dashboard Metrics", "inv": "📦 Inventory Management", "pos": "🛒 Point of Sale", 
        "staff": "👥 Staff & User Management", "analytics": "🔮 Predictive Analytics", "logout": "Logout",
        "login_btn": "Login", "user": "Username", "pass": "Password",
        "tot_prod": "Unique Items", "stock": "Total Items Stocked", "rev": "Net Gross Revenue",
        "add_prod": "➕ Register New Product", "p_name": "Product Name", "sku": "SKU / Barcode",
        "price": "Price (₹)", "qty": "Quantity", "upload": "📷 Upload Product Photo", "save": "Save to Database",
        "db": "📋 Live Database (Edit text directly or change images below)", "search": "🔍 Search Products...",
        "add": "Add", "cart": "🧾 Current Cart", "empty": "Cart is Empty",
        "sub": "Subtotal", "disc": "Discount", "tax": "Tax", "tot": "Total",
        "cust": "Customer Mobile (10-Digit)", "checkout": "💳 Checkout & Generate Bill", "dl_pdf": "📄 Download PDF Bill",
        "staff_name": "Full Name", "role": "Role", "add_staff": "Add Staff Member", "dl_csv": "📥 Export CSV"
    },
    "Hindi": {
        "dash": "📊 डैशबोर्ड मेट्रिक्स", "inv": "📦 इन्वेंटरी प्रबंधन", "pos": "🛒 बिक्री केंद्र (POS)", 
        "staff": "👥 स्टाफ और उपयोगकर्ता प्रबंधन", "analytics": "🔮 भविष्य कहनेवाला विश्लेषण", "logout": "लॉग आउट",
        "login_btn": "लॉग इन करें", "user": "उपयोगकर्ता नाम", "pass": "पासवर्ड",
        "tot_prod": "अद्वितीय उत्पाद", "stock": "स्टॉक में कुल इकाइयाँ", "rev": "कुल सकल राजस्व",
        "add_prod": "➕ नया उत्पाद पंजीकृत करें", "p_name": "उत्पाद का नाम", "sku": "बारकोड / SKU",
        "price": "कीमत (₹)", "qty": "मात्रा", "upload": "📷 उत्पाद फोटो अपलोड करें", "save": "डेटाबेस में सहेजें",
        "db": "📋 लाइव डेटाबेस (सीधे संशोधित करें या नीचे चित्र बदलें)", "search": "🔍 उत्पाद खोजें...",
        "add": "जोड़ें", "cart": "🧾 वर्तमान कार्ट", "empty": "कार्ट खाली है",
        "sub": "उप-योग", "disc": "छूट", "tax": "कर", "tot": "कुल योग",
        "cust": "ग्राहक मोबाइल नंबर", "checkout": "💳 चेकआउट और बिल बनाएं", "dl_pdf": "📄 PDF बिल डाउनलोड करें",
        "staff_name": "पूरा नाम", "role": "भूमिका", "add_staff": "स्टाफ सदस्य जोड़ें", "dl_csv": "📥 CSV निर्यात करें"
    },
    "Telugu": {
        "dash": "📊 డాష్‌బోర్డ్ గణాంకాలు", "inv": "📦 ఇన్వెంతరీ మేనేజెమెంట్", "pos": "🛒 పాయింట్ ఆఫ్ సేల్ (POS)", 
        "staff": "👥 సిబ్బంది & వినియోగదారు నిర్వహణ", "analytics": "🔮 ప్రిడిక్టివ్ అనలిటిక్స్", "logout": "లాగ్‌అవుట్",
        "login_btn": "లాగిన్", "user": "వినియోగదారు పేరు", "pass": "పాస్వర్డ్",
        "tot_prod": "ప్రత్యేక వస్తువులు", "stock": "మొత్తం స్టాక్", "rev": "నికర రాబడి",
        "add_prod": "➕ కొత్త ఉత్పత్తిని చేర్చండి", "p_name": "ఉత్పత్తి పేరు", "sku": "బార్‌కోడ్ / SKU",
        "price": "ధర (₹)", "qty": "పరిమాణం", "upload": "📷 ఉత్పత్తి ఫోటో అప్‌లోడ్", "save": "డేటాబేస్‌లో సేవ్ చేయి",
        "db": "📋 లైవ్ డేటాబేస్ (సవరించడానికి డబుల్ క్లిక్ చేయండి)", "search": "🔍 ఉత్పత్తులను వెతకండి...",
        "add": "జోడించు", "cart": "🧾 ప్రస్తుత కార్ట్", "empty": "కార్ట్ ఖాళీగా ఉంది",
        "sub": "ఉపమొత్తం", "disc": "డిస్కౌంట్", "tax": "పన్ను", "tot": "మొత్తం బిల్లు",
        "cust": "కస్టమర్ మొబైల్ నంబర్", "checkout": "💳 చెక్అవుట్ & బిల్లు జనరేషన్", "dl_pdf": "📄 PDF బిల్లు డౌన్‌లోడ్",
        "staff_name": "పూర్తి పేరు", "role": "పాత్ర", "add_staff": "సిబ్బందిని...జోడించండి", "dl_csv": "📥 CSV డౌన్‌లోడ్"
    }
}

# -----------------------------
# 3. RUNTIME INITIALIZATION
# -----------------------------
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "current_user" not in st.session_state: st.session_state["current_user"] = None
if "lang" not in st.session_state: st.session_state["lang"] = "English"
if "low_stock_threshold" not in st.session_state: st.session_state["low_stock_threshold"] = 5
if "cart" not in st.session_state: st.session_state["cart"] = []
if "last_receipt" not in st.session_state: st.session_state["last_receipt"] = None
if "current_page" not in st.session_state: st.session_state["current_page"] = "pos"

lang = T[st.session_state["lang"]]

st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #E0E7FF 0%, #EDE9FE 100%) !important; color: #1E293B !important; }
h1, h2, h3, .stApp h1, .stApp h2, .stApp h3, [data-testid="stMetricLabel"] { color: #DC2626 !important; font-weight: 700 !important; }
.stApp p, .stApp span, label { color: #1E293B !important; }
button[kind="primary"] { background-color: #DC2626 !important; color: #FFFFFF !important; border: none !important; font-weight: bold !important; padding: 12px 24px !important; }
button[kind="primary"]:hover { background-color: #991B1B !important; }
button[kind="secondary"] { background-color: #FFFFFF !important; color: #4338CA !important; border: 1px solid #C7D2FE !important; }
.login-container { background: #FFFFFF !important; padding: 35px 25px !important; border-radius: 16px !important; border-top: 6px solid #DC2626 !important; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1) !important; width: 100% !important; max-width: 420px !important; margin: 40px auto !important; text-align: center; }
div[data-baseweb="input"] input, .stNumberInput input, .stTextInput input { background-color: #FFFFFF !important; color: #1E293B !important; border: 1px solid #CBD5E1 !important; padding: 10px 14px !important; font-size: 16px !important; }
[data-testid="metric-container"] { background: #FFFFFF !important; border: 1px solid #E2E8F0 !important; padding: 20px !important; border-radius: 12px !important; border-top: 4px solid #DC2626 !important; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05) !important; }
.user-profile-badge { background-color: #FFFFFF !important; border-left: 4px solid #DC2626 !important; padding: 12px 16px !important; border-radius: 8px !important; box-shadow: 0 2px 4px rgba(0,0,0,0.04) !important; margin-bottom: 15px !important; }
</style>
""", unsafe_allow_html=True)

def fetch_inventory():
    if not DB_CONNECTED:
        return pd.DataFrame([
            {"id": "coke", "sku": "890123", "name": "Coca Cola Soda", "price": 40.0, "quantity": 50, "image": None, "category": "Drinks"},
            {"id": "maggi", "sku": "890456", "name": "Maggi Noodles", "price": 14.0, "quantity": 80, "image": None, "category": "General"}
        ])
    res = db.table("inventory").select("*").order("name").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["id", "sku", "name", "price", "quantity", "image", "category"])

def fetch_sales_count():
    if not DB_CONNECTED: return pd.DataFrame(columns=["id", "customer", "total", "date_str", "payment_mode"])
    res = db.table("sales").select("*").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["id", "customer", "total", "date_str", "payment_mode"])

def get_compressed_base64_image(uploaded_file):
    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file)
            if image.mode in ("RGBA", "P"): image = image.convert("RGB")
            image.thumbnail((150, 150))
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=40)
            base64_str = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/jpeg;base64,{base64_str}"
        except Exception as e: 
            st.error(f"Compression Failure: {e}")
    return None

def render_weather_predictive_alerts(df_inv):
    try:
        api_key = st.secrets["OPENWEATHER_API_KEY"]
    except Exception:
        st.warning("⚠️ OpenWeather API Key missing from configuration files.")
        return

    url = f"https://api.openweathermap.org/data/2.5/forecast?q=Hyderabad,IN&appid={api_key}&units=metric"
    try:
        response = requests.get(url, timeout=4).json()
        forecast_list = response.get("list", [])
        if response.get("cod") != "200" or not forecast_list:
            return
        max_temp = max([item["main"]["temp_max"] for item in forecast_list[:16]])
        has_rain = any(["rain" in item.get("weather", [{}])[0].get("main", "").lower() for item in forecast_list[:16]])
        
        c_w1, c_w2 = st.columns(2)
        c_w1.metric("Calculated 48H Peak Temp", f"{max_temp:.1f}°C")
        c_w2.metric("Precipitation Inbound", "Yes" if has_rain else "No")
    except Exception as e:
        pass

def generate_pdf(sale_id, date_str, customer, cart, subtotal, discount, tax, total, pay_mode="Cash"):
    if not PDF_READY: return None
    pdf = FPDF()
    pdf.add_page(); pdf.rect(5, 5, 200, 287)
    pdf.set_font("Arial", 'B', 18); pdf.cell(190, 15, "TITAN CONVENIENCE AND GROCERY", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(95, 6, f"Invoice No: {sale_id}", 0, 0); pdf.cell(95, 6, f"Date/Time: {date_str}", 0, 1, 'R')
    pdf.cell(190, 6, f"Customer: {customer} | Mode: {pay_mode}", 0, 1)
    return bytes(pdf.output())

def dashboard():
    st.title(lang["dash"])
    df_inv = fetch_inventory()
    df_sales = fetch_sales_count()
    tot_sku = len(df_inv)
    tot_rev = df_sales["total"].astype(float).sum() if not df_sales.empty else 0.0
    
    c1, c2 = st.columns(2)
    c1.metric(lang["rev"], f"₹{tot_rev:,.2f}")
    c2.metric(lang["tot_prod"], f"{tot_sku} Items")

def inventory():
    st.title(lang["inv"])
    df_inv = fetch_inventory()
    st.subheader(lang["db"])
    st.dataframe(df_inv)

def pos():
    st.title(lang["pos"])
    df_inv = fetch_inventory()
    if df_inv.empty: st.warning("Inventory empty."); return

    col1, col2 = st.columns([2.0, 1.2])
    with col1:
        chosen_cat = st.radio("Quick Filters By Department Tag", ["All", "Drinks", "Snacks", "Dairy", "General"], index=0, horizontal=True)
        search = st.text_input(lang["search"], value="", key="pos_live_search", autocomplete="off")
        
        display_df = df_inv.copy()
        if chosen_cat != "All":
            display_df = display_df[display_df['category'] == chosen_cat]
            
        cols = st.columns(3)
        for idx, row in display_df.reset_index().iterrows():
            with cols[idx % 3]:
                with st.container(border=True):
                    st.markdown(f"**{row['name']}**")
                    st.markdown(f"#### ₹{row['price']:,.2f}")
                    qty = st.number_input("Q", 1, max(int(row['quantity']), 1), key=f"q_{row['id']}", label_visibility="collapsed")
                    if st.button(lang["add"], key=f"b_{row['id']}", type="primary", use_container_width=True):
                        st.session_state.cart.append({"id": row["id"], "name": row["name"], "price": row["price"], "quantity": qty, "subtotal": row["price"] * qty})
                        st.rerun()

    with col2:
        with st.container(border=True):
            st.subheader(lang["cart"])
            if not st.session_state.cart: st.info(lang["empty"])
            else:
                subtotal = sum(i["subtotal"] for i in st.session_state.cart)
                for idx, item in enumerate(st.session_state.cart):
                    st.write(f"{item['quantity']}x {item['name']} - ₹{item['subtotal']:,.2f}")
                
                disc_pct = st.slider(f"{lang['disc']} (%)", 0, 100, 0)
                disc_amt = subtotal * (disc_pct / 100)
                tax_amt = (subtotal - disc_amt) * 0.05
                total = (subtotal - disc_amt) + tax_amt
                
                st.markdown(f"### {lang['tot']}: ₹{total:,.2f}")
                
                st.markdown("##### 👥 Customer Transaction Routing")
                customer_input = st.text_input(lang["cust"], value="9542762386").strip() # defaultగా మీ నంబర్ సెట్ చేయబడింది
                payment_mode = st.radio("Settle Payment Mode", ["Cash / UPI", "Card", "Khata Store Credit"], horizontal=True)
                
                st.divider()
                
                if st.button(lang["checkout"], type="primary", use_container_width=True):
                    s_id = str(random.randint(10000000, 99999999))
                    d_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    if DB_CONNECTED:
                        for c_item in st.session_state.cart:
                            current_stock = df_inv[df_inv['id'] == c_item['id']]['quantity'].values[0]
                            db.table("inventory").update({"quantity": int(current_stock - c_item['quantity'])}).eq("id", c_item['id']).execute()
                        db.table("sales").insert({"id": s_id, "customer": customer_input, "total": total, "date_str": d_str, "payment_mode": payment_mode}).execute()
                    
                    st.session_state.last_receipt = {"id": s_id, "date": d_str, "cust": customer_input, "items": list(st.session_state.cart), "sub": subtotal, "disc": disc_amt, "tax": tax_amt, "tot": total, "mode": payment_mode}
                    
                    # 🚀 TRIGGER FIREWALL-SAFE QUICK SMS ROUTE
                    sms_status = trigger_sms_bill_delivery(phone_input=customer_input, order_id=s_id, total_amount=total)
                    
                    if PDF_READY:
                        st.session_state['pdf'] = generate_pdf(s_id, d_str, customer_input, st.session_state.cart, subtotal, disc_amt, tax_amt, total, payment_mode)
                        st.session_state['pdf_name'] = f"Invoice_{s_id}.pdf"
                    
                    st.session_state.cart.clear()
                    
                    # SMS నెట్‌వర్క్ ప్రాసెస్ రన్ అవ్వడానికి 2 సెకన్లు విరామం ఇవ్వడం (Rerun కి ముందు)
                    time.sleep(2)
                    st.rerun()

def staff():
    st.title(lang["staff"])

def analytics():
    st.title(lang["analytics"])

# -----------------------------
# 8. ENFORCED CLOUD AUTHENTICATION LAYER
# -----------------------------
if not DB_CONNECTED:
    st.session_state["logged_in"] = True
    st.session_state["current_user"] = {"username": "local_operator", "role": "Owner", "is_main": True}

if not st.session_state["logged_in"]:
    st.info("Please Login")
else:
    with st.sidebar:
        role = st.session_state.current_user["role"]
        if st.button(lang["pos"], use_container_width=True, type="secondary"): st.session_state["current_page"] = "pos"
        if st.button(lang["inv"], use_container_width=True, type="secondary"): st.session_state["current_page"] = "inventory"
        if st.button(lang["dash"], use_container_width=True, type="secondary"): st.session_state["current_page"] = "dashboard"
        chosen_lang = st.selectbox("🌐 Language", ["English", "Hindi", "Telugu"], index=["English", "Hindi", "Telugu"].index(st.session_state.lang))
        if chosen_lang != st.session_state.lang:
            st.session_state.lang = chosen_lang
            st.rerun()

    pages = {"pos": pos, "inventory": inventory, "dashboard": dashboard, "staff": staff, "analytics": analytics}
    pages[st.session_state["current_page"]]()
