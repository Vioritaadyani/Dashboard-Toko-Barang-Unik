import streamlit as st
import pandas as pd
from sklearn.cluster import KMeans

# Konfigurasi halaman
st.set_page_config(page_title="KMeans Penjualan", layout="wide")
st.title("📊 Analisis Pola Penjualan dengan K-Means Clustering (k=3)")

# ✅ Tampilkan gambar hasil clustering dari file PNG statis yang benar
st.subheader("📈 Visualisasi K-Means Clustering (Gambar Statis)")
st.image(
    "./download_vio.png",  # Pastikan file ini berada di direktori yang sama dengan file .py
    caption="Visualisasi K-Means Clustering Optimal (k=3)",
    use_column_width=True
)

# ✅ Upload file CSV untuk analisis data
st.subheader("📂 Unggah File Data Penjualan")
uploaded_file = st.file_uploader("Pilih file CSV", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Validasi kolom yang dibutuhkan
    required_cols = ['Total Pembeli', 'Produk Terjual', 'Total Penjualan']
    if all(col in df.columns for col in required_cols):

        # Ekstrak fitur
        X = df[['Total Pembeli', 'Produk Terjual']]

        # KMeans clustering (k=3)
        kmeans = KMeans(n_clusters=3, random_state=42, n_init='auto')
        df['Cluster'] = kmeans.fit_predict(X)

        # Mapping cluster ke label kategori berdasarkan total penjualan
        cluster_summary = df.groupby('Cluster')['Total Penjualan'].sum().sort_values()
        kategori_label = ['Kurang Laris', 'Laris', 'Sangat Laris']
        final_map = {cluster_num: kategori_label[i] for i, cluster_num in enumerate(cluster_summary.index)}
        df['Kategori'] = df['Cluster'].map(final_map)

        # ✅ Tampilkan hasil data
        st.subheader("📋 Tabel Data dengan Label Kategori")
        st.dataframe(df[['Total Pembeli', 'Produk Terjual', 'Total Penjualan', 'Kategori']])

        # ✅ Ringkasan Total Penjualan per Kategori
        st.subheader("📊 Ringkasan Total Penjualan per Kategori")
        summary = df.groupby('Kategori')['Total Penjualan'].sum().reset_index().sort_values(by='Total Penjualan', ascending=False)
        st.table(summary)

    else:
        st.error("❗ Kolom 'Total Pembeli', 'Produk Terjual', dan 'Total Penjualan' tidak ditemukan dalam file.")
else:
    st.info("ℹ️ Silakan unggah file CSV untuk memulai analisis.")
