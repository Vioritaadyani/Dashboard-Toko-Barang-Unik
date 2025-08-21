import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from io import BytesIO
import numpy as np

# CONFIGURASI HALAMAN
st.set_page_config(page_title="Dashboard Penjualan", layout="wide", page_icon="📊")

# CUSTOM CSS UNTUK TAMPILAN DASHBOARD
st.markdown("""
    <style>
    body {
        background: linear-gradient(135deg, #e0f7fa 0%, #f1f8e9 100%);
        color: #333333;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .block-container {
        padding: 2rem 4rem;
        background: rgba(255, 255, 255, 0.9);
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.05);
    }
    h1 {
        color: #1976d2;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    .stMetric {
        background: linear-gradient(135deg, #ffffff, #f0f0f0);
        border-radius: 16px;
        padding: 1.5rem !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #e0e0e0;
    }
    hr {
        border: none;
        height: 2px;
        background: #1976d2;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# SIDEBAR: UPLOAD MULTIPLE CSV
uploaded_files = st.sidebar.file_uploader("📁 Upload File CSV", type=['csv'], accept_multiple_files=True)

if uploaded_files:
    # Buat list nama file
    file_names = [file.name for file in uploaded_files]

    # Pilih file yang mau ditampilkan
    selected_file_name = st.sidebar.selectbox("Pilih Dataset", file_names)

    # Ambil file sesuai pilihan
    selected_file = next(file for file in uploaded_files if file.name == selected_file_name)

    # Membaca CSV ke DataFrame
    df = pd.read_csv(selected_file)

    # Menambahkan kolom Total Penjualan 
    df['Total Penjualan (Juta)'] = df['Total Penjualan (Pesanan Dibuat) (IDR)'] / 1_000_000

    # KMeans Clustering 
    X = df[['Total Pembeli (Pesanan Dibuat)', 'Produk (Pesanan Dibuat)']]
    kmeans = KMeans(n_clusters=3, random_state=42)
    df['Cluster'] = kmeans.fit_predict(X)
    centroids = kmeans.cluster_centers_

    # Urutan cluster berdasarkan rata-rata penjualan (dari kecil ke besar)
    cluster_avg = df.groupby('Cluster')['Total Penjualan (Juta)'].mean().sort_values().index.tolist()
    
    # Mapping cluster ke kategori label
    final_map = {}
    for idx, label in zip(cluster_avg, ['Kurang Laris', 'Laris', 'Sangat Laris']):
        final_map[idx] = label
    df['Kategori'] = df['Cluster'].map(final_map)

    # SIDEBAR: FILTER DATA
    st.sidebar.markdown("## 🔍 Filter Data")
    kategori_filter = st.sidebar.multiselect("Pilih Kategori", options=df['Kategori'].unique(), default=df['Kategori'].unique())

    min_pembeli, max_pembeli = int(df['Total Pembeli (Pesanan Dibuat)'].min()), int(df['Total Pembeli (Pesanan Dibuat)'].max())
    pembeli_range = st.sidebar.slider("Jumlah Pembeli", min_value=min_pembeli, max_value=max_pembeli, value=(min_pembeli, max_pembeli))

    min_penjualan, max_penjualan = float(df['Total Penjualan (Juta)'].min()), float(df['Total Penjualan (Juta)'].max())
    penjualan_range = st.sidebar.slider("Total Penjualan (Juta)", min_value=min_penjualan, max_value=max_penjualan, value=(min_penjualan, max_penjualan))

    # Filter data
    df = df[
        (df['Kategori'].isin(kategori_filter)) &
        (df['Total Pembeli (Pesanan Dibuat)'].between(*pembeli_range)) &
        (df['Total Penjualan (Juta)'].between(*penjualan_range))
    ]

    # Rekomendasi strategi
    def rekomendasi(row):
        if row['Kategori'] == 'Sangat Laris':
            return "Pertahankan stok & promosi rutin"
        elif row['Kategori'] == 'Laris':
            return "Tingkatkan promosi jadi sangat laris"
        else:
            return "Evaluasi produk/buat bundling"
    df['Rekomendasi Strategi'] = df.apply(rekomendasi, axis=1)

    st.markdown(f"""
    <h1 style='text-align: center;'>📊 Dashboard Analisis Penjualan<br>{selected_file_name}</h1>
    <hr>
    """, unsafe_allow_html=True)

    # METRIK
    total_penjualan = df['Total Penjualan (Pesanan Dibuat) (IDR)'].sum()
    total_produk = df['Produk (Pesanan Dibuat)'].sum()
    total_data = len(df)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Penjualan", f"Rp{total_penjualan:,.0f}")
    col2.metric("Total Produk Terjual", f"{int(total_produk):,} pcs")
    col3.metric("Jumlah Data Produk", f"{total_data} item")

    # VISUALISASI TOP 10 PRODUK TERLARIS
    top_produk = df.sort_values(by='Produk (Pesanan Dibuat)', ascending=False).head(10)
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    sns.barplot(x='Produk (Pesanan Dibuat)', y='Produk', data=top_produk, palette="viridis", ax=ax1)
    ax1.set_title("Top 10 Produk Terlaris")
    col4, col5 = st.columns([2, 1])
    col4.pyplot(fig1)

    # PIE DISTRIBUSI KATEGORI
    kategori_counts = df['Kategori'].value_counts()
    fig2, ax2 = plt.subplots()
    ax2.pie(kategori_counts, labels=kategori_counts.index, autopct='%1.1f%%', startangle=140,
            colors=sns.color_palette("pastel"))
    ax2.axis('equal')
    ax2.set_title("Distribusi Kategori Produk")
    col5.pyplot(fig2)

    # VISUALISASI DIAGRAM BATANG MIRIP CONTOH GAMBAR
    # Pastikan sudah ada kolom Tahun & Bulan
    import re
    match = re.search(r'bulan_(\d+)_(\d+)', selected_file_name)
    if match:
        bulan_num = int(match.group(1))
        tahun_num = int(match.group(2))
        bulan_map = {
            1: "January", 2: "February", 3: "March", 4: "April",
            5: "May", 6: "June", 7: "July", 8: "August",
            9: "September", 10: "October", 11: "November", 12: "December"
        }
        df['Tahun'] = tahun_num
        df['Bulan'] = bulan_map.get(bulan_num, f"Bulan {bulan_num}")

    # Buat ringkasan per bulan & tahun
    monthly_summary = df.groupby(['Bulan', 'Tahun'])['Total Pembeli (Pesanan Dibuat)'].sum().reset_index()

    fig3, ax3 = plt.subplots(figsize=(8, 6))
    sns.barplot(x='Bulan', y='Total Pembeli (Pesanan Dibuat)', hue='Tahun', data=monthly_summary, palette='tab10', ax=ax3)
    ax3.set_title("Total Pesanan per Bulan per Tahun")
    ax3.set_xlabel("Bulan")
    ax3.set_ylabel("Total Pesanan")

    # KONTRIBUSI PENJUALAN
    cluster_penjualan = df.groupby('Kategori')['Total Penjualan (Juta)'].sum().sort_values(ascending=False)
    fig4, ax4 = plt.subplots(figsize=(6, 4))
    sns.barplot(x=cluster_penjualan.values, y=cluster_penjualan.index, palette="Blues_d", ax=ax4)
    ax4.set_title("Kontribusi Penjualan per Kategori")

    col6, col7 = st.columns(2)
    col6.pyplot(fig3)
    col7.pyplot(fig4)

    # TABEL REKOMENDASI
    st.subheader("📌 Rekomendasi Strategi Bisnis per Produk")
    st.dataframe(df[['Produk', 'Kategori', 'Total Penjualan (Juta)', 'Total Pembeli (Pesanan Dibuat)', 'Rekomendasi Strategi']])

    # DOWNLOAD CSV
    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="⬇ Download CSV Hasil + Strategi",
        data=csv_buffer.getvalue(),
        file_name=f"hasil_{selected_file_name.replace('.csv','')}_dengan_strategi.csv",
        mime="text/csv"
    )

    # FOOTER
    st.markdown("""
    <hr>
    <p style='text-align: center; font-size: 12px; color: gray;'>
        Dibuat oleh <b>VioRita Adnyani</b> • Dashboard Penjualan & Clustering K-Means © 2025
    </p>
    """, unsafe_allow_html=True)
    
else:
    st.info("Silakan upload satu atau lebih file CSV, lalu pilih file untuk ditampilkan.")