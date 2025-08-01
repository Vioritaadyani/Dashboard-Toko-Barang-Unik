import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from io import BytesIO
import numpy as np

# --- CONFIG ---
st.set_page_config(page_title="Dashboard Penjualan", layout="wide", page_icon="📊")

# --- CUSTOM CSS ---
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

# --- SIDEBAR ---
uploaded_file = st.sidebar.file_uploader("📁 Upload File CSV", type=['csv'])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df['Total Penjualan (Juta)'] = df['Total Penjualan (Pesanan Dibuat) (IDR)'] / 1_000_000

    # === KMeans Clustering ===
    X = df[['Total Pembeli (Pesanan Dibuat)', 'Produk (Pesanan Dibuat)']]
    kmeans = KMeans(n_clusters=3, random_state=42)
    df['Cluster'] = kmeans.fit_predict(X)
    centroids = kmeans.cluster_centers_

    cluster_avg = df.groupby('Cluster')['Total Penjualan (Juta)'].mean().sort_values().index.tolist()
    final_map = {}
    for idx, label in zip(cluster_avg, ['Kurang Laris', 'Laris', 'Sangat Laris']):
        final_map[idx] = label
    df['Kategori'] = df['Cluster'].map(final_map)

    st.sidebar.markdown("## 🔍 Filter Data")
    kategori_filter = st.sidebar.multiselect("Pilih Kategori", options=df['Kategori'].unique(), default=df['Kategori'].unique())

    min_pembeli, max_pembeli = int(df['Total Pembeli (Pesanan Dibuat)'].min()), int(df['Total Pembeli (Pesanan Dibuat)'].max())
    pembeli_range = st.sidebar.slider("Jumlah Pembeli", min_value=min_pembeli, max_value=max_pembeli, value=(min_pembeli, max_pembeli))

    min_penjualan, max_penjualan = float(df['Total Penjualan (Juta)'].min()), float(df['Total Penjualan (Juta)'].max())
    penjualan_range = st.sidebar.slider("Total Penjualan (Juta)", min_value=min_penjualan, max_value=max_penjualan, value=(min_penjualan, max_penjualan))

    df = df[
        (df['Kategori'].isin(kategori_filter)) &
        (df['Total Pembeli (Pesanan Dibuat)'].between(*pembeli_range)) &
        (df['Total Penjualan (Juta)'].between(*penjualan_range))
    ]

    def rekomendasi(row):
        if row['Kategori'] == 'Sangat Laris':
            return "Pertahankan stok & promosi rutin"
        elif row['Kategori'] == 'Laris':
            return "Tingkatkan promosi jadi sangat laris"
        else:
            return "Evaluasi produk/buat bundling"

    df['Rekomendasi Strategi'] = df.apply(rekomendasi, axis=1)

    st.markdown("""
    <h1 style='text-align: center;'>📊 Dashboard Analisis Penjualan Produk Toko Barang Unik Makassar</h1>
    <hr>
    """, unsafe_allow_html=True)

    total_penjualan = df['Total Penjualan (Pesanan Dibuat) (IDR)'].sum()
    total_produk = df['Produk (Pesanan Dibuat)'].sum()
    total_data = len(df)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Penjualan", f"Rp{total_penjualan:,.0f}")
    col2.metric("Total Produk Terjual", f"{int(total_produk):,} pcs")
    col3.metric("Jumlah Data Produk", f"{total_data} item")

    top_produk = df.sort_values(by='Produk (Pesanan Dibuat)', ascending=False).head(10)
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    sns.barplot(x='Produk (Pesanan Dibuat)', y='Produk', data=top_produk, palette="viridis", ax=ax1)
    ax1.set_title("Top 10 Produk Terlaris")
    col4, col5 = st.columns([2, 1])
    col4.pyplot(fig1)

    kategori_counts = df['Kategori'].value_counts()
    fig2, ax2 = plt.subplots()
    ax2.pie(kategori_counts, labels=kategori_counts.index, autopct='%1.1f%%', startangle=140,
            colors=sns.color_palette("pastel"))
    ax2.axis('equal')
    ax2.set_title("Distribusi Kategori Produk")
    col5.pyplot(fig2)

    fig3, ax3 = plt.subplots(figsize=(8, 6))
    colors = plt.cm.tab10(np.arange(10))

    for cluster_num in sorted(df['Cluster'].unique()):
        cluster_data = df[df['Cluster'] == cluster_num]
        kategori = final_map[cluster_num]
        ax3.scatter(
            cluster_data['Total Pembeli (Pesanan Dibuat)'],
            cluster_data['Produk (Pesanan Dibuat)'],
            label=f"Cluster {cluster_num} ({kategori})",
            c=[colors[cluster_num]],
            alpha=0.7,
            edgecolors='w',
            s=50
        )

    ax3.scatter(
        centroids[:, 0],
        centroids[:, 1],
        c='black',
        s=200,
        marker='X',
        label='Centroid'
    )

    ax3.set_xlabel("Total Pembeli")
    ax3.set_ylabel("Produk Terjual")
    ax3.set_title("Visualisasi K-Means Clustering (k=3)")
    ax3.legend()

    cluster_penjualan = df.groupby('Kategori')['Total Penjualan (Juta)'].sum().sort_values(ascending=False)
    fig4, ax4 = plt.subplots(figsize=(6, 4))
    sns.barplot(x=cluster_penjualan.values, y=cluster_penjualan.index, palette="Blues_d", ax=ax4)
    ax4.set_title("Kontribusi Penjualan per Kategori")

    col6, col7 = st.columns(2)
    col6.pyplot(fig3)
    col7.pyplot(fig4)

    st.subheader("📌 Rekomendasi Strategi Bisnis per Produk")
    st.dataframe(df[['Produk', 'Kategori', 'Total Penjualan (Juta)', 'Total Pembeli (Pesanan Dibuat)', 'Rekomendasi Strategi']])

    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="⬇️ Download CSV Hasil + Strategi",
        data=csv_buffer.getvalue(),
        file_name="hasil_penjualan_dengan_strategi.csv",
        mime="text/csv"
    )

    st.markdown("""
    <hr>
    <p style='text-align: center; font-size: 12px; color: gray;'>
        Dibuat oleh <b>VioRita Adnyani</b> • Dashboard Penjualan & Clustering K-Means © 2025
    </p>
    """, unsafe_allow_html=True)

else:
    st.info("Silakan upload file CSV untuk menampilkan dashboard.")
