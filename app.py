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
        "dash": "📊 Dashboard Metrics", "inv": "📦 Inventory Management", "pos": "🛒 Point of Sale", 
        "staff": "👥 Staff & User Management", "analytics": "📈 Advanced Analytics", "logout": "Logout",
        "login_btn": "Login", "user": "Username", "pass": "Password",
        "tot_prod": "Unique Items", "stock": "Total Items Stocked", "rev": "Net Gross Revenue",
        "add_prod": "➕ Register New Product", "p_name": "Product Name", "sku": "SKU / Barcode",
        "price": "Price (₹)", "qty": "Quantity", "upload": "📷 Upload Product Photo", "save": "Save to Database",
        "db": "📋 Live Database (Edit text directly or change images below)", "search": "🔍 Type Shortcode / Product Name...",
        "add": "Add", "cart": "🧾 Current Cart", "empty": "Cart is Empty",
        "sub": "Subtotal", "disc": "Discount", "tax": "Tax", "tot": "Total",
        "cust": "Customer Name", "checkout": "💳 Checkout & Generate Bill", "dl_pdf": "📄 Download PDF Bill",
        "staff_name": "Full Name", "role": "Role", "add_staff": "Add Staff Member", "dl_csv": "📥 Export CSV"
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

lang = T["English"]

# 🌟 CUSTOM PURPLE-BLUE BACKGROUND & REGULAR UNIFORM CARD UI STYLING 🌟
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #E0E7FF 0%, #EDE9FE 100%) !important;
    color: #1E293B !important;
}

h1, h2, h3, .stApp h1, .stApp h2, .stApp h3, [data-testid="stMetricLabel"] {
    color: #DC2626 !important; 
    font-weight: 700 !important;
}

.stApp p, .stApp span, label { 
    color: #1E293B !important; 
}

button[kind="primary"] {
    background-color: #DC2626 !important; 
    color: #FFFFFF !important;
    border: none !important;
    font-weight: bold !important;
}
button[kind="primary"]:hover {
    background-color: #991B1B !important;
}

button[kind="secondary"] {
    background-color: #FFFFFF !important;
    color: #4338CA !important; 
    border: 1px solid #C7D2FE !important;
}

[data-testid="metric-container"] { 
    background: #FFFFFF !important; 
    border: 1px solid #E2E8F0 !important; 
    padding: 20px !important; 
    border-radius: 12px !important; 
    border-top: 4px solid #DC2626 !important;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05) !important;
}

div[data-baseweb="input"] input, .stNumberInput input, .stTextInput input {
    background-color: #FFFFFF !important;
    color: #1E293B !important;
    border: 1px solid #CBD5E1 !important;
}

/* 🚀 ENFORCE UNIFORM CARD CONTAINER DIMENSIONS AND GRID SYMMETRY 🚀 */
.uniform-card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 16px;
    height: 340px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    margin-bottom: 20px;
}

.product-card-img { 
    border-radius: 8px; 
    height: 130px; 
    object-fit: cover; 
    width: 100%; 
    margin-bottom: 8px;
}

.card-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #1E293B;
    line-height: 1.3;
    height: 42px;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
}
</style>
""", unsafe_allow_html=True)

def fetch_inventory():
    res = db.table("inventory").select("*").order("name").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["id", "sku", "name", "price", "quantity", "image"])

def fetch_sales_count():
    res = db.table("sales").select("*").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["id", "customer", "total", "date_str"])

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

# -----------------------------
# 4. INVOICE GENERATOR
# -----------------------------
def generate_pdf(sale_id, date_str, customer, cart, subtotal, discount, tax, total):
    if not PDF_READY: return None
    pdf = FPDF()
    pdf.add_page(); pdf.rect(5, 5, 200, 287)
    pdf.set_font("Arial", 'B', 18); pdf.cell(190, 15, "TITAN CONVENIENCE AND GROCERY", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10); pdf.cell(190, 5, "Official Retail Transaction Invoice", ln=True, align='C'); pdf.ln(5)
    pdf.set_font("Arial", '', 10)
    pdf.cell(95, 6, f"Invoice No: {sale_id}", 0, 0); pdf.cell(95, 6, f"Date/Time: {date_str}", 0, 1, 'R')
    pdf.cell(190, 6, f"Customer: {customer}", 0, 1); pdf.line(10, 45, 200, 45); pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(90, 8, "Item Description", 1, 0, 'C'); pdf.cell(30, 8, "Qty", 1, 0, 'C'); pdf.cell(70, 8, "Amount (Rs)", 1, 1, 'C')
    
    pdf.set_font("Arial", '', 10)
    for item in cart:
        clean_name = item['name'].encode('ascii', 'ignore').decode('ascii')[:30]
        pdf.cell(90, 8, f" {clean_name if clean_name else 'Grocery Item'}", 1, 0)
        pdf.cell(30, 8, str(item['quantity']), 1, 0, 'C')
        pdf.cell(70, 8, f"{item['subtotal']:,.2f} ", 1, 1, 'R')
        
    pdf.ln(5)
    pdf.cell(120, 6, "", 0, 0); pdf.cell(35, 6, "Subtotal:", 0, 0, 'R'); pdf.cell(35, 6, f"{subtotal:,.2f} ", 0, 1, 'R')
    if discount > 0:
        pdf.cell(120, 6, "", 0, 0); pdf.cell(35, 6, "Discount:", 0, 0, 'R'); pdf.cell(35, 6, f"-{discount:,.2f} ", 0, 1, 'R')
    pdf.cell(120, 6, "", 0, 0); pdf.cell(35, 6, "Tax (5%):", 0, 0, 'R'); pdf.cell(35, 6, f"+{tax:,.2f} ", 0, 1, 'R')
    pdf.line(130, pdf.get_y(), 200, pdf.get_y()); pdf.ln(2); pdf.set_font("Arial", 'B', 14)
    pdf.cell(120, 8, "", 0, 0); pdf.cell(35, 8, "GRAND TOTAL:", 0, 0, 'R'); pdf.cell(35, 8, f"{total:,.2f} ", 0, 1, 'R')
    return bytes(pdf.output(dest='S'), 'latin-1')

# -----------------------------
# 5. CORE INTERFACE PAGES
# -----------------------------
def dashboard():
    st.title("📊 Executive Operational Dashboard")
    df_inv = fetch_inventory()
    df_sales = fetch_sales_count()
    
    tot_sku = len(df_inv)
    tot_items = int(df_inv["quantity"].sum()) if not df_inv.empty else 0
    tot_rev = df_sales["total"].astype(float).sum() if not df_sales.empty else 0.0
    total_tx = len(df_sales)
    avg_ticket = tot_rev / total_tx if total_tx > 0 else 0.0
    
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Net Gross Revenue", f"₹{tot_rev:,.2f}")
    c2.metric("Total Transactions Logged", f"{total_tx} Orders")
    c3.metric("Average Ticket Value", f"₹{avg_ticket:,.2f}")
    c4.metric("Live Catalog SKUs", f"{tot_sku} Items")
    
    st.markdown("---")
    
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.subheader("📆 Live Sales Pipeline Tracking")
        if not df_sales.empty:
            df_chart = df_sales.copy()
            df_chart['date_only'] = pd.to_datetime(df_chart['date_str']).dt.date
            daily_rev = df_chart.groupby('date_only')['total'].sum().reset_index()
            daily_rev.columns = ['Date', 'Revenue (₹)']
            st.line_chart(daily_rev.set_index('Date'), color="#DC2626")
        else: st.info("No pipeline logs parsed.")
        
    with col_b:
        st.subheader("⚠️ Critical Low Stock Warnings")
        low_stock = df_inv[df_inv["quantity"] <= st.session_state["low_stock_threshold"]]
        if not low_stock.empty:
            for _, item in low_stock.iterrows():
                st.error(f"🔴 **{item['name']}** - Only {item['quantity']} units left! (ID: {item['id']})")
        else: st.success("🍏 All parameters normal. Stock levels fully satisfied.")

def inventory():
    st.title("📦 Comprehensive Catalog Registry")
    df_inv = fetch_inventory()
    
    with st.expander(lang["add_prod"]):
        with st.form("new_prod", clear_on_submit=True):
            c_id, c_name = st.columns([1, 2])
            p_custom_id = c_id.text_input("Product ID Shortcode (e.g., coke, lays-m)").strip().lower()
            name = c_name.text_input(lang["p_name"])
            
            c1, c2 = st.columns(2)
            sku = c1.text_input(lang["sku"])
            price = c1.number_input(lang["price"], min_value=0.0)
            qty = c2.number_input(lang["qty"], min_value=0)
            img_file = st.file_uploader(lang["upload"], type=["png", "jpg", "jpeg"])
            
            if st.form_submit_button(lang["save"], type="primary") and name:
                final_id = p_custom_id if p_custom_id else str(uuid.uuid4())[:6]
                img_compressed = get_compressed_base64_image(img_file)
                
                try:
                    db.table("inventory").insert({"id": final_id, "sku": sku, "name": name, "price": price, "quantity": qty, "image": img_compressed}).execute()
                    st.success(f"✅ Added to Inventory Database with ID: {final_id}")
                except Exception:
                    db.table("inventory").insert({"id": final_id, "sku": sku, "name": name, "price": price, "quantity": qty, "image": None}).execute()
                    st.success(f"✅ Added text record with ID: {final_id}")
                st.rerun()

    st.subheader(lang["db"])
    if not df_inv.empty:
        cols_display = ["id", "sku", "name", "price", "quantity", "image"]
        updated_df = st.data_editor(
            df_inv[cols_display], use_container_width=True, hide_index=True, num_rows="dynamic",
            column_config={
                "id": st.column_config.TextColumn("Product ID / Shortcode", required=True),
                "image": st.column_config.ImageColumn("Preview")
            }
        )
        
        st.markdown("---")
        st.markdown("### 📷 Select Product to Inject/Replace Image")
        target_product = st.selectbox("Choose Item to Modify", df_inv["name"].tolist())
        target_file = st.file_uploader("Upload New Image Payload", type=["png", "jpg", "jpeg"], key="bulk_inject")
        
        c_save, c_sync = st.columns([1, 4])
        if c_save.button("🚀 Push Image to Cloud", type="primary") and target_file:
            new_img_str = get_compressed_base64_image(target_file)
            target_id = df_inv[df_inv["name"] == target_product]["id"].values[0]
            db.table("inventory").update({"image": new_img_str}).eq("id", target_id).execute()
            st.success("Image compiled and successfully synced!")
            st.rerun()
            
        if c_sync.button("💾 Sync Table Text Modifications Only"):
            for _, row in updated_df.iterrows():
                db.table("inventory").update({"sku": row['sku'], "name": row['name'], "price": row['price'], "quantity": row['quantity']}).eq("id", row['id']).execute()
            st.rerun()

def pos():
    st.title("🛒 Transaction Terminal (POS)")
    df_inv = fetch_inventory()
    if df_inv.empty: st.warning("Inventory empty. Populate tables inside dashboard first."); return

    col1, col2 = st.columns([2.0, 1.2])
    with col1:
        # 🌟 REAL-TIME AS-YOU-TYPE FILTER ENGAGEMENT 🌟
        search = st.text_input(lang["search"], value="", autocomplete="off")
        display_df = df_inv if not search else df_inv[
            df_inv['name'].str.contains(search, case=False) | 
            df_inv['sku'].str.contains(search, case=False) |
            df_inv['id'].str.contains(search, case=False)
        ]

        cols = st.columns(3)
        for idx, row in display_df.reset_index(drop=True).iterrows():
            with cols[idx % 3]:
                # Custom uniform HTML block structure configuration wrapper
                st.markdown('<div class="uniform-card">', unsafe_allow_html=True)
                
                if pd.notna(row.get('image')) and row['image']: 
                    st.image(row['image'], use_container_width=True)
                else:
                    st.markdown('<div style="height:130px; background:#F1F5F9; border-radius:8px; display:flex; align-items:center; justify-content:center; color:#94A3B8;">No Image</div>', unsafe_allow_html=True)
                
                st.markdown(f'<div class="card-title">{row["name"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<span style="font-size:0.85rem; color:#64748B;">ID Code: <code>{row["id"]}</code></span>', unsafe_allow_html=True)
                
                color = "#ef4444" if row['quantity'] <= st.session_state.low_stock_threshold else "#475569"
                st.markdown(f'<div style="font-size:0.9rem; margin-top:2px; color:{color}; font-weight:600;">Stock: {row["quantity"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="font-size:1.25rem; font-weight:700; color:#DC2626; margin-bottom:8px;">₹{row["price"]:,.2f}</div>', unsafe_allow_html=True)
                
                qty = st.number_input("Quantity Selector", 1, max(int(row['quantity']), 1), key=f"q_{row['id']}", label_visibility="collapsed")
                if st.button(lang["add"], key=f"b_{row['id']}", type="primary", use_container_width=True):
                    if row['quantity'] >= qty:
                        item = next((i for i in st.session_state.cart if i["id"] == row["id"]), None)
                        if item:
                            item["quantity"] += qty; item["subtotal"] = item["price"] * item["quantity"]
                        else:
                            st.session_state.cart.append({"id": row["id"], "name": row["name"], "price": row["price"], "quantity": qty, "subtotal": row["price"] * qty})
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)

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
                
                st.divider()
                st.markdown("##### 📅 Transaction Date & Time Adjustment")
                tx_date = st.date_input("Execution Date", datetime.now())
                tx_time = st.time_input("Execution Time", datetime.now().time())
                d_str = datetime.combine(tx_date, tx_time).strftime("%Y-%m-%d %H:%M")
                
                if st.button(lang["checkout"], type="primary", use_container_width=True):
                    s_id = str(uuid.uuid4())[:8].upper()
                    for c_item in st.session_state.cart:
                        current_stock = df_inv[df_inv['id'] == c_item['id']]['quantity'].values[0]
                        db.table("inventory").update({"quantity": int(current_stock - c_item['quantity'])}).eq("id", c_item['id']).execute()
                    
                    db.table("sales").insert({"id": s_id, "customer": cust, "total": total, "date_str": d_str}).execute()
                    st.session_state.last_receipt = {"id": s_id, "date": d_str, "cust": cust, "items": list(st.session_state.cart), "sub": subtotal, "disc": disc_amt, "tax": tax_amt, "tot": total}
                    if PDF_READY:
                        st.session_state['pdf'] = generate_pdf(s_id, d_str, cust, st.session_state.cart, subtotal, disc_amt, tax_amt, total)
                        st.session_state['pdf_name'] = f"Invoice_{s_id}.pdf"
                    st.session_state.cart.clear(); st.rerun()

        if st.session_state.last_receipt:
            r = st.session_state.last_receipt
            items_html = "".join([f"<div class='flex'><span>{i['quantity']}x {i['name'][:20]}</span><span>Rs. {i['subtotal']:,.2f}</span></div>" for i in r['items']])
            
            iframe_html = f"""
            <!DOCTYPE html><html><head><style>
                body {{ font-family: monospace; color: #1E293B; padding: 15px; background: #fff; margin: 0; }}
                .container {{ border: 2px dashed #94A3B8; padding: 30px; max-width: 520px; margin: 0 auto; border-radius: 8px; }}
                .print-btn {{ width: 100%; padding: 14px; background: #DC2626; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; margin-top: 25px; }}
                .flex {{ display: flex; justify-content: space-between; font-size: 15px; margin: 4px 0; }}
                .line {{ border-bottom: 2px dashed #94A3B8; margin: 15px 0; }}
                @media print {{ .print-btn {{ display: none !important; }} .container {{ border: none; }} }}
            </style></head><body>
                <div class="container">
                    <h2 style="text-align:center; margin-top:0; letter-spacing: 1px;">TITAN CONVENIENCE & GROCERY</h2>
                    <div class="line"></div>
                    <div class="flex"><span><b>Bill No:</b> {r['id']}</span></div>
                    <div class="flex"><span><b>Date/Time:</b> {r['date']}</span></div>
                    <div class="flex"><span><b>Customer:</b> {r['cust']}</span></div>
                    <div class="line"></div>
                    <div style="font-weight: bold; margin-bottom: 8px;" class="flex"><span>Item Allocation</span><span>Subtotal</span></div>
                    {items_html}
                    <div class="line"></div>
                    <div class="flex"><span>Subtotal:</span> <span>Rs. {r['sub']:,.2f}</span></div>
                    <div class="flex"><span>Discount:</span> <span>-Rs. {r['disc']:,.2f}</span></div>
                    <div class="flex"><span>Tax (5%):</span> <span>+Rs. {r['tax']:,.2f}</span></div>
                    <div class="line"></div>
                    <h2 class="flex" style="margin:0; padding-top: 5px;"><span>TOTAL DUED:</span> <span>Rs. {r['tot']:,.2f}</span></h2>
                </div><button class="print-btn" onclick="window.print()">🖨️ Execute Print Routing</button>
            </body></html>"""
            
            st.success("✅ Transaction logged successfully!")
            st.markdown("### 🧾 System Transaction Receipt")
            st.markdown('<div style="display: flex; justify-content: center; width: 100%; background: #F1F5F9; padding: 20px; border-radius: 12px; margin-bottom: 15px;">', unsafe_allow_html=True)
            components.html(iframe_html, height=560, width=560, scrolling=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            if 'pdf' in st.session_state:
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
    st.title("📈 Advanced Performance Analytics")
    df_sales = fetch_sales_count()
    if df_sales.empty: st.info("No transaction telemetry caught."); return
    
    df_sales['datetime'] = pd.to_datetime(df_sales['date_str'])
    df_sales['date_only'] = df_sales['datetime'].dt.date
    df_sales['hour'] = df_sales['datetime'].dt.hour
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📅 Gross Revenue Progression")
        daily_perf = df_sales.groupby('date_only')['total'].sum().reset_index()
        daily_perf.columns = ['Date', 'Sales (₹)']
        st.bar_chart(daily_perf.set_index('Date'), color="#DC2626")
        
    with c2:
        st.subheader("⏰ Traffic Density Peak Distribution Hours")
        hourly_perf = df_sales.groupby('hour')['total'].count().reset_index()
        hourly_perf.columns = ['Hour of Day', 'Total Orders Placed']
        st.line_chart(hourly_perf.set_index('Hour of Day'), color="#10B981")
        
    st.markdown("---")
    st.subheader("📜 Complete Historical Ledger Audits")
    st.dataframe(df_sales[['id', 'customer', 'total', 'date_str']], use_container_width=True, hide_index=True)
    st.download_button(lang["dl_csv"], data=df_sales.to_csv(index=False).encode('utf-8'), file_name='sales_report.csv', type="primary")

# -----------------------------
# 6. ENFORCED CLOUD AUTHENTICATION LAYER
# -----------------------------
if not DB_CONNECTED:
    st.error("🛑 CRITICAL SERVER ERROR: Application fails to connect to cloud services.")
    st.info(f"Diagnostic Error Output: {CONNECTION_ERROR}")
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
                    else: st.error("Access Denied: Invalid Credentials.")
    else:
        with st.sidebar:
            # 🌟 INTERCHANGED POSITION: LANGUAGE SELECTOR PLACED AT THE ABSOLUTE TOP 🌟
            new_lang = st.selectbox("🌐 Language Selection Block", ["English"], index=0, label_visibility="collapsed")
            st.divider()
            
            role = st.session_state.current_user["role"]
            st.caption(f"👤 {st.session_state.current_user['username'].title()} ({role})")
            st.divider()
            
            # Application Nav Controllers
            if st.button(lang["pos"], use_container_width=True, type="secondary"): st.session_state["current_page"] = "pos"
            if st.button(lang["inv"], use_container_width=True, type="secondary"): st.session_state["current_page"] = "inventory"
            if role in ["Owner", "Manager"]:
                if st.button(lang["dash"], use_container_width=True, type="secondary"): st.session_state["current_page"] = "dashboard"
                if st.button(lang["staff"], use_container_width=True, type="secondary"): st.session_state["current_page"] = "staff"
            if role == "Owner":
                if st.button(lang["analytics"], use_container_width=True, type="secondary"): st.session_state["current_page"] = "analytics"
                    
            st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
            st.divider()
            
            # 🌟 CLEANUP FIX: LOGOUT PINNED AT THE BOTTOM, DOOR EMOJI OBLITERATED 🌟
            if st.button(lang["logout"], use_container_width=True, type="primary"):
                st.session_state["logged_in"] = False; st.rerun()

        pages = {"pos": pos, "inventory": inventory, "dashboard": dashboard, "staff": staff, "analytics": analytics}
        pages[st.session_state["current_page"]]()
