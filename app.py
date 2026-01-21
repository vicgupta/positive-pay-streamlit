import streamlit as st
import pandas as pd
from datetime import datetime
import io

st.set_page_config(page_title="Fraud Control Center", layout="wide")

# --- INITIALIZE SESSION STATE ---
if 'decisions' not in st.session_state:
    st.session_state.decisions = {}
if 'notes' not in st.session_state:
    st.session_state.notes = {}

# --- HELPER: DATA GENERATOR ---
def get_mock_files():
    # Customer Register (The Truth)
    cust_csv = """Check #,Amount,Payee
1010,120.00,Vendor Alpha
1011,45.82,Service Beta
1012,5000.00,Equipment Gamma
1013,150.00,Repair Delta
1014,2300.00,Consulting Epsilon
2010,1000.00,ACME Corp
2011,500.00,Internal Revenue Service
2012,150.00,Staples
2013,2500.00,City of New York
2014,800.00,Delta Airlines
4010,0.00,VOID
4011,100.00,Old Vendor
4012,500.00,Stopped Payee
4013,25.00,Duplicate Test
4014,10.00,Small Payment
1001,500.00,Valid Match 1
1002,750.00,Valid Match 2
1003,1200.00,Valid Match 3
1004,30.00,Valid Match 4
1005,95.00,Valid Match 5"""

    # Bank Paid File (The Reality/Fraud)
    bank_csv = """Check #,Amount,Payee
1010,1200.00,Vendor Alpha
1011,45.28,Service Beta
1012,5000.80,Equipment Gamma
1013,750.00,Repair Delta
1014,3200.00,Consulting Epsilon
2010,1000.00,ACME Corporation
2011,500.00,John Doe
2012,150.00,Cash
2013,2500.00,City of New York Inc
2014,800.00,Deltas Air
3010,8500.00,Luxury Rentals LLC
3011,12.50,Local Gas Station
3012,1000.00,Payroll Service
3013,55.00,Generic Retailer
3014,15000.00,Wire Transfer Co
4010,50.00,Voided User
4011,100.00,Old Vendor
4012,500.00,Stopped Payee
4013,25.00,Duplicate Test
4014,100.00,Small Payment"""
    
    return cust_csv, bank_csv

# --- NAVIGATION ---
page = st.sidebar.radio("Navigation", ["🔍 Processing Dashboard"])

# --- PROCESSING LOGIC ---
def process_reconciliation(df_cust, df_bank):
    exceptions = []
    df_cust['Check #'] = df_cust['Check #'].astype(str)
    df_bank['Check #'] = df_bank['Check #'].astype(str)
    
    for _, bank_row in df_bank.iterrows():
        check_num = bank_row['Check #']
        match = df_cust[df_cust['Check #'] == check_num]
        
        reason = None
        if match.empty:
            reason = "FORGERY: Not in Register"
        elif float(bank_row['Amount']) != float(match.iloc[0]['Amount']):
            reason = f"AMT MISMATCH: (Issued ${match.iloc[0]['Amount']})"
        elif str(bank_row['Payee']).lower() != str(match.iloc[0]['Payee']).lower():
            reason = f"PAYEE MISMATCH: (Issued to {match.iloc[0]['Payee']})"
        
        if reason:
            exceptions.append({
                "Check #": check_num,
                "Payee": bank_row['Payee'],
                "Amount": bank_row['Amount'],
                "Reason": reason,
                "Status": st.session_state.decisions.get(f"recon_{check_num}", "PENDING")
            })
    return pd.DataFrame(exceptions)

# --- PAGE 1: PROCESSING DASHBOARD ---
if page == "🔍 Processing Dashboard":
    st.title("🛡️ Positive Pay: Image Verification")
    
    with st.expander("🛠️ Step 1: Download 20 Fraud Scenarios", expanded=True):
        st.write("Click both buttons to get the testing files containing varied fraud types.")
        cust_csv, bank_csv = get_mock_files()
        c1, c2 = st.columns(2)
        c1.download_button("📥 Download Customer Register", cust_csv, "customer_register.csv")
        c2.download_button("📥 Download Bank Activity", bank_csv, "bank_paid_file.csv")

    st.divider()
    col_a, col_b = st.columns(2)
    cust_file = col_a.file_uploader("Upload Customer Issued File", type="csv")
    bank_file = col_b.file_uploader("Upload Bank Activity File", type="csv")

    if cust_file and bank_file:
        df_cust = pd.read_csv(cust_file)
        df_bank = pd.read_csv(bank_file)
        df_exceptions = process_reconciliation(df_cust, df_bank)

        st.subheader(f"🔍 Found {len(df_exceptions)} Exceptions")
        
        for _, row in df_exceptions.iterrows():
            check_num = row['Check #']
            item_id = f"recon_{check_num}"
            
            with st.container(border=True):
                info_col, action_col = st.columns([3, 1])
                with info_col:
                    st.error(f"**Check #{check_num}** — {row['Reason']}")
                    st.write(f"Bank Data: **{row['Payee']}** for **${row['Amount']}**")
                    
                    st.session_state.notes[item_id] = st.text_area("Research/Email Notes:", key=f"note_{item_id}", height=70)
                    
                    with st.expander("👁️ View Check Images"):
                        i1, i2 = st.columns(2)
                        i1.image(f"https://placehold.co/600x200/f8f9fa/333?text=FRONT+#{check_num}%0A{row['Payee']}", use_container_width=True)
                        i2.image(f"https://placehold.co/600x200/e9ecef/666?text=BACK+#{check_num}", use_container_width=True)
                
                with action_col:
                    if item_id not in st.session_state.decisions:
                        if st.button("✅ Pay", key=f"pay_{item_id}", use_container_width=True):
                            st.session_state.decisions[item_id] = "PAID"; st.rerun()
                        if st.button("🚫 Return", key=f"ret_{item_id}", use_container_width=True):
                            st.session_state.decisions[item_id] = "RETURNED"; st.rerun()
                    else:
                        st.info(f"Decision: {st.session_state.decisions[item_id]}")

# --- PAGE 2: EXECUTIVE SUMMARY ---
else:
    st.title("📊 Executive Exception Summary")
    
    # Try to access previously uploaded files from session_state if available, 
    # but for simplicity in this demo, we ask the user to upload on Page 1 first.
    st.info("Ensure you have uploaded both files on the 'Processing Dashboard' to view the summary.")
    
    # This part would typically be wrapped in a more robust state management for real apps
    try:
        # Re-running logic for the summary
        cust_csv, bank_csv = get_mock_files()
        df_cust = pd.read_csv(io.StringIO(cust_csv))
        df_bank = pd.read_csv(io.StringIO(bank_csv))
        df_exceptions = process_reconciliation(df_cust, df_bank)

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Exceptions", len(df_exceptions))
        m2.metric("Fraud Exposure", f"${df_exceptions['Amount'].sum():,.2f}")
        pending = len(df_exceptions) - len(st.session_state.decisions)
        m3.metric("Pending Decisions", pending)

        st.divider()
        st.subheader("High-Level Review Table")
        
        # Display the list with notes
        summary_df = df_exceptions.copy()
        summary_df['User Notes'] = summary_df['Check #'].apply(lambda x: st.session_state.notes.get(f"recon_{x}", ""))
        
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
        
        if st.button("🔄 Reset Demo Session"):
            st.session_state.decisions = {}
            st.session_state.notes = {}
            st.rerun()
            
    except Exception as e:
        st.write("Waiting for data processing...")