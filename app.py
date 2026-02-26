import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import plotly.express as px

# Konfigurasi Halaman
st.set_page_config(page_title="Audit Confirmation Tool", page_icon="⚖️", layout="wide")

# Custom CSS untuk mempercantik tampilan
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; background-color: #2e7d32; color: white; border-radius: 5px; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# Sidebar untuk Instruksi
with st.sidebar:
    st.title("📌 Instruksi")
    st.info("""
    1. Siapkan PDF Kontrak (CC/LS).
    2. Drop file ke kotak unggahan.
    3. Periksa data di tabel preview.
    4. Klik 'Download' untuk hasil Excel.
    """)
    st.image("https://www.streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.png", width=150)

st.title("⚖️ Project Name")
st.subheader("Subheader")

# 1. Kotak Drag & Drop (Uploader)
uploaded_files = st.file_uploader("Upload atau Drop PDF Kontrak di sini", type="pdf", accept_multiple_files=True)

if uploaded_files:
    results = []
    
    with st.spinner('Sedang memproses PDF...'):
        for uploaded_file in uploaded_files:
            with pdfplumber.open(uploaded_file) as pdf:
                page = pdf.pages[0]
                full_text = page.extract_text() or ""
                
                # Inisialisasi Data
                data = {
                    'File_Name': uploaded_file.name,
                    'Lease_Number': "N/A",
                    'Security_Deposit': 0.0,
                    'AR_Outstanding': 0.0,
                    'AF_Outstanding': 0.0,
                    'Contract_Date': "-"
                }

                # Ekstraksi Lease Number & Date
                ln = re.search(r'(\d\.\d{2}\.\d{2}\.\d{6,7})', full_text)
                if ln: data['Lease_Number'] = ln.group(1)
                
                cd = re.search(r'Contract Date\s*[:\s]*(\d{2}/\d{2}/\d{4})', full_text, re.I)
                if cd: data['Contract_Date'] = cd.group(1)

                # Ekstraksi Angka (Metode Koordinat Kanan)
                right_area = page.within_bbox((page.width * 0.5, 0, page.width, page.height))
                words = right_area.extract_words()
                # Ambil angka berformat money (1,234.00)
                money_vals = [w['text'].replace(',', '') for w in words if re.match(r'^\d{1,3}(?:,\d{3})*(?:\.\d{2})$', w['text'])]
                
                # Mapping berdasarkan urutan vertikal standar
                if len(money_vals) >= 3:
                    data['Security_Deposit'] = float(money_vals[0])
                    data['AR_Outstanding'] = float(money_vals[1])
                    data['AF_Outstanding'] = float(money_vals[2])
                
                results.append(data)

    df = pd.DataFrame(results)

    # 2. Baris Ringkasan (Metric Cards)
    m1, m2, m3 = st.columns(3)
    m1.metric("Total File", len(df))
    m2.metric("Total AR", f"Rp {df['AR_Outstanding'].sum():,.2f}")
    m3.metric("Total AF", f"Rp {df['AF_Outstanding'].sum():,.2f}")

    # 3. Preview Tabel Interaktif
    st.write("### Preview Data Konfirmasi")
    st.dataframe(df.style.format({
        'Security_Deposit': '{:,.2f}',
        'AR_Outstanding': '{:,.2f}',
        'AF_Outstanding': '{:,.2f}'
    }), use_container_width=True)

    # 4. Visualisasi untuk Auditor
    fig = px.bar(df, x='Lease_Number', y=['AR_Outstanding', 'AF_Outstanding'], 
                 title="Sebaran Saldo per Kontrak", barmode='group')
    st.plotly_chart(fig, use_container_width=True)

    # 5. Tombol Download Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Audit_Data')
    
    st.download_button(
        label="📥 Download Excel untuk Confirmation Letter",
        data=output.getvalue(),
        file_name="Data_Audit_Confirmation.xlsx",
        mime="application/vnd.ms-excel"
    )
else:

    st.warning("Silakan unggah file PDF untuk memulai.")
