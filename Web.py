import streamlit as st
from urllib.parse import urlencode
from datetime import datetime, timedelta
from supabase import create_client, Client

st.set_page_config(page_title="Tracker Akademik", layout="wide")

# --- KONEKSI SUPABASE ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

# --- SISTEM HYBRID ---
if st.query_params.get("akses") == "mentor":
    st.session_state.user_email = "mentor_vip"
elif 'user_email' not in st.session_state:
    st.session_state.user_email = None

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
    if st.session_state.user_email != "mentor_vip":
        supabase.auth.sign_out()
    st.session_state.user_email = None
    st.query_params.clear()
    st.rerun()

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
        pass_reg = st.text_input("Password Baru", type="password", key="reg_pass")
        if st.button("Daftar"):
            register_user(email_reg, pass_reg)

else:
    def hapus_data(id_kegiatan):
        supabase.table("kegiatan").delete().eq("id", id_kegiatan).execute()

    def update_data(id_kegiatan, kategori, nama, deadline, status, deskripsi, link, tgl_prop, stat_prop, naungan, tujuan_prop):
        data = {
            "kategori": kategori, "nama": nama, "deadline": str(deadline),
            "status": status, "deskripsi": deskripsi, "link": link,
            "tgl_proposal": str(tgl_prop) if tgl_prop else None,
            "status_proposal": stat_prop, "naungan": naungan,
            "tujuan_proposal": tujuan_prop
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

    # --- MAIN AREA: FORM TAMBAH DATA ---
    with st.expander("➕ Tambah Kegiatan Baru (Klik untuk membuka)", expanded=False):
        kategori_baru = st.selectbox("Pilih Kategori", ["Jurnal", "Kompetisi", "Funding", "Project", "Pengmas"])
        nama_baru = st.text_input("Nama Kegiatan (Wajib diisi)")
        
        col_m1, col_m2 = st.columns(2)
        deadline_baru = col_m1.date_input("Deadline Utama (Final)")
        status_baru = col_m2.selectbox("Status Akhir", ["Persiapan", "In Review", "Revisi", "Selesai", "Ditolak"])
        
        if kategori_baru != "Jurnal":
            st.markdown("##### 📄 Detail Kelengkapan Proposal & Afiliasi")
            col_p3, col_p4 = st.columns(2)
            naungan_prop = col_p3.selectbox("Dinaungi Oleh", ["Individu", "Laboratorium Dasar Komputer", "Telkom University", "Lainnya"])
            wajib_label = " (Wajib Diisi)" if naungan_prop != "Individu" else ""
            tujuan_prop = col_p4.text_input(f"Dikirim ke Instansi/Penyelenggara{wajib_label}")
            
            col_p1, col_p2 = st.columns(2)
            tgl_prop = col_p1.date_input("Deadline Pengiriman Proposal")
            stat_prop = col_p2.selectbox("Status Proposal", ["Belum Kirim", "Terkirim", "Diterima", "Ditolak"])
        else:
            tgl_prop = None
            stat_prop = "-"
            naungan_prop = "Individu"
            tujuan_prop = "-"
            
        st.markdown("##### 📝 Informasi Tambahan")
        col_i1, col_i2 = st.columns(2)
        deskripsi_baru = col_i1.text_area("Deskripsi Singkat / Catatan")
        link_baru = col_i2.text_input("Link Berkas (Drive / Web)")

        if st.button("Simpan Kegiatan", type="primary", use_container_width=True):
            if not nama_baru:
                st.error("❌ Nama kegiatan tidak boleh kosong!")
            elif kategori_baru != "Jurnal" and naungan_prop != "Individu" and not tujuan_prop:
                st.error("🚨 Gagal Menyimpan! Karena ini berafiliasi (bukan Individu), kolom 'Dikirim ke' WAJIB diisi.")
            else:
                data_insert = {
                    "owner_email": st.session_state.user_email,
                    "kategori": kategori_baru, "nama": nama_baru,
                    "deadline": str(deadline_baru), "status": status_baru,
                    "deskripsi": deskripsi_baru, "link": link_baru,
                    "tgl_proposal": str(tgl_prop) if tgl_prop else None,
                    "status_proposal": stat_prop, "naungan": naungan_prop,
                    "tujuan_proposal": tujuan_prop
                }
                supabase.table("kegiatan").insert(data_insert).execute()
                st.success("Tersimpan!")
                st.rerun()

    st.divider()

    # --- AMBIL DATA DARI SUPABASE ---
    response = supabase.table("kegiatan").select("*").eq("owner_email", st.session_state.user_email).execute()
    data_semua = response.data

    today = datetime.now().date()
    data_aktif = []
    data_history = []

    for row in data_semua:
        dl_date = datetime.strptime(row['deadline'], "%Y-%m-%d").date()
        if row['status'] == 'Selesai' or (today > (dl_date + timedelta(days=7)) and row['status'] != 'Revisi'):
            data_history.append(row)
        else:
            data_aktif.append(row)

    total_ongoing = len(data_aktif)
    mendekati_dl = sum(1 for row in data_aktif if 0 <= (datetime.strptime(row['deadline'], "%Y-%m-%d").date() - today).days <= 7)
    total_history = len(data_history)
    selesai_count = sum(1 for row in data_history if row['status'] == 'Selesai')
    terlewat_count = total_history - selesai_count

    # --- TAMPILAN TAB BAWAH ---
    tab_aktif, tab_history = st.tabs(["📌 Aktif", "🗄️ History"])
    
    kategori_list = ["Jurnal", "Kompetisi", "Funding", "Project", "Pengmas"]
    status_list = ["Persiapan", "In Review", "Revisi", "Selesai", "Ditolak"]
    naungan_list = ["Individu", "Laboratorium Dasar Komputer", "Telkom University", "Lainnya"]
    stat_prop_list = ["Belum Kirim", "Terkirim", "Diterima", "Ditolak"]

    with tab_aktif:
        st.info(f"**ℹ️ Status Saat Ini:** Total *ongoing* paper / jurnal / project / kompetisi ada **{total_ongoing}**.")
        st.error(f"**🚨 Yang mendekati deadline (< 7 hari):** ada **{mendekati_dl}**.")
        st.divider()

        if not data_aktif:
            st.write("Belum ada target aktif.")
        for row in data_aktif:
            dl_date = datetime.strptime(row['deadline'], "%Y-%m-%d").date()
            days_left = (dl_date - today).days
            
            peringatan = ""
            if row['status'] == 'Revisi':
                peringatan = "🔴 [REVISI] "
            elif 0 <= days_left <= 7:
                peringatan = "🚨 [DEADLINE DEKAT] "
            elif days_left < 0:
                peringatan = "⚠️ [LEWAT DEADLINE] "

            with st.expander(f"{peringatan}[{row['kategori']}] {row['nama']} (DL Final: {row['deadline']})"):
                if row['status'] == 'Revisi':
                    st.error("📌 Status berubah menjadi REVISI! Segera perbaiki dan kirim ulang.")
                elif 0 <= days_left <= 7:
                    st.error(f"⏳ Hati-hati! Sisa waktu tinggal {days_left} hari lagi menuju deadline!")
                
                st.write(f"**Status Saat Ini:** {row['status']}")
                st.write(f"**Deskripsi:** {row.get('deskripsi', '-')}")
                if row.get('link', ''):
                    st.write(f"**Link:** [Buka Tautan]({row['link']})")
                
                if row['kategori'] != "Jurnal":
                    st.write("---")
                    st.write(f"**Afiliasi:** {row.get('naungan', '-')} | **Tujuan:** {row.get('tujuan_proposal', '-')}")
                    st.write(f"**Status Proposal:** {row.get('status_proposal', '-')} (DL Proposal: {row.get('tgl_proposal', '-')})")
                
                st.divider()
                
                # --- FORM EDIT DINAMIS ---
                st.markdown("##### ✏️ Edit Data")
                with st.form(key=f"edit_{row['id']}"):
                    e_kat = st.selectbox("Kategori", kategori_list, index=kategori_list.index(row['kategori']) if row['kategori'] in kategori_list else 0)
                    e_nama = st.text_input("Nama Kegiatan", value=row['nama'])
                    
                    col_e1, col_e2 = st.columns(2)
                    e_dl = col_e1.date_input("Deadline Utama", value=dl_date)
                    e_stat = col_e2.selectbox("Status Akhir", status_list, index=status_list.index(row['status']) if row['status'] in status_list else 0)
                    
                    if e_kat != "Jurnal":
                        st.markdown("###### Kelengkapan Proposal & Afiliasi")
                        col_ep1, col_ep2 = st.columns(2)
                        idx_naungan = naungan_list.index(row.get('naungan')) if row.get('naungan') in naungan_list else 0
                        e_naungan = col_ep1.selectbox("Dinaungi Oleh", naungan_list, index=idx_naungan)
                        
                        wajib_label_e = " (Wajib Diisi)" if e_naungan != "Individu" else ""
                        e_tujuan = col_ep2.text_input(f"Dikirim ke Instansi/Penyelenggara{wajib_label_e}", value=row.get('tujuan_proposal') or "")
                        
                        col_ep3, col_ep4 = st.columns(2)
                        prop_date_val = datetime.strptime(row['tgl_proposal'], "%Y-%m-%d").date() if row.get('tgl_proposal') else today
                        e_tgl_prop = col_ep3.date_input("Deadline Proposal", value=prop_date_val)
                        
                        idx_stat_prop = stat_prop_list.index(row.get('status_proposal')) if row.get('status_proposal') in stat_prop_list else 0
                        e_stat_prop = col_ep4.selectbox("Status Proposal", stat_prop_list, index=idx_stat_prop)
                    else:
                        e_tgl_prop = None
                        e_stat_prop = "-"
                        e_naungan = "Individu"
                        e_tujuan = "-"
                        
                    st.markdown("###### Informasi Tambahan")
                    col_ei1, col_ei2 = st.columns(2)
                    e_desk = col_ei1.text_area("Deskripsi", value=row.get('deskripsi') or "")
                    e_link = col_ei2.text_input("Link Berkas", value=row.get('link') or "")
                    
                    # Logika validasi simpan edit
                    if st.form_submit_button("Update Data"):
                        if not e_nama:
                            st.error("❌ Nama kegiatan tidak boleh kosong!")
                        elif e_kat != "Jurnal" and e_naungan != "Individu" and not e_tujuan:
                            st.error("🚨 Gagal Update! Karena ini berafiliasi (bukan Individu), kolom 'Dikirim ke' WAJIB diisi.")
                        else:
                            update_data(row['id'], e_kat, e_nama, e_dl, e_stat, e_desk, e_link, e_tgl_prop, e_stat_prop, e_naungan, e_tujuan)
                            st.success("Data diperbarui!")
                            st.rerun()
                
                # Tombol hapus taruh di luar form edit biar gampang dipencet
                if st.button("🗑️ Hapus Data", key=f"del_{row['id']}"):
                    hapus_data(row['id'])
                    st.rerun()

    with tab_history:
        st.success(f"**✅ Rekap History:** Target *already done* ada **{selesai_count}**.")
        st.warning(f"**⚠️ Terlewat *deadline*:** ada **{terlewat_count}**.")
        st.divider()
        if not data_history:
            st.write("History kosong.")
        for row in data_history:
            with st.expander(f"{row['nama']} - Terakhir: {row['status']}"):
                if st.button("🗑️ Hapus Permanen", key=f"del_h_{row['id']}"):
                    hapus_data(row['id'])
                    st.rerun()
