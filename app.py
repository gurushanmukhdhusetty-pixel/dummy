import streamlit as st
import pandas as pd
import uuid
import base64
from datetime import datetime
import streamlit.components.v1 as components
from PIL import Image
import io

# --- COMPULSORY LIBRARIES VALIDATION ---
try:
    from fpdf import FPDF
    PDF_READY = True
except ImportError:
    PDF_READY = False

st.set_page_config(page_title="Titan Inventory & POS System", page_icon="🛒", layout="wide", initial_sidebar_state="expanded")

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
    DB_CONNECTED = False
    CONNECTION_ERROR = str(e)

# -----------------------------
# 2. TRANSLATION INTERFACE MAP
# -----------------------------
T = {
    "English": {
        "dash": "📊 Dashboard", "inv": "📦 Inventory", "pos": "🛒 Point of Sale", 
        "staff": "👥 Staff & User Management", "analytics": "📈 Analytics", "logout": "🚪 Logout",
        "login_btn": "Login", "user": "Username", "pass": "Password",
        "tot_prod": "Total Products", "stock": "Units in Stock", "rev": "Gross Revenue",
        "add_prod": "➕ Register New Product", "p_name": "Product Name", "sku": "SKU / Barcode",
        "price": "Price (₹)", "qty": "Quantity", "upload": "📷 Upload Product Photo", "save": "Save to Database",
        "db": "📋 Live Database (Double-click to edit)", "search": "🔍 Search Products...",
        "add": "Add", "cart": "🧾 Current Cart", "empty": "Cart is Empty",
        "sub": "Subtotal", "disc": "Discount", "tax": "Tax", "tot": "Total",
        "cust": "Customer Name", "checkout": "💳 Checkout & Generate Bill", "dl_pdf": "📄 Download PDF Bill",
        "staff_name": "Full Name", "role": "Role", "add_staff": "Add Staff Member", "dl_csv": "📥 Export CSV"
    },
    "Hindi": {
        "dash": "📊 डैशबोर्ड", "inv": "📦 इन्वेंटरी", "pos": "🛒 बिक्री केंद्र (POS)", 
        "staff": "👥 स्टाफ और प्रबंधन", "analytics": "📈 एनालिटिक्स", "logout": "🚪 लॉग आउट",
        "login_btn": "लॉग इन करें", "user": "उपयोगकर्ता नाम", "pass": "पासवर्ड",
        "tot_prod": "कुल उत्पाद", "stock": "स्टॉक में इकाइयाँ", "rev": "कुल आय",
        "add_prod": "➕ नया उत्पाद जोड़ें", "p_name": "उत्पाद का नाम", "sku": "बारकोड",
        "price": "कीमत (₹)", "qty": "मात्रा", "upload": "📷 फोटो अपलोड करें", "save": "सेव करें",
        "db": "📋 डेटाबेस (संपादित करने के लिए डबल-क्लिक करें)", "search": "🔍 उत्पाद खोजें...",
        "add": "जोड़ें", "cart": "🧾 कार्ट", "empty": "कार्ट खाली है",
        "sub": "उप-योग", "disc": "छूट", "tax": "कर", "tot": "कुल",
        "cust": "ग्राहक का नाम", "checkout": "💳 चेकआउट और बिल (PDF)", "dl_pdf": "📄 PDF बिल डाउनलोड करें",
        "staff_name": "पूरा नाम", "role": "भूमिका", "add_staff": "स्टाफ जोड़ें", "dl_csv": "📥 CSV डाउनलोड करें"
    },
    "Telugu": {
        "dash": "📊 డాష్‌బోర్డ్", "inv": "📦 ఇన్వెంటరీ", "pos": "🛒 విక్రయ కేంద్రం (POS)", 
        "staff": "👥 సిబ్బంది & యూజర్ మేనేజ్మెంట్", "analytics": "📈 విశ్లేషణలు", "logout": "🚪 లాగ్ అవుట్",
        "login_btn": "లాగిన్", "user": "వినియోగదారు పేరు", "pass": "పాస్వర్డ్",
        "tot_prod": "మొత్తం ఉత్పత్తులు", "stock": "స్టాక్", "rev": "మొత్తం ఆదాయం",
        "add_prod": "➕ కొత్త ఉత్పత్తిని జోడించండి", "p_name": "ఉత్పత్తి పేరు", "sku": "బార్‌కోడ్",
        "price": "ధర (₹)", "qty": "పరిమాణం", "upload": "📷 ఫోటో అప్‌లోడ్", "save": "సేవ్ చేయండి",
        "db": "📋 డేటాబేస్ (సవరించడానికి డబుల్ క్లిక్ చేయండి)", "search": "🔍 ఉత్పత్తులను శోధించండి...",
        "add": "జోడించు", "cart": "🧾 బండి", "empty": "బండి ఖాళీగా ఉంది",
        "sub": "ఉపమొత్తం", "disc": "డిస్కౌంట్", "tax": "పన్ను", "tot": "మొత్తం",
        "cust": "కస్టమర్ పేరు", "checkout": "💳 చెక్అవుట్ & బిల్లు", "dl_pdf": "📄 PDF బిల్లు డౌన్‌లోడ్",
        "staff_name": "పూర్తి పేరు", "role": "పాత్ర", "add_staff": "సిబ్బందిని జోడించండి", "dl_csv": "📥 CSV డౌన్‌లోడ్ చేయండి"
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

lang = T[st.session_state.lang]

# 🌟 CLEAN LIGHT-MODE THEME OVERRIDES 🌟
st.markdown("""
<style>
/* Reset color conflict zones to allow Streamlit's native Light Mode engine to shine */
.stApp, .stApp p, .stApp span, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6, label { 
    color: inherit; 
}
/* Ensure product image frames fit perfectly inside catalog layouts */
.product-card-img {
    border-radius: 8px; max-height: 140px; object-fit: cover; width: 100%;
}
</style>
""", unsafe_allow_html=True)

def fetch_inventory():
    res = db.table("inventory").select("*").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["id", "sku", "name", "price", "quantity", "image"])

def fetch_sales_count():
    res = db.table("sales").select("*").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["id", "customer", "total", "date_str"])

# 🌟 AUTO-COMPRESSION LOGIC TO PREVENT PAYLOAD SIZE ERRORS 🌟
def get_compressed_base64_image(uploaded_file):
    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file)
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            image.thumbnail((300, 300))
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=60)
            base64_str = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/jpeg;base64,{base64_str}"
        except Exception as e:
            st.error(f"Image Compression Failure: {e}")
    return None

# -----------------------------
# 4. INVOICE GENERATOR
# -----------------------------
def generate_pdf(sale_id, date_str, customer, cart, subtotal, discount, tax, total):
    if not PDF_READY: return None
    pdf = FPDF()
    pdf.add_page()
    pdf.rect(5, 5, 200, 287)
    
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(190, 15, "TITAN CONVENIENCE AND GROCERY", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(190, 5, "Official Retail Transaction Invoice", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Arial", '', 10)
    pdf.cell(95, 6, f"Invoice No: {sale_id}", 0, 0)
    pdf.cell(95, 6, f"Date/Time: {date_str}", 0, 1, 'R')
    pdf.cell(190, 6, f"Customer: {customer}", 0, 1)
    pdf.line(10, 45, 200, 45)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(90, 8, "Item Description", 1, 0, 'C')
    pdf.cell(30, 8, "Qty", 1, 0, 'C')
    pdf.cell(70, 8, "Amount (Rs)", 1, 1, 'C')
    
    pdf.set_font("Arial", '', 10)
    for item in cart:
        clean_name = item['name'].encode('ascii', 'ignore').decode('ascii')[:30]
        if not clean_name: clean_name = "Grocery Item"
        pdf.cell(90, 8, f" {clean_name}", 1, 0)
        pdf.cell(30, 8, str(item['quantity']), 1, 0, 'C')
        pdf.cell(70, 8, f"{item['subtotal']:,.2f} ", 1, 1, 'R')
        
    pdf.ln(5)
    pdf.cell(120, 6, "", 0, 0); pdf.cell(35, 6, "Subtotal:", 0, 0, 'R'); pdf.cell(35, 6, f"{subtotal:,.2f} ", 0, 1, 'R')
    if discount > 0:
        pdf.cell(120, 6, "", 0, 0); pdf.cell(35, 6, "Discount:", 0, 0, 'R'); pdf.cell(35, 6, f"-{discount:,.2f} ", 0, 1, 'R')
    pdf.cell(120, 6, "", 0, 0); pdf.cell(35, 6, "Tax (5%):", 0, 0, 'R'); pdf.cell(35, 6, f"+{tax:,.2f} ", 0, 1, 'R')
    
    pdf.line(130, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(120, 8, "", 0, 0); pdf.cell(35, 8, "GRAND TOTAL:", 0, 0, 'R'); pdf.cell(35, 8, f"{total:,.2f} ", 0, 1, 'R')
    return bytes(pdf.output(dest='S'), 'latin-1')

# -----------------------------
# 5. CORE INTERFACE PAGES
# -----------------------------
def dashboard():
    st.title(lang["dash"])
    df_inv = fetch_inventory()
    df_sales = fetch_sales_count()
    
    tot_qty = df_inv["quantity"].sum() if not df_inv.empty else 0
    tot_rev = df_sales["total"].astype(float).sum() if not df_sales.empty else 0.0
    
    c1, c2, c3 = st.columns(3)
    c1.metric(lang["tot_prod"], len(df_inv))
    c2.metric(lang["stock"], tot_qty)
    c3.metric(lang["rev"], f"₹{tot_rev:,.2f}")

def inventory():
    st.title(lang["inv"])
    df_inv = fetch_inventory()
    
    with st.expander(lang["add_prod"]):
        with st.form("new_prod", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input(lang["p_name"])
            sku = c2.text_input(lang["sku"])
            price = c1.number_input(lang["price"], min_value=0.0)
            qty = c2.number_input(lang["qty"], min_value=0)
            img_file = st.file_uploader(lang["upload"], type=["png", "jpg", "jpeg"])
            
            if st.form_submit_button(lang["save"], type="primary") and name:
                # 🌟 RUN AUTO-COMPRESSION LOGIC TO PROTECT DATABASE FROM DROPPING 🌟
                img_compressed = get_compressed_base64_image(img_file)
                new_id = str(uuid.uuid4())[:8]
                
                # Fixed line 212 mapping error right here:
                db.table("inventory").insert({"id": new_id, "sku": sku, "name": name, "price": price, "quantity": qty, "image": img_compressed}).execute()
                st.success("✅ Added to Inventory Database!")
                st.rerun()

    st.subheader(lang["db"])
    if not df_inv.empty:
        updated_df = st.data_editor(
            df_inv, use_container_width=True, hide_index=True, num_rows="dynamic",
            column_config={"id": None, "image": st.column_config.ImageColumn("Preview")}
        )
        if st.button("Save Table Changes", type="primary"):
            for _, row in updated_df.iterrows():
                db.table("inventory").update({"sku": row['sku'], "name": row['name'], "price": row['price'], "quantity": row['quantity']}).eq("id", row['id']).execute()
            st.rerun()

def pos():
    st.title(lang["pos"])
    df_inv = fetch_inventory()
    if df_inv.empty: st.warning("Inventory empty. Populate tables inside dashboard first."); return

    col1, col2 = st.columns([2.2, 1])

    with col1:
        search = st.text_input(lang["search"])
        display_df = df_inv if not search else df_inv[df_inv['name'].str.contains(search, case=False) | df_inv['sku'].str.contains(search, case=False)]

        cols = st.columns(3)
        for idx, row in display_df.iterrows():
            with cols[idx % 3]:
                with st.container(border=True):
                    if pd.notna(row.get('image')) and row['image']: 
                        st.image(row['image'], use_container_width=True)
                    st.markdown(f"**{row['name']}**")
                    color = "#ef4444" if row['quantity'] <= st.session_state.low_stock_threshold else "gray"
                    st.markdown(f"<span style='color:{color}'>{lang['stock']}: {row['quantity']}</span>", unsafe_allow_html=True)
                    st.markdown(f"#### ₹{row['price']:,.2f}")
                    
                    qty = st.number_input("Q", 1, max(int(row['quantity']), 1), key=f"q_{row['id']}", label_visibility="collapsed")
                    if st.button(lang["add"], key=f"b_{row['id']}", type="primary", use_container_width=True):
                        if row['quantity'] >= qty:
                            item = next((i for i in st.session_state.cart if i["id"] == row["id"]), None)
                            if item:
                                item["quantity"] += qty; item["subtotal"] = item["price"] * item["quantity"]
                            else:
                                st.session_state.cart.append({"id": row["id"], "name": row["name"], "price": row["price"], "quantity": qty, "subtotal": row["price"] * qty})
                            st.rerun()

    with col2:
        with st.container(border=True):
            st.subheader(lang["cart"])
            if not st.session_state.cart: st.info(lang["empty"])
            else:
                subtotal = sum(i["subtotal"] for i in st.session_state.cart)
                for idx, item in enumerate(st.session_state.cart):
                    c_a, c_b, c_c = st.columns([3, 1.5, 1])
                    c_a.write(f"{item['quantity']}x {item['name']}")
                    c_b.write(f"₹{item['subtotal']:,.2f}")
                    if c_c.button("✖", key=f"rm_{idx}"): st.session_state.cart.pop(idx); st.rerun()
                
                st.divider()
                disc_pct = st.slider(f"{lang['disc']} (%)", 0, 100, 0)
                disc_amt = subtotal * (disc_pct / 100)
                tax_amt = (subtotal - disc_amt) * 0.05
                total = (subtotal - disc_amt) + tax_amt
                
                st.caption(f"{lang['sub']}: ₹{subtotal:,.2f} | {lang['tax']}: +₹{tax_amt:,.2f} | {lang['disc']}: -₹{disc_amt:,.2f}")
                st.markdown(f"### {lang['tot']}: ₹{total:,.2f}")
                cust = st.text_input(lang["cust"], "Walk-in")
                
                # --- BACKDATED TRANSACTION SELECTOR ---
                st.divider()
                st.markdown("##### 📅 Transaction Date & Time Adjustment")
                tx_date = st.date_input("Execution Date", datetime.now())
                tx_time = st.time_input("Execution Time", datetime.now().time())
                tx_combined = datetime.combine(tx_date, tx_time)
                d_str = tx_combined.strftime("%Y-%m-%d %H:%M")
                
                if st.button(lang["checkout"], type="primary", use_container_width=True):
                    s_id = str(uuid.uuid4())[:8].upper()
                    
                    for c_item in st.session_state.cart:
                        current_stock = df_inv[df_inv['id'] == c_item['id']]['quantity'].values[0]
                        db.table("inventory").update({"quantity": int(current_stock - c_item['quantity'])}).eq("id", c_item['id']).execute()
                    
                    db.table("sales").insert({"id": s_id, "customer": cust, "total": total, "date_str": d_str}).execute()

                    st.session_state.last_receipt = {
                        "id": s_id, "date": d_str, "cust": cust, "items": list(st.session_state.cart),
                        "sub": subtotal, "disc": disc_amt, "tax": tax_amt, "tot": total
                    }

                    if PDF_READY:
                        st.session_state['pdf'] = generate_pdf(s_id, d_str, cust, st.session_state.cart, subtotal, disc_amt, tax_amt, total)
                        st.session_state['pdf_name'] = f"Invoice_{s_id}.pdf"

                    st.session_state.cart.clear()
                    st.rerun()

        if st.session_state.last_receipt:
            r = st.session_state.last_receipt
            items_html = "".join([f"<div class='flex'><span>{i['quantity']}x {i['name'][:15]}</span><span>Rs. {i['subtotal']:,.2f}</span></div>" for i in r['items']])
            iframe_html = f"""
            <!DOCTYPE html><html><head><style>
                body {{ font-family: monospace; color: #000; padding: 10px; background: #fff; }}
                .container {{ border: 2px dashed #000; padding: 15px; max-width: 320px; margin: 0 auto; }}
                .print-btn {{ width: 100%; padding: 12px; background: #4F46E5; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; margin-top: 20px; }}
                .flex {{ display: flex; justify-content: space-between; }}
                .line {{ border-bottom: 1px dashed #000; margin: 10px 0; }}
                @media print {{ .print-btn {{ display: none !important; }} .container {{ border: none; }} }}
            </style></head><body>
                <div class="container">
                    <h3 style="text-align:center; margin-top:0;">TITAN CONVENIENCE & GROCERY</h3>
                    <div class="line"></div>
                    <div><b>Bill No:</b> {r['id']}</div><div><b>Date/Time:</b> {r['date']}</div><div><b>Customer:</b> {r['cust']}</div>
                    <div class="line"></div>{items_html}<div class="line"></div>
                    <div class="flex"><span>Subtotal:</span> <span>Rs. {r['sub']:,.2f}</span></div>
                    <div class="flex"><span>Discount:</span> <span>-Rs. {r['disc']:,.2f}</span></div>
                    <div class="flex"><span>Tax (5%):</span> <span>+Rs. {r['tax']:,.2f}</span></div>
                    <h3 class="flex" style="margin:4px 0 0 0;"><span>TOTAL:</span> <span>Rs. {r['tot']:,.2f}</span></h3>
                </div><button class="print-btn" onclick="window.print()">🖨️ Print Receipt</button>
            </body></html>"""
            
            st.success("✅ Transaction logged successfully!")
            c_left, c_right = st.columns([1, 1])
            with c_left: components.html(iframe_html, height=460, scrolling=True)
            with c_right:
                if 'pdf' in st.session_state:
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    st.download_button(lang["dl_pdf"], data=st.session_state['pdf'], file_name=st.session_state['pdf_name'], mime="application/pdf", type="primary", use_container_width=True)

def staff():
    st.title(lang["staff"])
    is_main_owner = st.session_state.current_user.get("is_main", False) or st.session_state.current_user.get("username") == "shanmukh"
    
    if is_main_owner:
        with st.expander("👑 Primary Administrative Privilege: Add Sub-Owners", expanded=True):
            with st.form("add_sub_owner", clear_on_submit=True):
                new_username = st.text_input("Assign Sub-Owner Username").strip().lower()
                new_password = st.text_input("Assign Sub-Owner Security Password", type="password")
                if st.form_submit_button("Grant Administrative Access", type="primary"):
                    if new_username and new_password:
                        db.table("users").insert({"username": new_username, "password_hash": new_password, "role": "Owner", "is_main": False}).execute()
                        st.success(f"Successfully configured Sub-Owner profile for '{new_username}'")
                    else: st.error("Fields cannot be left blank.")

    with st.form("new_staff", clear_on_submit=True):
        st.subheader("Register System Cashiers & Workers")
        c1, c2 = st.columns(2)
        name = c1.text_input(lang["staff_name"])
        role = c2.selectbox(lang["role"], ["Cashier", "Manager"])
        if st.form_submit_button(lang["add_staff"], type="primary") and name:
            db.table("staff_list").insert({"id": str(uuid.uuid4())[:8], "name": name, "role": role}).execute()
            st.rerun()
            
    res = db.table("staff_list").select("*").execute()
    if res.data: st.dataframe(pd.DataFrame(res.data), use_container_width=True, hide_index=True)

def analytics():
    st.title(lang["analytics"])
    df_sales = fetch_sales_count()
    if df_sales.empty: st.info("No sales logs found."); return
    
    df_sales['date_only'] = pd.to_datetime(df_sales['date_str']).dt.date
    st.bar_chart(df_sales.groupby('date_only')['total'].sum(), color="#4F46E5")
    st.download_button(lang["dl_csv"], data=df_sales.to_csv(index=False).encode('utf-8'), file_name='sales_report.csv', type="primary")

# -----------------------------
# 6. ENFORCED CLOUD AUTHENTICATION LAYER
# -----------------------------
if not DB_CONNECTED:
    st.error("🛑 CRITICAL SERVER ERROR: Application fails to connect to cloud services.")
    st.info(f"Diagnostic Error Output: {CONNECTION_ERROR}")
    st.warning("Ensure SUPABASE_URL and SUPABASE_KEY configurations match your Deployed App Secrets Framework.")
else:
    if not st.session_state["logged_in"]:
        st.markdown("<br><br><h2 style='text-align: center;'>🏬 Titan Inventory & POS System</h2>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 1, 1])
        with c2:
            with st.container(border=True):
                usr = st.text_input(lang["user"]).strip().lower()
                pwd = st.text_input(lang["pass"], type="password")
                if st.button(lang["login_btn"], type="primary", use_container_width=True):
                    res = db.table("users").select("*").eq("username", usr).execute()
                    if res.data and res.data[0]["password_hash"] == pwd:
                        st.session_state["logged_in"] = True
                        st.session_state["current_user"] = {"username": usr, "role": res.data[0]["role"], "is_main": res.data[0]["is_main"]}
                        st.rerun()
                    else: 
                        st.error("Access Denied: Invalid Credentials.")
    else:
        with st.sidebar:
            st.subheader("⚙️ Settings")
            new_lang = st.selectbox("🌐 Language", ["English", "Hindi", "Telugu"], index=["English", "Hindi", "Telugu"].index(st.session_state.lang))
            if new_lang != st.session_state.lang:
                st.session_state.lang = new_lang
                st.rerun()
                
            st.divider()
            role = st.session_state.current_user["role"]
            st.caption(f"👤 {st.session_state.current_user['username'].title()} ({role})")
            st.divider()
            
            # Button Navigation Blocks
            if st.button(lang["pos"], use_container_width=True, type="secondary"):
                st.session_state["current_page"] = "pos"
            if st.button(lang["inv"], use_container_width=True, type="secondary"):
                st.session_state["current_page"] = "inventory"
                
            if role in ["Owner", "Manager"]:
                if st.button(lang["dash"], use_container_width=True, type="secondary"):
                    st.session_state["current_page"] = "dashboard"
                if st.button(lang["staff"], use_container_width=True, type="secondary"):
                    st.session_state["current_page"] = "staff"
            if role == "Owner":
                if st.button(lang["analytics"], use_container_width=True, type="secondary"):
                    st.session_state["current_page"] = "analytics"
                    
            st.divider()
            if st.button(lang["logout"], use_container_width=True, type="primary"):
                st.session_state["logged_in"] = False
                st.rerun()

        # Dynamic Execution Frame Router
        pages = {"pos": pos, "inventory": inventory, "dashboard": dashboard, "staff": staff, "analytics": analytics}
        pages[st.session_state["current_page"]]()
