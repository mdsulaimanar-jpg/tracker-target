from playwright.sync_api import sync_playwright
import time

# Masukin link web utama lu di sini (Ganti sama link web Streamlit lu yang asli)
URL = "https://tracker-target-gzqotdkrcc9b5he4drgvx2.streamlit.app/"

def run():
    with sync_playwright() as p:
        print("Membuka browser tanpa layar...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print(f"Mengunjungi {URL}...")
        # Buka web dan tunggu sampai loading kelar
        page.goto(URL, timeout=60000)
        
        # Nunggu 15 detik ngasih waktu buat Streamlit nyalain WebSocket-nya
        time.sleep(15) 
        print("Web berhasil dibangunin! Tidur lagi bot...")
        
        browser.close()

if __name__ == "__main__":
    run()