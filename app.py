import streamlit as st
import pandas as pd
import uuid
import base64
from datetime import datetime
import streamlit.components.v1 as components

# --- SAFETY CHECK FOR PDF LIBRARY ---
try:
    from fpdf import FPDF
    PDF_READY = True
except ImportError:
    PDF_READY = False

st.set_page_config(page_title="MSME POS", page_icon="💳", layout="wide", initial_sidebar_state="expanded")

# -----------------------------
# 1. TRANSLATION DICTIONARY
# -----------------------------
T = {
    "English": {
        "dash": "📊 Dashboard", "inv": "📦 Inventory", "pos": "🛒 Point of Sale", 
        "staff": "👥 Staff", "analytics": "📈 Analytics", "logout": "🚪 Logout",
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
        "staff": "👥 स्टाफ", "analytics": "📈 एनालिटिक्स", "logout": "🚪 लॉग आउट",
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
        "staff": "👥 సిబ్బంది", "analytics": "📈 విశ్లేషణలు", "logout": "🚪 లాగ్ అవుట్",
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
# 2. SYSTEM INIT & FIXED CSS
# -----------------------------
def init_db():
    defaults = {
        "users": {"shanmukh": {"pass": "owner123", "role": "Owner"}, "staff": {"pass": "staff123", "role": "Staff"}},
        "logged_in": False, "current_user": None, "lang": "English", "low_stock_threshold": 5,
        "inventory": pd.DataFrame(columns=["id", "sku", "name", "price", "quantity", "image"]),
        "cart": [], "sales": [], "staff_list": [], "last_receipt": None
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

def get_base64_image(uploaded_file):
    if uploaded_file is not None:
        base64_str = base64.b64encode(uploaded_file.read()).decode()
        return f"data:{uploaded_file.type};base64,{base64_str}"
    return None

init_db()
lang = T[st.session_state.lang]

# Added rule to make Sidebar Navigation Font much larger
st.markdown("""
<style>
/* Core Backgrounds */
.stApp { background-color: #F8FAFC; }
[data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E2E8F0; }

/* 🌟 INCREASE NAVIGATION BAR FONT SIZE 🌟 */
[data-testid="stSidebar"] .stRadio label p {
    font-size: 1.3rem !important;
    font-weight: 600 !important;
    padding: 10px 0px;
    color: #1E293B !important;
}

/* Force Typography Visibility */
p, h1, h2, h3, h4, h5, h6, span, label, [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
    color: #1E293B !important;
}

/* Protect Primary Buttons */
.stButton>button[kind="primary"] p, .stButton>button[kind="primary"] span {
    color: #FFFFFF !important;
}

/* Styled Containers */
[data-testid="metric-container"] {
    background: #FFFFFF; border: 1px solid #E2E8F0; padding: 20px;
    border-radius: 12px; border-top: 4px solid #4F46E5;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
div[data-testid="stVerticalBlock"] > div[style*="border"] {
    background: #FFFFFF; border-color: #E2E8F0; border-radius: 10px; padding: 15px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

/* Inputs */
input { 
    color: #1E293B !important; 
    background-color: #FFFFFF !important; 
    border: 1px solid #CBD5E1 !important; 
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# 3. PROFESSIONAL PDF GENERATOR
# -----------------------------
def generate_pdf(sale_id, date_str, customer, cart, subtotal, discount, tax, total):
    if not PDF_READY: return None
    pdf = FPDF()
    pdf.add_page()
    
    pdf.rect(5, 5, 200, 287)
    
    pdf.set_font("Arial", 'B', 22)
    pdf.cell(190, 15, "SHANMUKH ENTERPRISES", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(190, 5, "Official Retail Invoice", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Arial", '', 10)
    pdf.cell(95, 6, f"Invoice No: {sale_id}", 0, 0)
    pdf.cell(95, 6, f"Date: {date_str}", 0, 1, 'R')
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
        if not clean_name: clean_name = "Retail Item"
        pdf.cell(90, 8, f" {clean_name}", 1, 0)
        pdf.cell(30, 8, str(item['quantity']), 1, 0, 'C')
        pdf.cell(70, 8, f"{item['subtotal']:,.2f} ", 1, 1, 'R')
        
    pdf.ln(5)
    
    pdf.set_font("Arial", '', 11)
    pdf.cell(120, 6, "", 0, 0); pdf.cell(35, 6, "Subtotal:", 0, 0, 'R'); pdf.cell(35, 6, f"{subtotal:,.2f} ", 0, 1, 'R')
    if discount > 0:
        pdf.cell(120, 6, "", 0, 0); pdf.cell(35, 6, "Discount:", 0, 0, 'R'); pdf.cell(35, 6, f"-{discount:,.2f} ", 0, 1, 'R')
    pdf.cell(120, 6, "", 0, 0); pdf.cell(35, 6, "Tax (5%):", 0, 0, 'R'); pdf.cell(35, 6, f"+{tax:,.2f} ", 0, 1, 'R')
    
    pdf.line(130, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(120, 8, "", 0, 0); pdf.cell(35, 8, "GRAND TOTAL:", 0, 0, 'R'); pdf.cell(35, 8, f"{total:,.2f} ", 0, 1, 'R')
    
    pdf.ln(15)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(190, 5, "Thank you for your business!", ln=True, align='C')
    pdf.cell(190, 5, "Authorized Signatory", ln=True, align='R')
    
    return bytes(pdf.output(dest='S'), 'latin-1')

# -----------------------------
# 4. PAGE LOGIC
# -----------------------------
def dashboard():
    st.title(lang["dash"])
    df_inv = st.session_state.inventory
    tot_qty = df_inv["quantity"].sum() if not df_inv.empty else 0
    tot_rev = sum(s["total"] for s in st.session_state.sales)
    
    c1, c2, c3 = st.columns(3)
    c1.metric(lang["tot_prod"], len(df_inv))
    c2.metric(lang["stock"], tot_qty)
    c3.metric(lang["rev"], f"₹{tot_rev:,.2f}")

def inventory():
    st.title(lang["inv"])
    with st.expander(lang["add_prod"]):
        with st.form("new_prod", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input(lang["p_name"])
            sku = c2.text_input(lang["sku"])
            price = c1.number_input(lang["price"], min_value=0.0)
            qty = c2.number_input(lang["qty"], min_value=0)
            img_file = st.file_uploader(lang["upload"], type=["png", "jpg", "jpeg"])
            
            if st.form_submit_button(lang["save"], type="primary") and name:
                img_b64 = get_base64_image(img_file)
                new_row = {"id": str(uuid.uuid4())[:8], "sku": sku, "name": name, "price": price, "quantity": qty, "image": img_b64}
                st.session_state.inventory = pd.concat([st.session_state.inventory, pd.DataFrame([new_row])], ignore_index=True)
                st.success("✅ Added!")
                st.rerun()

    st.subheader(lang["db"])
    if not st.session_state.inventory.empty:
        st.session_state.inventory = st.data_editor(
            st.session_state.inventory, use_container_width=True, hide_index=True, num_rows="dynamic",
            column_config={"id": None, "image": st.column_config.ImageColumn("Preview")}
        )

def pos():
    st.title(lang["pos"])
    df_inv = st.session_state.inventory
    if df_inv.empty: st.warning("Inventory empty."); return

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
                if st.button(lang["checkout"], type="primary", use_container_width=True):
                    s_id = str(uuid.uuid4())[:8].upper()
                    d_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    for c_item in st.session_state.cart:
                        idx = df_inv.index[df_inv['id'] == c_item['id']].tolist()[0]
                        st.session_state.inventory.at[idx, 'quantity'] -= c_item['quantity']

                    st.session_state.sales.append({"id": s_id, "customer": cust, "total": total, "date": d_str})
                    
                    st.session_state.last_receipt = {
                        "id": s_id, "date": d_str, "cust": cust, "items": list(st.session_state.cart),
                        "sub": subtotal, "disc": disc_amt, "tax": tax_amt, "tot": total
                    }

                    if PDF_READY:
                        pdf_file = generate_pdf(s_id, d_str, cust, st.session_state.cart, subtotal, disc_amt, tax_amt, total)
                        st.session_state['pdf'] = pdf_file
                        st.session_state['pdf_name'] = f"Invoice_{s_id}.pdf"

                    st.session_state.cart.clear()
                    st.rerun()

        # Render On-Screen Receipt inside an isolated iFrame so ONLY the receipt prints
        if st.session_state.last_receipt:
            r = st.session_state.last_receipt
            items_html = "".join([
                f"<div style='display:flex; justify-content:space-between; margin-bottom:4px;'>"
                f"<span>{i['quantity']}x {i['name'][:15]}</span>"
                f"<span>Rs. {i['subtotal']:,.2f}</span>"
                f"</div>" for i in r['items']
            ])
            
            # Isolated HTML document for perfect printing
            iframe_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                body {{ font-family: 'Courier New', Courier, monospace; color: #000; margin: 0; padding: 0; background: #fff; }}
                .receipt-container {{ border: 2px dashed #000; padding: 20px; max-width: 350px; margin: 0 auto; }}
                .print-btn {{ width: 100%; padding: 12px; background: #4F46E5; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; margin-top: 20px; }}
                .print-btn:hover {{ background: #4338ca; }}
                .flex {{ display: flex; justify-content: space-between; }}
                .line {{ border-bottom: 1px dashed #000; margin: 10px 0; }}
                @media print {{
                    .print-btn {{ display: none !important; }}
                    .receipt-container {{ border: none; padding: 0; margin: 0; max-width: 100%; }}
                }}
            </style>
            </head>
            <body>
                <div class="receipt-container">
                    <h3 style="text-align:center; margin-top:0;">SHANMUKH ENTERPRISES</h3>
                    <div class="line"></div>
                    <div><b>Bill No:</b> {r['id']}</div>
                    <div><b>Date:</b> {r['date']}</div>
                    <div><b>Customer:</b> {r['cust']}</div>
                    <div class="line"></div>
                    {items_html}
                    <div class="line"></div>
                    <div class="flex"><span>Subtotal:</span> <span>Rs. {r['sub']:,.2f}</span></div>
                    <div class="flex"><span>Discount:</span> <span>-Rs. {r['disc']:,.2f}</span></div>
                    <div class="flex"><span>Tax (5%):</span> <span>+Rs. {r['tax']:,.2f}</span></div>
                    <h3 class="flex" style="margin-bottom:0;"><span>TOTAL:</span> <span>Rs. {r['tot']:,.2f}</span></h3>
                    <div style="text-align:center; margin-top:15px; font-size:12px;">Thank you for your business!</div>
                </div>
                <button class="print-btn" onclick="window.print()">🖨️ Print Receipt</button>
            </body>
            </html>
            """
            
            st.success("✅ Sale processed successfully!")
            
            c_left, c_right = st.columns([1, 1])
            with c_left:
                st.markdown("### Print")
                # Using components.html completely isolates the print command
                components.html(iframe_html, height=500, scrolling=True)
            with c_right:
                st.markdown("### Download")
                if 'pdf' in st.session_state:
                    st.download_button(lang["dl_pdf"], data=st.session_state['pdf'], file_name=st.session_state['pdf_name'], mime="application/pdf", type="primary", use_container_width=True)

def staff():
    st.title(lang["staff"])
    with st.form("new_staff", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input(lang["staff_name"])
        role = c2.selectbox(lang["role"], ["Cashier", "Manager"])
        if st.form_submit_button(lang["add_staff"], type="primary") and name:
            st.session_state.staff_list.append({"id": str(uuid.uuid4())[:8], "name": name, "role": role})
            st.rerun()
    if st.session_state.staff_list: 
        st.dataframe(pd.DataFrame(st.session_state.staff_list), use_container_width=True, hide_index=True)

def analytics():
    st.title(lang["analytics"])
    if not st.session_state.sales: return
    df_s = pd.DataFrame(st.session_state.sales)
    df_s['date'] = pd.to_datetime(df_s['date']).dt.date
    st.bar_chart(df_s.groupby('date')['total'].sum(), color="#4F46E5")
    st.download_button(lang["dl_csv"], data=df_s.to_csv(index=False).encode('utf-8'), file_name='sales.csv', type="primary")

# -----------------------------
# 5. CORE ROUTING
# -----------------------------
if not st.session_state.logged_in:
    st.markdown("<br><br><h2 style='text-align: center;'>💳 MSME POS</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        with st.container(border=True):
            usr = st.text_input(lang["user"]).strip().lower()
            pwd = st.text_input(lang["pass"], type="password")
            if st.button(lang["login_btn"], type="primary", use_container_width=True):
                if usr in st.session_state.users and st.session_state.users[usr]["pass"] == pwd:
                    st.session_state.logged_in = True
                    st.session_state.current_user = {"username": usr, "role": st.session_state.users[usr]["role"]}
                    st.rerun()
                else: st.error("Error")
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
        
        menu_options = {lang["pos"]: pos, lang["inv"]: inventory}
        if role == "Owner" or role == "Manager":
            menu_options = {lang["dash"]: dashboard} | menu_options | {lang["staff"]: staff}
        if role == "Owner":
            menu_options[lang["analytics"]] = analytics

        choice = st.radio("Nav", list(menu_options.keys()), label_visibility="collapsed")
        st.divider()
        if st.button(lang["logout"], use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    menu_options[choice]()
