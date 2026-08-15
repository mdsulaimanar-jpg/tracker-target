import streamlit as st
from urllib.parse import urlencode
from datetime import datetime, timedelta
from ics import Calendar, Event
from supabase import create_client, Client

st.set_page_config(page_title="Tracker Akademik", layout="wide")

# --- KONEKSI SUPABASE ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

# --- SISTEM HYBRID: CEK JALUR VIP MENTOR ---
# Kalau mentor buka link pakai ?akses=mentor, otomatis login sebagai 'mentor_vip'
if st.query_params.get("akses") == "mentor":
    st.session_state.user_email = "mentor_vip"
elif 'user_email' not in st.session_state:
    st.session_state.user_email = None

# --- FUNGSI AUTENTIKASI ---
def login_user(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user_email = res.user.email
        st.rerun()
    except Exception as e:
        st.error("Login gagal! Cek email/password lu.")

def register_user(email, password):
    try:
        supabase.auth.sign_up({"email": email, "password": password})
        st.success("Berhasil daftar! Silakan Login.")
    except Exception as e:
        st.error(f"Gagal daftar: {e}")

def logout_user():
    # Cuma bisa logout kalau bukan mentor (karena mentor jalurnya nempel di URL)
    if st.session_state.user_email != "mentor_vip":
        supabase.auth.sign_out()
    st.session_state.user_email = None
    st.query_params.clear() # Hapus param URL kalau ada
    st.rerun()

# --- HALAMAN LOGIN (MUNCUL KALAU BUKAN MENTOR & BELUM LOGIN) ---
if st.session_state.user_email is None:
    st.title("🔐 Login Tracker App")
    tab_login, tab_register = st.tabs(["Masuk", "Daftar Baru"])
    
    with tab_login:
        email_login = st.text_input("Email")
        pass_login = st.text_input("Password", type="password")
        if st.button("Login"):
            login_user(email_login, pass_login)
            
    with tab_register:
        email_reg = st.text_input("Email Baru", key="reg_email")
        pass_reg = st.text_input("Password Baru (Min 6 karakter)", type="password", key="reg_pass")
        if st.button("Daftar"):
            register_user(email_reg, pass_reg)

# --- HALAMAN UTAMA (JIKA SUDAH LOGIN / MASUK JALUR VIP) ---
else:
    # --- FUNGSI UPDATE & DELETE ---
    def hapus_data(id_kegiatan):
        supabase.table("kegiatan").delete().eq("id", id_kegiatan).execute()

    def update_data(id_kegiatan, kategori, nama, deadline, status, deskripsi):
        data = {
            "kategori": kategori, "nama": nama, "deadline": str(deadline),
            "status": status, "deskripsi": deskripsi
        }
        supabase.table("kegiatan").update(data).eq("id", id_kegiatan).execute()

    col_head1, col_head2 = st.columns([4, 1])
    col_head1.title("🎯 Tracker Jurnal & Kompetisi")
    
    with col_head2:
        if st.session_state.user_email == "mentor_vip":
            st.success("👨‍🏫 Akses VIP Mentor")
        else:
            st.info(f"👤 {st.session_state.user_email}")
            if st.button("🚪 Logout"):
                logout_user()

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("➕ Tambah Kegiatan")
        kategori_baru = st.selectbox("Kategori", ["Jurnal", "Kompetisi", "Funding"])
        nama_baru = st.text_input("Nama Kegiatan")
        deadline_baru = st.date_input("Tanggal Deadline")
        status_baru = st.selectbox("Status", ["Persiapan", "In Review", "Revisi", "Selesai", "Ditolak"])
        deskripsi_baru = st.text_area("Deskripsi / Link")
        
        if st.button("Simpan", type="primary"):
            if nama_baru:
                data_insert = {
                    "owner_email": st.session_state.user_email, # Data nempel ke user yg aktif
                    "kategori": kategori_baru,
                    "nama": nama_baru,
                    "deadline": str(deadline_baru),
                    "status": status_baru,
                    "deskripsi": deskripsi_baru
                }
                supabase.table("kegiatan").insert(data_insert).execute()
                st.success("Tersimpan!")
                st.rerun()

    # --- AMBIL DATA SESUAI USER ---
    response = supabase.table("kegiatan").select("*").eq("owner_email", st.session_state.user_email).execute()
    data_semua = response.data

    today = datetime.now().date()
    data_aktif = []
    data_history = []

    for row in data_semua:
        dl_date = datetime.strptime(row['deadline'], "%Y-%m-%d").date()
        if row['status'] == 'Selesai' or today > (dl_date + timedelta(days=7)):
            data_history.append(row)
        else:
            data_aktif.append(row)

    # --- TAMPILAN TAB ---
    tab_aktif, tab_history = st.tabs(["📌 Aktif", "🗄️ History"])
    kategori_list = ["Jurnal", "Kompetisi", "Funding"]
    status_list = ["Persiapan", "In Review", "Revisi", "Selesai", "Ditolak"]

    with tab_aktif:
        if not data_aktif:
            st.info("Belum ada target aktif.")
        for row in data_aktif:
            with st.expander(f"[{row['kategori']}] {row['nama']} (DL: {row['deadline']})"):
                st.write(row['deskripsi'])
                st.divider()
                with st.form(key=f"edit_{row['id']}"):
                    col1, col2 = st.columns(2)
                    e_kat = col1.selectbox("Kategori", kategori_list, index=kategori_list.index(row['kategori']))
                    e_nama = col2.text_input("Nama", value=row['nama'])
                    col3, col4 = st.columns(2)
                    dl_date = datetime.strptime(row['deadline'], "%Y-%m-%d").date()
                    e_dl = col3.date_input("Deadline", value=dl_date)
                    e_stat = col4.selectbox("Status", status_list, index=status_list.index(row['status']))
                    e_desk = st.text_area("Catatan", value=row['deskripsi'])
                    
                    if st.form_submit_button("Update"):
                        update_data(row['id'], e_kat, e_nama, e_dl, e_stat, e_desk)
                        st.rerun()
                if st.button("🗑️ Hapus", key=f"del_{row['id']}"):
                    hapus_data(row['id'])
                    st.rerun()

    with tab_history:
        if not data_history:
            st.info("History kosong.")
        for row in data_history:
            with st.expander(f"{row['nama']} - Terakhir: {row['status']}"):
                if st.button("🗑️ Hapus Permanen", key=f"del_h_{row['id']}"):
                    hapus_data(row['id'])
                    st.rerun()
