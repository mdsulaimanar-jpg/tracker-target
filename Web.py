import streamlit as st
import pandas as pd
from urllib.parse import urlencode
from datetime import datetime, timedelta
from ics import Calendar, Event
from supabase import create_client, Client

st.set_page_config(page_title="Tracker Akademik & Funding", layout="wide")

# --- KONEKSI SUPABASE ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

# --- FUNGSI UPDATE & DELETE ---
def hapus_data(id_kegiatan):
    supabase.table("kegiatan").delete().eq("id", id_kegiatan).execute()

def update_data(id_kegiatan, kategori, nama, deadline, status, deskripsi):
    data = {
        "kategori": kategori,
        "nama": nama,
        "deadline": str(deadline),
        "status": status,
        "deskripsi": deskripsi
    }
    supabase.table("kegiatan").update(data).eq("id", id_kegiatan).execute()

st.title(" Tracker Jurnal, Kompetisi & Funding")

# --- SIDEBAR: Form Tambah Data ---
with st.sidebar:
    st.header("➕ Tambah Kegiatan Baru")
    kategori_baru = st.selectbox("Kategori", ["Jurnal", "Kompetisi", "Funding"])
    nama_baru = st.text_input("Nama Kegiatan (Wajib diisi)")
    deadline_baru = st.date_input("Tanggal Deadline")
    status_baru = st.selectbox("Status", ["Persiapan", "In Review", "Revisi", "Selesai", "Ditolak"])
    deskripsi_baru = st.text_area("Deskripsi / Link Drive")
    
    if st.button("Simpan Kegiatan", type="primary"):
        if nama_baru:
            data_insert = {
                "kategori": kategori_baru,
                "nama": nama_baru,
                "deadline": str(deadline_baru),
                "status": status_baru,
                "deskripsi": deskripsi_baru
            }
            supabase.table("kegiatan").insert(data_insert).execute()
            st.success("Data berhasil ditambahkan ke Cloud!")
            st.rerun()
        else:
            st.error("Nama kegiatan tidak boleh kosong, bre!")

# --- AMBIL DATA DARI SUPABASE ---
response = supabase.table("kegiatan").select("*").execute()
df = pd.DataFrame(response.data)

if not df.empty:
    df['deadline_date'] = pd.to_datetime(df['deadline']).dt.date
    today = datetime.now().date()
    kondisi_history = (df['status'] == 'Selesai') | (today > df['deadline_date'] + timedelta(days=7))
    df_history = df[kondisi_history]
    df_aktif = df[~kondisi_history]
else:
    df_aktif = pd.DataFrame()
    df_history = pd.DataFrame()

# --- MAIN AREA: DIBAGI JADI 2 TAB ---
tab_aktif, tab_history = st.tabs(["📌 Target Aktif", " History Target"])

kategori_list = ["Jurnal", "Kompetisi", "Funding"]
status_list = ["Persiapan", "In Review", "Revisi", "Selesai", "Ditolak"]

# 1. TAB TARGET AKTIF
with tab_aktif:
    st.header("Daftar Target Aktif")
    if df_aktif.empty:
        st.info("Belum ada target aktif. Gas tambah baru di sidebar!")
    else:
        for index, row in df_aktif.iterrows():
            with st.expander(f"[{row['kategori']}] {row['nama']} - Status: {row['status']} (DL: {row['deadline']})"):
                st.write(f"**Catatan/Link:** {row['deskripsi']}")
                
                # --- Tombol Kalender ---
                col_cal1, col_cal2 = st.columns(2)
                dl_date = datetime.strptime(row['deadline'], "%Y-%m-%d")
                dl_str = dl_date.strftime("%Y%m%d")
                end_str = (dl_date + timedelta(days=1)).strftime("%Y%m%d")
                
                gcal_params = {"action": "TEMPLATE", "text": f"Deadline: {row['nama']}", "dates": f"{dl_str}/{end_str}", "details": row['deskripsi']}
                gcal_url = "https://calendar.google.com/calendar/render?" + urlencode(gcal_params)
                col_cal1.markdown(f"**[📅 Masukkan ke Google Calendar]({gcal_url})**")
                
                cal = Calendar()
                e = Event()
                e.name = f"Deadline: {row['nama']}"
                e.begin = row['deadline']
                e.description = row['deskripsi']
                e.make_all_day()
                cal.events.add(e)
                col_cal2.download_button("📥 Download .ics", str(cal), file_name=f"DL_{row['nama']}.ics", mime="text/calendar", key=f"ics_{row['id']}")
                
                st.divider()
                
                # --- Form Edit Data ---
                st.write("⚙️ **Edit atau Hapus Target**")
                with st.form(key=f"form_edit_{row['id']}"):
                    col1, col2 = st.columns(2)
                    edit_kat = col1.selectbox("Kategori", kategori_list, index=kategori_list.index(row['kategori']), key=f"kat_{row['id']}")
                    edit_nama = col2.text_input("Nama Kegiatan", value=row['nama'], key=f"nama_{row['id']}")
                    
                    col3, col4 = st.columns(2)
                    edit_dl = col3.date_input("Deadline", value=dl_date.date(), key=f"dl_{row['id']}")
                    edit_status = col4.selectbox("Status", status_list, index=status_list.index(row['status']), key=f"stat_{row['id']}")
                    
                    edit_desk = st.text_area("Deskripsi / Link", value=row['deskripsi'], key=f"desk_{row['id']}")
                    
                    if st.form_submit_button("Simpan Perubahan"):
                        update_data(row['id'], edit_kat, edit_nama, edit_dl, edit_status, edit_desk)
                        st.success("Target berhasil diperbarui!")
                        st.rerun()
                
                if st.button("🗑️ Hapus", key=f"del_{row['id']}"):
                    hapus_data(row['id'])
                    st.rerun()

# 2. TAB HISTORY
with tab_history:
    st.header("History Target")
    if df_history.empty:
        st.info("Belum ada history.")
    else:
        for index, row in df_history.iterrows():
            alasan = "Beneran Beres 🏆" if row['status'] == 'Selesai' else "Kehapus (Lewat Deadline 7 Hari) ⏳"
            with st.expander(f"[{alasan}] {row['nama']} ({row['kategori']})"):
                st.write(f"**Tanggal Deadline Dulu:** {row['deadline']}")
                st.write(f"**Status Terakhir:** {row['status']}")
                st.write(f"**Catatan/Link:** {row['deskripsi']}")
                
                if st.button("🗑️ Hapus Permanen", key=f"del_hist_{row['id']}"):
                    hapus_data(row['id'])
                    st.rerun()