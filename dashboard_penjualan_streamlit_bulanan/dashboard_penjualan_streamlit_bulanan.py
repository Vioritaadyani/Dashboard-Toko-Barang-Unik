# 📦 Dashboard Penjualan Bulanan - Streamlit
# Fungsi: Mengunggah file CSV penjualan per bulan,
#         memeriksa struktur file, menampilkan ringkasan,
#         grafik penjualan, dan analisis top produk.

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Penjualan Bulanan", layout="wide")
st.title("📦 Dashboard Penjualan Lengkap")

# Upload File CSV
uploaded_files = st.file_uploader(
    "📁 Upload file CSV (penjualan per bulan)", 
    type="csv", 
    accept_multiple_files=True
)

if uploaded_files:
    all_data = []  # Menyimpan semua data yang valid dari setiap file

    st.subheader("🧪 Pemeriksaan Struktur File CSV")
    for file in uploaded_files:
        file_name = file.name
        st.markdown(f"#### 📁 {file_name}")

        try:
            # Membaca ulang dari awal untuk menghindari posisi file yang salah
            file.seek(0)
            df = pd.read_csv(file, encoding='ISO-8859-1')

            # Menampilkan jumlah baris & kolom
            st.write(f"Jumlah baris: {len(df)}")
            st.write("Kolom ditemukan:", list(df.columns))

            # Validasi kolom penting
            if 'Produk (Pesanan Dibuat)' not in df.columns or 'Produk' not in df.columns:
                st.error("❌ Kolom 'Produk (Pesanan Dibuat)' atau 'Produk' TIDAK DITEMUKAN")
                continue
            elif df.empty or df['Produk (Pesanan Dibuat)'].dropna().empty:
                st.warning("⚠️ File ini kosong atau tidak ada data penjualan")
                continue
            else:
                st.success("✅ Struktur file valid")

            # Ekstrak bulan & tahun dari nama file 
            match = re.search(r'bulan_(\d{1,2})_(\d{4})', file_name)
            if match:
                bulan, tahun = int(match.group(1)), int(match.group(2))
            else:
                st.warning(f"❌ Nama file tidak dikenali: {file_name}")
                continue

            # Konversi jumlah produk ke integer
            df['Jumlah'] = pd.to_numeric(df['Produk (Pesanan Dibuat)'], errors='coerce').fillna(0).astype(int)

            # Tambahkan kolom informasi waktu
            df['Bulan'] = bulan
            df['Tahun'] = tahun
            df['Nama_Bulan'] = pd.to_datetime(f"{tahun}-{bulan}-01").strftime('%B')

            # Simpan data yang valid
            all_data.append(df)

        except Exception as e:
            st.error(f"❌ Gagal membaca file: {e}")

    # Proses jika ada data valid
    if all_data:
        # Gabungkan semua data
        df_all = pd.concat(all_data, ignore_index=True)

        # Ringkasan total penjualan per bulan
        st.subheader("📊 Ringkasan Total Penjualan per Bulan")
        summary = df_all.groupby(['Tahun', 'Bulan', 'Nama_Bulan'])['Jumlah'].sum().reset_index()
        summary_sorted = summary.sort_values(by='Jumlah', ascending=False)

        # Tampilkan bulan dengan penjualan tertinggi
        best = summary_sorted.iloc[0]
        st.success(f"📌 Penjualan terbanyak: **{best['Nama_Bulan']} {int(best['Tahun'])}** sebanyak **{int(best['Jumlah'])} pesanan**.")
        st.info(f"💡 Strategi: Tingkatkan stok & promosi sebelum **{best['Nama_Bulan']}** setiap tahun.")

        # Tabel ringkasan
        st.dataframe(summary.sort_values(by=['Tahun', 'Bulan']))

        # Grafik penjualan bulanan
        st.subheader("📉 Grafik Penjualan Bulanan")
        plt.figure(figsize=(12, 6))
        sns.barplot(data=summary, x='Nama_Bulan', y='Jumlah', hue='Tahun', palette='tab10')
        plt.ylabel("Total Pesanan")
        plt.xlabel("Bulan")
        plt.xticks(rotation=45)
        st.pyplot(plt.gcf())

        # Tabel Total Pesanan
        st.subheader("📋 Total Pesanan per Bulan")
        summary_display = summary.sort_values(by=['Tahun', 'Bulan'])
        summary_display['Periode'] = summary_display['Nama_Bulan'] + " " + summary_display['Tahun'].astype(str)
        summary_display = summary_display[['Periode', 'Jumlah']].rename(columns={'Jumlah': 'Total Pesanan'})
        st.table(summary_display.set_index('Periode'))

        # Filter bulan & tahun untuk analisis detail
        st.subheader("🗂️ Filter Data Berdasarkan Bulan dan Tahun")
        bulan_terpilih = st.selectbox("Pilih Bulan", options=sorted(df_all['Nama_Bulan'].unique()))
        tahun_terpilih = st.selectbox("Pilih Tahun", options=sorted(df_all['Tahun'].unique()))
        df_filtered = df_all[(df_all['Nama_Bulan'] == bulan_terpilih) & (df_all['Tahun'] == tahun_terpilih)]

        # Top 5 produk paling laris
        st.subheader(f"🏆 Top 5 Produk Paling Laris - {bulan_terpilih} {tahun_terpilih}")
        if not df_filtered.empty:
            produk_total_all = df_filtered.groupby('Produk')['Jumlah'].sum().sort_values(ascending=False)
            top5 = produk_total_all.head(5)[::-1]  # Balik urutan biar tampil dari bawah ke atas
            total_semua = df_filtered['Jumlah'].sum()
            persentase = (top5 / total_semua * 100).round(1)

            # Fungsi catatan dinamis
            def catatan_produk_laris(nama_produk):
                nama_produk = nama_produk.lower()
                if "bulu mata" in nama_produk:
                    return "Trend kecantikan akhir tahun"
                elif "alis" in nama_produk:
                    return "Permintaan alat kecantikan meningkat"
                elif "taplak" in nama_produk or "meja makan" in nama_produk:
                    return "Dekorasi rumah menjelang liburan"
                elif "korean" in nama_produk:
                    return "Produk viral di media sosial"
                elif "penjepit" in nama_produk:
                    return "Alat kecantikan praktis dan murah"
                else:
                    return "Kemungkinan efek diskon/promosi"

            # Grafik top 5 produk
            plt.figure(figsize=(12, 6))
            ax = sns.barplot(x=top5.values, y=top5.index, color='#FFB47D')
            plt.title(f"Kategori Produk Paling Laris - {bulan_terpilih} {tahun_terpilih}", fontsize=18, fontweight='bold')
            plt.xlabel("Jumlah Pesanan", fontsize=12)

            # Tambahkan label jumlah & persentase di bar chart
            for i, (val, pct) in enumerate(zip(top5.values, persentase.values)):
                ax.text(val + max(top5.values) * 0.01, i, f"{pct}%\n{val} pesanan", va='center', fontsize=10)

            plt.tight_layout()
            st.pyplot(plt.gcf())

            # Tabel top 5 + catatan
            st.markdown("#### 📌 Detail Top 5 Produk dengan Catatan")
            top5_df = pd.DataFrame({
                'Produk': top5.index,
                'Jumlah Pesanan': top5.values,
                'Persentase': persentase.values
            })
            top5_df['Catatan'] = top5_df['Produk'].apply(catatan_produk_laris)
            st.dataframe(top5_df.reset_index(drop=True))

            # Produk lainnya
            st.subheader("📦 Produk Lainnya (di luar Top 5)")
            produk_lain = produk_total_all.iloc[5:]
            if not produk_lain.empty:
                produk_lain_df = produk_lain.reset_index()
                produk_lain_df.columns = ['Produk', 'Jumlah Pesanan']
                st.dataframe(produk_lain_df)
            else:
                st.info("✅ Tidak ada produk lain di luar Top 5.")
        else:
            st.warning("⚠️ Tidak ada data penjualan pada bulan dan tahun ini.")
    else:
        st.warning("⚠️ Tidak ada file valid untuk diproses.")
else:
    st.info("⬆️ Upload file CSV penjualan untuk mulai analisis.")
