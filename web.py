from flask import Flask, render_template, request, abort
import os
from OpenSSL import SSL, crypto
import threading
from waitress import serve

# Buat dua instance Flask untuk website utama (HTTPS) dan panel admin (HTTP)
app_main = Flask(__name__)
app_admin = Flask(__name__)

CERT_FILE = "cert.pem"
KEY_FILE = "key.pem"

def generate_self_signed_cert(cert_file, key_file):
    """Membuat sertifikat SSL self-signed jika belum ada."""
    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        key = crypto.PKey()
        key.generate_key(crypto.TYPE_RSA, 2048)

        cert = crypto.X509()
        cert.get_subject().CN = "localhost"
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)  # 10 tahun
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(key)
        cert.sign(key, "sha256")

        with open(cert_file, "wb") as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        with open(key_file, "wb") as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

        print("Sertifikat SSL otomatis dibuat!")

# Generate sertifikat jika belum ada
generate_self_signed_cert(CERT_FILE, KEY_FILE)

ASCII_LOGO = """
 __ __ _____ _____    __ _____ _____    _____ _____ _____ _____ 
|  |  |  |  |  |  |__|  |     |   | |  |  |  |     |   __|_   _|
|_   _|     |  |  |  |  |-   -| | | |  |     |  |  |__   | | |  
  |_| |__|__|_____|_____|_____|_|___|  |__|__|_____|_____| |_|
"""

# Website utama (HTTPS)
@app_main.route('/')
def home():
    if not os.path.exists("templates/home.html"):
        return "Error: home.html tidak ditemukan!", 404
    return render_template("home.html", ascii_logo=ASCII_LOGO)

@app_main.route('/page')
def custom_page():
    page = request.args.get("name", "home")
    page_path = f"templates/{page}.html"
    
    if not os.path.exists(page_path) or ".." in page:
        abort(404)  # Hindari Path Traversal dan file yang tidak ada
    
    return render_template(f"{page}.html")

# Panel admin (HTTP) untuk pengaturan hosting
@app_admin.route('/')
def admin_home():
    return """
    <h1>Panel Admin</h1>
    <p>Gunakan menu di panel ini untuk mengelola hosting Anda.</p>
    <a href='/hosting'>Pengaturan Hosting</a>
    """

@app_admin.route('/hosting', methods=['GET', 'POST'])
def hosting():
    if request.method == 'POST':
        domain = request.form.get("domain")
        server_ip = request.form.get("server_ip")
        ssl_enabled = request.form.get("ssl_enabled") == "on"
        return f"""
        <h1>Konfigurasi Hosting</h1>
        <p><strong>Domain:</strong> {domain}</p>
        <p><strong>Server IP:</strong> {server_ip}</p>
        <p><strong>SSL:</strong> {'Diaktifkan' if ssl_enabled else 'Tidak Diaktifkan'}</p>
        """
    return """
    <h1>Pengaturan Hosting</h1>
    <form method="post">
        <label>Domain: <input type="text" name="domain" required></label><br>
        <label>Server IP: <input type="text" name="server_ip" required></label><br>
        <label>SSL: <input type="checkbox" name="ssl_enabled"></label><br>
        <button type="submit">Simpan</button>
    </form>
    """

def run_main_server():
    print("Menjalankan server utama di https://0.0.0.0:5000")
    context = (CERT_FILE, KEY_FILE)
    app_main.run(host="0.0.0.0", port=5000, ssl_context=context, threaded=True)

def run_admin_server():
    print("Menjalankan panel admin di http://0.0.0.0:5001")
    serve(app_admin, host="0.0.0.0", port=5001, threads=2)

if __name__ == '__main__':
    threading.Thread(target=run_main_server, daemon=True).start()
    threading.Thread(target=run_admin_server, daemon=True).start()
    while True:  # Mencegah script langsung berhenti
        pass
