import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Fraud Control Center", layout="wide")

# --- INITIALIZE SESSION STATE ---
if 'ach_rules' not in st.session_state:
    st.session_state.ach_rules = pd.DataFrame([
        {"Vendor": "AWS Cloud", "Company ID": "98765", "Max Amount": 1500.00},
        {"Vendor": "Verizon", "Company ID": "54321", "Max Amount": 250.00}
    ])

if 'decisions' not in st.session_state:
    st.session_state.decisions = {}

st.title("🛡️ Fraud Control Center")

tab1, tab2 = st.tabs(["📋 Check Positive Pay", "📟 ACH Debit Filter"])

# ---------------------------------------------------------
# TAB 1: CHECK POSITIVE PAY
# ---------------------------------------------------------
with tab1:
    st.header("Check Exception Review")
    
    # --- MAIN PAGE SAMPLE DOWNLOAD ---
    with st.expander("🚀 New to the Demo? Start here", expanded=True):
        st.write("To simulate a business workflow, download our sample check register and then upload it below.")
        
        sample_data = pd.DataFrame([
            {"Check #": "5001", "Amount": 1000.00, "Payee": "Office Depot"},
            {"Check #": "5002", "Amount": 50.00, "Payee": "Local Cafe"},
        ])
        
        st.download_button(
            label="📥 Download Sample Check Register (CSV)",
            data=sample_data.to_csv(index=False),
            file_name="daily_checks_template.csv",
            mime="text/csv"
        )
    
    st.divider()
    
    # --- UPLOAD SECTION ---
    uploaded_file = st.file_uploader("Step 2: Upload your Register to compare against Bank activity", type="csv")

    # Stubbed data representing checks presented at the bank
    presented_checks = [
        {"Check #": "5001", "Amount": 1000.00, "Payee": "Office Depot"}, # Match
        {"Check #": "5002", "Amount": 500.00, "Payee": "Local Cafe"},    # Amount mismatch
        {"Check #": "5003", "Amount": 2400.00, "Payee": "Unknown LLC"}   # Not in register
    ]

    if uploaded_file:
        issued = pd.read_csv(uploaded_file)
        issued['Check #'] = issued['Check #'].astype(str)
        
        st.subheader("🚩 Detected Exceptions")
        
        for p in presented_checks:
            match = issued[issued['Check #'] == p['Check #']]
            
            reason = None
            if match.empty:
                reason = "Item not in Issue File (Possible Forgery)"
            elif float(match.iloc[0]['Amount']) != float(p['Amount']):
                reason = f"Amount Mismatch (Issued: ${match.iloc[0]['Amount']})"
            elif match.iloc[0]['Payee'].lower() != p['Payee'].lower():
                reason = f"Payee Mismatch (Issued: {match.iloc[0]['Payee']})"

            if reason:
                item_id = f"check_{p['Check #']}"
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    with c1:
                        st.error(f"**Check #{p['Check #']}**")
                        st.caption(f"Error: {reason}")
                    with c2:
                        st.write(f"**Payee:** {p['Payee']}")
                        st.write(f"**Presented Amount:** ${p['Amount']}")
                    with c3:
                        if item_id not in st.session_state.decisions:
                            if st.button("✅ Pay", key=f"pay_{item_id}"):
                                st.session_state.decisions[item_id] = "PAID"
                                st.rerun()
                            if st.button("🚫 Return", key=f"ret_{item_id}"):
                                st.session_state.decisions[item_id] = "RETURNED"
                                st.rerun()
                        else:
                            st.info(f"Status: {st.session_state.decisions[item_id]}")
    else:
        st.info("Use the download button above to get a file, then upload it here.")

# ---------------------------------------------------------
# TAB 2: ACH POSITIVE PAY
# ---------------------------------------------------------
with tab2:
    st.header("ACH Debit Review")
    
    incoming_ach = [
        {"Vendor": "Verizon", "ID": "54321", "Amount": 280.00},
        {"Vendor": "Suspicious Inc", "ID": "99999", "Amount": 500.00}
    ]

    for ach in incoming_ach:
        rule = st.session_state.ach_rules[st.session_state.ach_rules['Company ID'] == ach['ID']]
        
        ach_reason = None
        if rule.empty:
            ach_reason = "Unauthorized Vendor"
        elif ach['Amount'] > rule.iloc[0]['Max Amount']:
            ach_reason = f"Exceeds Limit (${rule.iloc[0]['Max Amount']})"

        if ach_reason:
            item_id = f"ach_{ach['ID']}"
            with st.container(border=True):
                col_a, col_b, col_c = st.columns([2, 2, 1])
                with col_a:
                    st.warning(f"**ACH: {ach['Vendor']}**")
                    st.caption(f"ID: {ach['ID']}")
                with col_b:
                    st.write(f"**Amount:** ${ach['Amount']}")
                    st.write(f"**Flag:** {ach_reason}")
                with col_c:
                    if item_id not in st.session_state.decisions:
                        if st.button("✅ Accept", key=f"acc_{item_id}"):
                            st.session_state.decisions[item_id] = "ACCEPTED"
                            st.rerun()
                        if st.button("🚫 Reject", key=f"rej_{item_id}"):
                            st.session_state.decisions[item_id] = "REJECTED"
                            st.rerun()
                    else:
                        st.info(f"Status: {st.session_state.decisions[item_id]}")

# ---------------------------------------------------------
# AUDIT LOG & RESET
# ---------------------------------------------------------
st.divider()
if st.session_state.decisions:
    st.subheader("📜 Session Audit Log")
    history = [{"Time": datetime.now().strftime("%H:%M"), "Item": k, "Decision": v} 
               for k, v in st.session_state.decisions.items()]
    st.table(history)
    
    if st.button("🔄 Clear All Decisions & Reset Demo"):
        st.session_state.decisions = {}
        st.rerun()
        