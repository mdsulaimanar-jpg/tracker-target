import streamlit as st
import time
from urllib.parse import urlencode
from datetime import datetime, timedelta
from supabase import create_client, Client

st.set_page_config(page_title="Tracker Akademik", layout="wide", page_icon="🎯")

# --- CSS INJECTION: BIKIN UI MAKIN SMOOTH & MODERN ---
smooth_ui_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Efek hover smooth untuk kotak metrik */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e6e6ea;
        padding: 5% 5% 5% 10%;
        border-radius: 12px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.03);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 4px 4px 15px rgba(0,0,0,0.1);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
    </style>
"""
st.markdown(smooth_ui_style, unsafe_allow_html=True)

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
        st.error("❌ Login gagal! Cek email/password lu.")

def register_user(email, password):
    try:
        supabase.auth.sign_up({"email": email, "password": password})
        st.success("✅ Berhasil daftar! Silakan Login.")
    except Exception as e:
        st.error(f"❌ Gagal daftar: {e}")

def logout_user():
    if st.session_state.user_email != "mentor_vip":
        supabase.auth.sign_out()
    st.session_state.user_email = None
    st.query_params.clear()
    st.rerun()

# ==========================================
# HALAMAN LOGIN
# ==========================================
if st.session_state.user_email is None:
    st.markdown("<h1 style='text-align: center; color: #ff4b4b; padding-top: 50px;'>🎯 Tracker Akademik</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Sistem Manajemen Target & Eksekusi Jurnal/Kompetisi</p><br>", unsafe_allow_html=True)
    
    col_empty1, col_login, col_empty2 = st.columns([1, 2, 1])
    with col_login:
        with st.container(border=True):
            tab_login, tab_register = st.tabs(["🔐 Masuk", "📝 Daftar Baru"])
            
            with tab_login:
                email_login = st.text_input("Email")
                pass_login = st.text_input("Password", type="password")
                if st.button("Masuk Dashboard", use_container_width=True, type="primary"):
                    login_user(email_login, pass_login)
                    
            with tab_register:
                email_reg = st.text_input("Email Baru", key="reg_email")
                pass_reg = st.text_input("Password Baru", type="password", key="reg_pass")
                if st.button("Daftar Akun", use_container_width=True):
                    register_user(email_reg, pass_reg)

# ==========================================
# HALAMAN UTAMA (DASHBOARD)
# ==========================================
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

    # Header Atas
    col_head1, col_head2 = st.columns([4, 1])
    col_head1.header("🎯 Dashboard Akademik")
    
    with col_head2:
        if st.session_state.user_email == "mentor_vip":
            st.info("👨‍🏫 VIP Mentor", icon="✨")
        else:
            st.markdown(f"**👤 {st.session_state.user_email.split('@')[0]}**")
            if st.button("🚪 Logout", use_container_width=True):
                logout_user()

    # --- FORM TAMBAH DATA ---
    with st.expander("➕ **Klik di sini untuk Tambah Kegiatan Baru**", expanded=False):
        kategori_baru = st.selectbox("Pilih Kategori", ["Jurnal", "Kompetisi", "Funding", "Project", "Pengmas"])
        nama_baru = st.text_input("Nama Kegiatan (Wajib diisi)")
        
        col_m1, col_m2 = st.columns(2)
        deadline_baru = col_m1.date_input("Deadline Utama (Final)")
        status_baru = col_m2.selectbox("Status Akhir", ["Persiapan", "In Review", "Revisi", "Selesai", "Ditolak"])
        
        if kategori_baru != "Jurnal":
            with st.container(border=True):
                st.markdown("##### 📄 Kelengkapan Proposal & Afiliasi")
                col_p3, col_p4 = st.columns(2)
                naungan_prop = col_p3.selectbox("Dinaungi Oleh", ["Individu", "Laboratorium Dasar Komputer", "Telkom University", "Lainnya"])
                wajib_label = " *(Wajib)*" if naungan_prop != "Individu" else ""
                tujuan_prop = col_p4.text_input(f"Dikirim ke Instansi/Penyelenggara{wajib_label}")
                
                col_p1, col_p2 = st.columns(2)
                tgl_prop = col_p1.date_input("Deadline Pengiriman Proposal")
                stat_prop = col_p2.selectbox("Status Proposal", ["Belum Kirim", "Terkirim", "Diterima", "Ditolak"])
        else:
            tgl_prop = None
            stat_prop = "-"
            naungan_prop = "Individu"
            tujuan_prop = "-"
            
        with st.container(border=True):
            st.markdown("##### 📝 Informasi Tambahan")
            col_i1, col_i2 = st.columns(2)
            deskripsi_baru = col_i1.text_area("Deskripsi Singkat / Catatan")
            link_baru = col_i2.text_input("Link Berkas (Drive / Web)")

        if st.button("Simpan Kegiatan", type="primary", use_container_width=True):
            if not nama_baru:
                st.error("❌ Nama kegiatan tidak boleh kosong!")
            elif kategori_baru != "Jurnal" and naungan_prop != "Individu" and not tujuan_prop:
                st.error("🚨 Gagal Menyimpan! Karena berafiliasi, kolom 'Dikirim ke' WAJIB diisi.")
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
                st.toast('🚀 Data berhasil ditambahkan!', icon='✅')
                time.sleep(1)
                st.rerun()

    st.divider()

    # --- AMBIL DATA DARI SUPABASE ---
    response = supabase.table("kegiatan").select("*").eq("owner_email", st.session_state.user_email).execute()
    data_semua = response.data

    today = datetime.now().date()
    data_aktif = []
    data_history = []

    hitung_kat_aktif = {"Jurnal": 0, "Kompetisi": 0, "Funding": 0, "Project": 0, "Pengmas": 0}
    hitung_kat_hist = {"Jurnal": 0, "Kompetisi": 0, "Funding": 0, "Project": 0, "Pengmas": 0}

    for row in data_semua:
        dl_date = datetime.strptime(row['deadline'], "%Y-%m-%d").date()
        if row['status'] == 'Selesai' or (today > (dl_date + timedelta(days=7)) and row['status'] != 'Revisi'):
            data_history.append(row)
            if row['kategori'] in hitung_kat_hist:
                hitung_kat_hist[row['kategori']] += 1
        else:
            data_aktif.append(row)
            if row['kategori'] in hitung_kat_aktif:
                hitung_kat_aktif[row['kategori']] += 1

    total_ongoing = len(data_aktif)
    mendekati_dl = sum(1 for row in data_aktif if 0 <= (datetime.strptime(row['deadline'], "%Y-%m-%d").date() - today).days <= 7)
    total_history = len(data_history)
    selesai_count = sum(1 for row in data_history if row['status'] == 'Selesai')
    terlewat_count = total_history - selesai_count

    # --- TAMPILAN TAB BAWAH ---
    tab_aktif, tab_history = st.tabs(["📌 On-Going Target", "🗄️ History & Arsip"])
    
    kategori_list = ["Jurnal", "Kompetisi", "Funding", "Project", "Pengmas"]
    status_list = ["Persiapan", "In Review", "Revisi", "Selesai", "Ditolak"]
    naungan_list = ["Individu", "Laboratorium Dasar Komputer", "Telkom University", "Lainnya"]
    stat_prop_list = ["Belum Kirim", "Terkirim", "Diterima", "Ditolak"]

    # ==========================
    # TAB 1: AKTIF
    # ==========================
    with tab_aktif:
        col_met1, col_met2, col_met3 = st.columns(3)
        col_met1.metric(label="📌 Total On-Going", value=total_ongoing)
        
        delta_stat = f"-{mendekati_dl} Butuh Perhatian!" if mendekati_dl > 0 else "Aman"
        col_met2.metric(label="🚨 Mendekati Deadline (<7 Hari)", value=mendekati_dl, delta=delta_stat, delta_color="inverse")
        
        revisi_count = sum(1 for row in data_aktif if row['status'] == 'Revisi')
        delta_rev = f"-{revisi_count} Perlu Diperbaiki" if revisi_count > 0 else "Bersih"
        col_met3.metric(label="🔴 Butuh Revisi", value=revisi_count, delta=delta_rev, delta_color="inverse")
        
        st.markdown("###### 📊 Breakdown Kategori Aktif")
        cb1, cb2, cb3, cb4, cb5 = st.columns(5)
        cb1.metric("📝 Jurnal", hitung_kat_aktif["Jurnal"])
        cb2.metric("🏆 Kompetisi", hitung_kat_aktif["Kompetisi"])
        cb3.metric("💰 Funding", hitung_kat_aktif["Funding"])
        cb4.metric("🚀 Project", hitung_kat_aktif["Project"])
        cb5.metric("🤝 Pengmas", hitung_kat_aktif["Pengmas"])
        
        st.divider()

        filter_aktif = st.radio("🔍 Tampilkan Data:", ["Semua", "Jurnal", "Kompetisi", "Funding", "Project", "Pengmas"], horizontal=True, key="filter_aktif")

        data_aktif_filtered = [r for r in data_aktif if filter_aktif == "Semua" or r['kategori'] == filter_aktif]

        if not data_aktif_filtered:
            st.info(f"Belum ada target aktif untuk kategori {filter_aktif}.")
        for row in data_aktif_filtered:
            dl_date = datetime.strptime(row['deadline'], "%Y-%m-%d").date()
            days_left = (dl_date - today).days
            
            peringatan = ""
            if row['status'] == 'Revisi':
                peringatan = "🔴 "
            elif 0 <= days_left <= 7:
                peringatan = "🚨 "
            elif days_left < 0:
                peringatan = "⚠️ "

            with st.expander(f"{peringatan}[{row['kategori']}] {row['nama']} (DL Final: {row['deadline']})"):
                if row['status'] == 'Revisi':
                    st.error("📌 **REVISI!** Segera perbaiki dan kirim ulang.")
                elif 0 <= days_left <= 7:
                    st.warning(f"⏳ **Hati-hati!** Sisa waktu tinggal {days_left} hari lagi menuju deadline!")
                elif days_left < 0:
                    st.error(f"⚠️ **TERLEWAT DEADLINE!** Sudah lewat {abs(days_left)} hari.")
                
                col_det1, col_det2 = st.columns(2)
                col_det1.write(f"**Status:** `{row['status']}`")
                col_det2.write(f"**Deadline:** `{row['deadline']}`")
                st.write(f"**Deskripsi:** {row.get('deskripsi', '-')}")
                if row.get('link', ''):
                    st.markdown(f"🔗 **[Buka Tautan Berkas/Drive]({row['link']})**")
                
                if row['kategori'] != "Jurnal":
                    st.info(f"🏢 **Afiliasi:** {row.get('naungan', '-')} ➡️ **Tujuan:** {row.get('tujuan_proposal', '-')}")
                    st.write(f"📄 **Status Proposal:** {row.get('status_proposal', '-')} (DL Proposal: {row.get('tgl_proposal', '-')})")
                
                st.divider()
                
                with st.form(key=f"edit_{row['id']}"):
                    st.markdown("##### ✏️ Edit Data")
                    e_kat = st.selectbox("Kategori", kategori_list, index=kategori_list.index(row['kategori']) if row['kategori'] in kategori_list else 0, key=f"kat_{row['id']}")
                    e_nama = st.text_input("Nama Kegiatan", value=row['nama'], key=f"nama_{row['id']}")
                    
                    col_e1, col_e2 = st.columns(2)
                    e_dl = col_e1.date_input("Deadline Utama", value=dl_date, key=f"dl_{row['id']}")
                    e_stat = col_e2.selectbox("Status Akhir", status_list, index=status_list.index(row['status']) if row['status'] in status_list else 0, key=f"stat_{row['id']}")
                    
                    if e_kat != "Jurnal":
                        col_ep1, col_ep2 = st.columns(2)
                        idx_naungan = naungan_list.index(row.get('naungan')) if row.get('naungan') in naungan_list else 0
                        e_naungan = col_ep1.selectbox("Dinaungi Oleh", naungan_list, index=idx_naungan, key=f"naungan_{row['id']}")
                        
                        wajib_label_e = " (Wajib Diisi)" if e_naungan != "Individu" else ""
                        e_tujuan = col_ep2.text_input(f"Dikirim ke Instansi/Penyelenggara{wajib_label_e}", value=row.get('tujuan_proposal') or "", key=f"tujuan_{row['id']}")
                        
                        col_ep3, col_ep4 = st.columns(2)
                        prop_date_val = datetime.strptime(row['tgl_proposal'], "%Y-%m-%d").date() if row.get('tgl_proposal') else today
                        e_tgl_prop = col_ep3.date_input("Deadline Proposal", value=prop_date_val, key=f"tglp_{row['id']}")
                        
                        idx_stat_prop = stat_prop_list.index(row.get('status_proposal')) if row.get('status_proposal') in stat_prop_list else 0
                        e_stat_prop = col_ep4.selectbox("Status Proposal", stat_prop_list, index=idx_stat_prop, key=f"statp_{row['id']}")
                    else:
                        e_tgl_prop = None
                        e_stat_prop = "-"
                        e_naungan = "Individu"
                        e_tujuan = "-"
                        
                    col_ei1, col_ei2 = st.columns(2)
                    e_desk = col_ei1.text_area("Deskripsi", value=row.get('deskripsi') or "", key=f"desk_{row['id']}")
                    e_link = col_ei2.text_input("Link Berkas", value=row.get('link') or "", key=f"link_{row['id']}")
                    
                    if st.form_submit_button("💾 Update Data"):
                        if not e_nama:
                            st.error("❌ Nama kegiatan tidak boleh kosong!")
                        elif e_kat != "Jurnal" and e_naungan != "Individu" and not e_tujuan:
                            st.error("🚨 Gagal Update! Karena berafiliasi, kolom 'Dikirim ke' WAJIB diisi.")
                        else:
                            update_data(row['id'], e_kat, e_nama, e_dl, e_stat, e_desk, e_link, e_tgl_prop, e_stat_prop, e_naungan, e_tujuan)
                            st.toast('✨ Data berhasil di-update!', icon='✅')
                            time.sleep(1)
                            st.rerun()
                
                if st.button("🗑️ Hapus Data", key=f"del_{row['id']}"):
                    hapus_data(row['id'])
                    st.rerun()

    # ==========================
    # TAB 2: HISTORY
    # ==========================
    with tab_history:
        col_hm1, col_hm2 = st.columns(2)
        col_hm1.metric(label="✅ Already Done", value=selesai_count)
        col_hm2.metric(label="⚠️ Terlewat Deadline", value=terlewat_count)
        
        st.markdown("###### 📊 Breakdown Kategori History")
        ch1, ch2, ch3, ch4, ch5 = st.columns(5)
        ch1.metric("📝 Jurnal", hitung_kat_hist["Jurnal"])
        ch2.metric("🏆 Kompetisi", hitung_kat_hist["Kompetisi"])
        ch3.metric("💰 Funding", hitung_kat_hist["Funding"])
        ch4.metric("🚀 Project", hitung_kat_hist["Project"])
        ch5.metric("🤝 Pengmas", hitung_kat_hist["Pengmas"])

        st.divider()
        
        filter_hist = st.radio("🔍 Tampilkan History:", ["Semua", "Jurnal", "Kompetisi", "Funding", "Project", "Pengmas"], horizontal=True, key="filter_hist")
        
        data_hist_filtered = [r for r in data_history if filter_hist == "Semua" or r['kategori'] == filter_hist]
        
        if not data_hist_filtered:
            st.info(f"Belum ada history untuk kategori {filter_hist}.")
        for row in data_hist_filtered:
            dl_date = datetime.strptime(row['deadline'], "%Y-%m-%d").date()
            ikon_hist = "✅ " if row['status'] == 'Selesai' else "⚠️ "
            
            with st.expander(f"{ikon_hist} [{row['kategori']}] {row['nama']} - Terakhir: {row['status']}"):
                st.write(f"**Deskripsi:** {row.get('deskripsi', '-')}")
                if row.get('link', ''):
                    st.markdown(f"🔗 **[Buka Tautan Berkas/Drive]({row['link']})**")
                
                st.divider()
                
                with st.form(key=f"edit_hist_{row['id']}"):
                    st.markdown("##### ✏️ Edit Data (Bangkitkan dari History)")
                    e_kat = st.selectbox("Kategori", kategori_list, index=kategori_list.index(row['kategori']) if row['kategori'] in kategori_list else 0, key=f"kat_h_{row['id']}")
                    e_nama = st.text_input("Nama Kegiatan", value=row['nama'], key=f"nama_h_{row['id']}")
                    
                    col_e1, col_e2 = st.columns(2)
                    e_dl = col_e1.date_input("Deadline Utama", value=dl_date, key=f"dl_h_{row['id']}")
                    e_stat = col_e2.selectbox("Status Akhir", status_list, index=status_list.index(row['status']) if row['status'] in status_list else 0, key=f"stat_h_{row['id']}")
                    
                    if e_kat != "Jurnal":
                        col_ep1, col_ep2 = st.columns(2)
                        idx_naungan = naungan_list.index(row.get('naungan')) if row.get('naungan') in naungan_list else 0
                        e_naungan = col_ep1.selectbox("Dinaungi Oleh", naungan_list, index=idx_naungan, key=f"naungan_h_{row['id']}")
                        
                        wajib_label_e = " (Wajib Diisi)" if e_naungan != "Individu" else ""
                        e_tujuan = col_ep2.text_input(f"Dikirim ke Instansi/Penyelenggara{wajib_label_e}", value=row.get('tujuan_proposal') or "", key=f"tujuan_h_{row['id']}")
                        
                        col_ep3, col_ep4 = st.columns(2)
                        prop_date_val = datetime.strptime(row['tgl_proposal'], "%Y-%m-%d").date() if row.get('tgl_proposal') else today
                        e_tgl_prop = col_ep3.date_input("Deadline Proposal", value=prop_date_val, key=f"tglp_h_{row['id']}")
                        
                        idx_stat_prop = stat_prop_list.index(row.get('status_proposal')) if row.get('status_proposal') in stat_prop_list else 0
                        e_stat_prop = col_ep4.selectbox("Status Proposal", stat_prop_list, index=idx_stat_prop, key=f"statp_h_{row['id']}")
                    else:
                        e_tgl_prop = None
                        e_stat_prop = "-"
                        e_naungan = "Individu"
                        e_tujuan = "-"
                        
                    col_ei1, col_ei2 = st.columns(2)
                    e_desk = col_ei1.text_area("Deskripsi", value=row.get('deskripsi') or "", key=f"desk_h_{row['id']}")
                    e_link = col_ei2.text_input("Link Berkas", value=row.get('link') or "", key=f"link_h_{row['id']}")
                    
                    if st.form_submit_button("💾 Update Data"):
                        if not e_nama:
                            st.error("❌ Nama kegiatan tidak boleh kosong!")
                        elif e_kat != "Jurnal" and e_naungan != "Individu" and not e_tujuan:
                            st.error("🚨 Gagal Update! Karena berafiliasi, kolom 'Dikirim ke' WAJIB diisi.")
                        else:
                            update_data(row['id'], e_kat, e_nama, e_dl, e_stat, e_desk, e_link, e_tgl_prop, e_stat_prop, e_naungan, e_tujuan)
                            st.toast('✨ Data berhasil di-update!', icon='✅')
                            time.sleep(1)
                            st.rerun()
                
                if st.button("🗑️ Hapus Permanen", key=f"del_h_{row['id']}"):
                    hapus_data(row['id'])
                    st.rerun()
