import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Positive Pay Pro: Audit Ready", layout="wide")

# --- INITIALIZE SESSION STATE ---
if 'decisions' not in st.session_state:
    st.session_state.decisions = {}
if 'notes' not in st.session_state:
    st.session_state.notes = {}

st.title("🛡️ Positive Pay: Image Verification & Audit")

# --- STEP 1: GENERATE MOCK FILES ---
with st.expander("🛠️ Demo Setup: Download Mock Files", expanded=True):
    st.write("Download these files to simulate the reconciliation process.")
    c1, c2 = st.columns(2)
    
    cust_data = pd.DataFrame([
        {"Check #": "9001", "Amount": 1200.00, "Payee": "Tech Supplies Inc"},
        {"Check #": "9002", "Amount": 450.50, "Payee": "Janitorial Services"},
    ])
    c1.download_button("1. Download Customer Register", cust_data.to_csv(index=False), "customer_register.csv")

    bank_data = pd.DataFrame([
        {"Check #": "9001", "Amount": 1200.00, "Payee": "Tech Supplies Inc"}, 
        {"Check #": "9002", "Amount": 4500.50, "Payee": "Janitorial Services"}, # AMT FRAUD
        {"Check #": "9003", "Amount": 300.00, "Payee": "Unknown Thief"}        # FORGERY
    ])
    c2.download_button("2. Download Bank Activity File", bank_data.to_csv(index=False), "bank_paid_file.csv")

st.divider()

# --- STEP 2: UPLOAD SECTION ---
col_a, col_b = st.columns(2)
with col_a:
    cust_file = st.file_uploader("Upload Customer Issued File", type="csv")
with col_b:
    bank_file = st.file_uploader("Upload Bank Activity File", type="csv")

# --- STEP 3: RECONCILIATION & IMAGE VIEWER ---
if cust_file and bank_file:
    df_cust = pd.read_csv(cust_file)
    df_bank = pd.read_csv(bank_file)
    
    df_cust['Check #'] = df_cust['Check #'].astype(str)
    df_bank['Check #'] = df_bank['Check #'].astype(str)

    st.subheader("🔍 Exception Processing")
    
    for _, bank_row in df_bank.iterrows():
        check_num = bank_row['Check #']
        match = df_cust[df_cust['Check #'] == check_num]
        
        item_id = f"recon_{check_num}"
        reason = ""
        is_exception = False

        if match.empty:
            is_exception = True
            reason = "FORGERY ALERT: Missing from Register"
        elif float(bank_row['Amount']) != float(match.iloc[0]['Amount']):
            is_exception = True
            reason = f"AMOUNT MISMATCH: Issued ${match.iloc[0]['Amount']}"

        if is_exception:
            with st.container(border=True):
                info_col, action_col = st.columns([3, 1])
                
                with info_col:
                    st.error(f"**Check #{check_num}** — {reason}")
                    st.write(f"Presented: **{bank_row['Payee']}** for **${bank_row['Amount']}**")
                    
                    # --- NOTE FIELD FOR EMAIL COPY/PASTE ---
                    st.session_state.notes[item_id] = st.text_area(
                        "Internal Research Notes (Paste Email/Slack logs here):", 
                        placeholder="e.g. Per email from Sarah in Accounts Payable, this check was voided and reissued.",
                        key=f"note_{item_id}",
                        height=100
                    )
                    
                    with st.expander("👁️ View Check Front & Back Images"):
                        img_front, img_back = st.columns(2)
                        with img_front:
                            st.image(f"https://placehold.co/600x250/fdfdfd/333?text=FRONT+#{check_num}%0A{bank_row['Payee']}%0A${bank_row['Amount']}", use_container_width=True)
                        with img_back:
                            st.image(f"https://placehold.co/600x250/eeeeee/666?text=BACK+#{check_num}", use_container_width=True)
                
                with action_col:
                    st.write("#### Action")
                    if item_id not in st.session_state.decisions:
                        if st.button("✅ Pay", key=f"pay_{item_id}", use_container_width=True):
                            st.session_state.decisions[item_id] = "PAID"
                            st.rerun()
                        if st.button("🚫 Return", key=f"ret_{item_id}", use_container_width=True):
                            st.session_state.decisions[item_id] = "RETURNED"
                            st.rerun()
                    else:
                        st.info(f"Decision: {st.session_state.decisions[item_id]}")
                        if st.session_state.notes.get(item_id):
                            st.caption(f"**Saved Note:** {st.session_state.notes[item_id]}")
        else:
            st.success(f"✅ Check #{check_num} verified.")

# --- STEP 4: AUDIT LOG ---
if st.session_state.decisions:
    st.divider()
    st.subheader("📜 Compliance Audit Trail")
    
    # Building a formatted audit trail including notes
    audit_data = []
    for k, v in st.session_state.decisions.items():
        check_num_log = k.split('_')[1]
        audit_data.append({
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Check #": check_num_log,
            "Action": v,
            "Research Notes": st.session_state.notes.get(k, "No notes provided")
        })
    
    st.dataframe(audit_data, use_container_width=True)
    
    if st.button("🔄 Reset Demo Session"):
        st.session_state.decisions = {}
        st.session_state.notes = {}
        st.rerun()