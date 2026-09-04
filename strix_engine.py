"""
Strix Pentest Engine for Project-XVOID.
Supports native external Strix CLI binary if installed, or falls back to the
built-in Autonomous Security & Penetration Testing Engine.
"""
from __future__ import annotations

import json
import os
import re
import socket
import ssl
import subprocess
import shutil
import time
from urllib.parse import urlparse
import concurrent.futures
import urllib3
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def run_pentest_scan(target_url: str, timeout: int = 45) -> dict:
    target_url = target_url.strip()
    if not target_url.startswith(("http://", "https://")):
        target_url = "https://" + target_url

    # 1. Try external Strix CLI binary if available in PATH
    strix_bin = shutil.which("strix")
    if strix_bin:
        try:
            res = subprocess.run(
                [strix_bin, "scan", target_url, "--json"],
                capture_output=True, text=True, timeout=timeout
            )
            if res.returncode == 0:
                try:
                    return json.loads(res.stdout)
                except json.JSONDecodeError:
                    return {
                        "scanner": "Strix CLI",
                        "status": "completed",
                        "target": target_url,
                        "output": res.stdout.strip()
                    }
        except Exception:
            pass  # Fallback to native engine

    # 2. Native Strix Pentest Engine
    return run_native_pentest(target_url, timeout=timeout)


def run_native_pentest(target_url: str, timeout: int = 15) -> dict:
    parsed = urlparse(target_url)
    hostname = parsed.hostname or target_url
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    scheme = parsed.scheme or "https"

    start_time = time.time()
    vulnerabilities = []
    headers_audit = {}
    ssl_audit = {}
    sensitive_files = []
    open_ports = []
    tech_stack = []

    # 1. Host Resolution
    ip_address = None
    try:
        ip_address = socket.gethostbyname(hostname)
    except socket.gaierror:
        return {
            "scanner": "Strix Autonomous Pentest Engine",
            "status": "failed",
            "target": target_url,
            "error": f"Domain target '{hostname}' tidak dapat ditemukan atau tidak aktif di internet (DNS NXDOMAIN / [Errno 11001]). Pastikan domain sudah terdaftar, DNS aktif, dan server sedang online."
        }
    except Exception as e:
        return {
            "scanner": "Strix Autonomous Pentest Engine",
            "status": "failed",
            "target": target_url,
            "error": f"Gagal me-resolve domain target ({hostname}): {str(e)}"
        }

    # 2. Port Recon (Fast Multi-threaded TCP Port Scan)
    ports_to_check = [21, 22, 80, 443, 3000, 3306, 5432, 6379, 8080, 8443]
    def check_port(p):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.2)
        try:
            if s.connect_ex((ip_address, p)) == 0:
                service_map = {
                    21: "FTP", 22: "SSH", 80: "HTTP", 443: "HTTPS",
                    3000: "Node/Web", 3306: "MySQL", 5432: "PostgreSQL",
                    6379: "Redis", 8080: "HTTP-Proxy/Alt", 8443: "HTTPS-Alt"
                }
                return {"port": p, "service": service_map.get(p, "Unknown"), "state": "OPEN"}
        except Exception:
            pass
        finally:
            s.close()
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(check_port, ports_to_check)
        for r in results:
            if r:
                open_ports.append(r)

    # Check for exposed database/redis/ftp ports
    for p in open_ports:
        if p["port"] in [21, 3306, 5432, 6379]:
            vulnerabilities.append({
                "severity": "HIGH",
                "title": f"Port Layanan Database/FTP Terbuka ke Publik ({p['port']}/{p['service']})",
                "description": f"Port {p['port']} ({p['service']}) terdeteksi terbuka langsung ke jaringan internet tanpa firewall atau VPN restriction.",
                "remediation": f"Tutup port {p['port']} menggunakan firewall (iptables/UFW/Security Group) atau batasi akses hanya ke IP internal."
            })

    # 3. SSL / TLS Handshake & Certificate Audit
    if scheme == "https" or any(p["port"] == 443 for p in open_ports):
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = True
            ctx.verify_mode = ssl.CERT_REQUIRED
            with socket.create_connection((hostname, 443), timeout=4.0) as sock:
                with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    proto_version = ssock.version()

                    subject = dict(x[0] for x in cert.get("subject", []))
                    issuer = dict(x[0] for x in cert.get("issuer", []))
                    not_after = cert.get("notAfter", "")
                    sans = [x[1] for x in cert.get("subjectAltName", []) if x[0] == "DNS"]

                    ssl_audit = {
                        "valid": True,
                        "protocol": proto_version,
                        "cipher": cipher[0] if cipher else "Unknown",
                        "bits": cipher[2] if cipher and len(cipher) > 2 else "Unknown",
                        "subject": subject.get("commonName", hostname),
                        "issuer": issuer.get("organizationName") or issuer.get("commonName", "Unknown"),
                        "expires": not_after,
                        "alt_names_count": len(sans)
                    }

                    if proto_version in ["TLSv1", "TLSv1.1", "SSLv3", "SSLv2"]:
                        vulnerabilities.append({
                            "severity": "HIGH",
                            "title": f"Protokol SSL/TLS Usang Digunakan ({proto_version})",
                            "description": f"Server mendukung negosiasi {proto_version} yang rentan terhadap POODLE/BEAST/DROWN attacks.",
                            "remediation": "Nonaktifkan TLS 1.0/1.1 pada web server (Nginx/Apache) dan hanya izinkan TLS 1.2 serta TLS 1.3."
                        })
        except ssl.SSLCertVerificationError as e:
            ssl_audit = {"valid": False, "error": str(e)}
            vulnerabilities.append({
                "severity": "HIGH",
                "title": "Sertifikat SSL Tidak Valid atau Self-Signed",
                "description": f"Verifikasi sertifikat gagal: {str(e)}",
                "remediation": "Pasang sertifikat SSL yang valid dari Otoritas Sertifikat (CA) tepercaya seperti Let's Encrypt atau DigiCert."
            })
        except Exception as e:
            ssl_audit = {"valid": False, "error": str(e)}

    # 4. HTTP Headers & Web Application Security Audit
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) StrixPentestScanner/2.0 Project-XVOID"
    }
    session = requests.Session()
    resp = None
    try:
        resp = session.get(target_url, headers=headers, timeout=6.0, verify=False, allow_redirects=True)
    except Exception as e:
        vulnerabilities.append({
            "severity": "MEDIUM",
            "title": "Koneksi HTTP/HTTPS Target Gagal",
            "description": f"Permintaan ke target gagal: {str(e)}",
            "remediation": "Pastikan web server aktif dan menerima koneksi dari IP luar."
        })

    if resp is not None:
        resp_headers = {k.lower(): v for k, v in resp.headers.items()}

        # Server Information Disclosure
        server_header = resp_headers.get("server")
        if server_header:
            tech_stack.append(f"Server: {server_header}")
            if any(char.isdigit() for char in server_header):
                vulnerabilities.append({
                    "severity": "LOW",
                    "title": "Kebocoran Versi Web Server (Information Disclosure)",
                    "description": f"Header 'Server: {server_header}' mengekspos versi software yang digunakan.",
                    "remediation": "Sembunyikan nomor versi server (misal: 'server_tokens off;' di Nginx atau 'ServerSignature Off' di Apache)."
                })

        x_powered_by = resp_headers.get("x-powered-by")
        if x_powered_by:
            tech_stack.append(f"Powered-By: {x_powered_by}")
            vulnerabilities.append({
                "severity": "LOW",
                "title": "Kebocoran Header X-Powered-By",
                "description": f"Header 'X-Powered-By: {x_powered_by}' memberitahu penyerang teknologi framework yang digunakan.",
                "remediation": "Hapus header 'X-Powered-By' pada konfigurasi aplikasi atau reverse proxy."
            })

        # Security Headers Audit
        # 1. HSTS
        hsts = resp_headers.get("strict-transport-security")
        headers_audit["Strict-Transport-Security"] = bool(hsts)
        if not hsts and scheme == "https":
            vulnerabilities.append({
                "severity": "MEDIUM",
                "title": "Missing HTTP Strict Transport Security (HSTS)",
                "description": "Header HSTS tidak ditemukan pada target HTTPS. Target rentan terhadap serangan SSL Striping / Man-In-The-Middle.",
                "remediation": "Tambahkan header 'Strict-Transport-Security: max-age=31536000; includeSubDomains; preload'."
            })

        # 2. CSP
        csp = resp_headers.get("content-security-policy")
        headers_audit["Content-Security-Policy"] = bool(csp)
        if not csp:
            vulnerabilities.append({
                "severity": "MEDIUM",
                "title": "Missing Content-Security-Policy (CSP)",
                "description": "Aplikasi tidak memiliki header CSP. Hal ini meningkatkan risiko eksploitasi Cross-Site Scripting (XSS) dan Data Injection.",
                "remediation": "Konfigurasi header 'Content-Security-Policy' dengan membatasi script-src, object-src, dan default-src."
            })
        elif "unsafe-inline" in csp or "unsafe-eval" in csp:
            vulnerabilities.append({
                "severity": "LOW",
                "title": "CSP Memperbolehkan unsafe-inline / unsafe-eval",
                "description": "Kebijakan CSP mengandung 'unsafe-inline' atau 'unsafe-eval', mengurangi efektivitas proteksi XSS.",
                "remediation": "Gunakan nonce atau sha256 hash untuk inline script daripada 'unsafe-inline'."
            })

        # 3. X-Frame-Options
        xfo = resp_headers.get("x-frame-options")
        headers_audit["X-Frame-Options"] = bool(xfo)
        if not xfo and not (csp and "frame-ancestors" in csp):
            vulnerabilities.append({
                "severity": "MEDIUM",
                "title": "Missing X-Frame-Options (Rentan Clickjacking)",
                "description": "Halaman web dapat di-embed dalam <iframe> di domain luar, memungkinkan serangan Clickjacking / UI Redressing.",
                "remediation": "Tambahkan header 'X-Frame-Options: SAMEORIGIN' atau 'DENY'."
            })

        # 4. X-Content-Type-Options
        xcto = resp_headers.get("x-content-type-options")
        headers_audit["X-Content-Type-Options"] = bool(xcto)
        if not xcto or xcto.lower() != "nosniff":
            vulnerabilities.append({
                "severity": "LOW",
                "title": "Missing X-Content-Type-Options: nosniff",
                "description": "Browser dapat melakukan MIME sniffing terhadap file yang diunggah atau resource static.",
                "remediation": "Tambahkan header 'X-Content-Type-Options: nosniff'."
            })

        # 5. Referrer-Policy
        rp = resp_headers.get("referrer-policy")
        headers_audit["Referrer-Policy"] = bool(rp)
        if not rp:
            vulnerabilities.append({
                "severity": "INFO",
                "title": "Missing Referrer-Policy",
                "description": "Informasi URL lengkap dapat bocor ke situs eksternal saat pengguna mengklik tautan keluar.",
                "remediation": "Tambahkan header 'Referrer-Policy: strict-origin-when-cross-origin'."
            })

        # 6. Permissions-Policy
        pp = resp_headers.get("permissions-policy") or resp_headers.get("feature-policy")
        headers_audit["Permissions-Policy"] = bool(pp)
        if not pp:
            vulnerabilities.append({
                "severity": "INFO",
                "title": "Missing Permissions-Policy",
                "description": "Akses ke fitur hardware browser (kamera, mikrofon, geolokasi) tidak dibatasi secara eksplisit.",
                "remediation": "Tetapkan Permissions-Policy untuk membatasi fitur sensitif browser."
            })

        # Cookie Audit
        for cookie in resp.cookies:
            cookie_issues = []
            if not cookie.secure and scheme == "https":
                cookie_issues.append("Missing Secure flag")
            if not cookie.has_nonstandard_attr("httponly") and not getattr(cookie, "httponly", False):
                cookie_issues.append("Missing HttpOnly flag")
            if cookie_issues:
                vulnerabilities.append({
                    "severity": "MEDIUM",
                    "title": f"Insecure Cookie Flag ({cookie.name})",
                    "description": f"Cookie '{cookie.name}' terdeteksi dengan kelemahan: {', '.join(cookie_issues)}.",
                    "remediation": f"Pastikan cookie '{cookie.name}' disetel dengan flag 'Secure; HttpOnly; SameSite=Lax'."
                })

    # 5. CORS Misconfiguration Test
    try:
        evil_origin = "https://evil-attacker.com"
        cors_resp = session.get(target_url, headers={"Origin": evil_origin, "User-Agent": headers["User-Agent"]}, timeout=4.0, verify=False)
        acao = cors_resp.headers.get("access-control-allow-origin", "")
        acac = cors_resp.headers.get("access-control-allow-credentials", "").lower()
        if acao == evil_origin and acac == "true":
            vulnerabilities.append({
                "severity": "HIGH",
                "title": "Kritis: CORS Arbitrary Origin dengan Credentials Diizinkan",
                "description": "Server memantulkan Origin penyerang ('evil-attacker.com') dan mengizinkan kredensial ('Access-Control-Allow-Credentials: true'). Penyerang dapat membaca data sensitif korban!",
                "remediation": "Jangan merefleksikan Origin header sembarangan. Gunakan whitelist domain yang ketat."
            })
        elif acao == "*":
            headers_audit["CORS_Wildcard"] = True
    except Exception:
        pass

    # 6. HTTP Methods Enumeration (OPTIONS)
    try:
        opt_resp = session.options(target_url, timeout=3.0, verify=False)
        allowed = opt_resp.headers.get("allow") or opt_resp.headers.get("public")
        if allowed:
            dangerous = [m for m in ["PUT", "DELETE", "TRACE", "CONNECT"] if m in allowed.upper()]
            if dangerous:
                vulnerabilities.append({
                    "severity": "MEDIUM",
                    "title": f"Metode HTTP Berisiko Diizinkan ({', '.join(dangerous)})",
                    "description": f"Metode HTTP berikut diizinkan: {allowed}. Metode TRACE/DELETE/PUT dapat disalahgunakan.",
                    "remediation": "Nonaktifkan metode HTTP yang tidak digunakan pada web server."
                })
    except Exception:
        pass

    # 7. Sensitive Files & Path Probe (Fast HEAD requests)
    sensitive_paths = [
        {"path": "/.git/HEAD", "desc": "Exposed Git Repository (Source Code Disclosure)", "severity": "CRITICAL"},
        {"path": "/.env", "desc": "Exposed Environment File (API Keys / Passwords)", "severity": "CRITICAL"},
        {"path": "/robots.txt", "desc": "Robots.txt File Found", "severity": "INFO"},
        {"path": "/.well-known/security.txt", "desc": "Security.txt Contact Policy", "severity": "INFO"}
    ]

    base_origin = f"{parsed.scheme}://{parsed.netloc}"
    def check_path(item):
        target_path_url = base_origin + item["path"]
        try:
            r = requests.get(target_path_url, headers=headers, timeout=3.0, verify=False, allow_redirects=False)
            if r.status_code == 200 and len(r.text.strip()) > 0:
                # Validate content for .git/HEAD
                if item["path"] == "/.git/HEAD" and not ("ref:" in r.text or len(r.text) == 41):
                    return None
                if item["path"] == "/.env" and not ("=" in r.text and ("APP_" in r.text or "DB_" in r.text or "KEY" in r.text)):
                    return None
                return {
                    "path": item["path"],
                    "url": target_path_url,
                    "status_code": r.status_code,
                    "description": item["desc"],
                    "severity": item["severity"]
                }
        except Exception:
            pass
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        f_results = executor.map(check_path, sensitive_paths)
        for f in f_results:
            if f:
                sensitive_files.append(f)
                if f["severity"] in ["CRITICAL", "HIGH"]:
                    vulnerabilities.append({
                        "severity": f["severity"],
                        "title": f"File Sensitif Terbuka ke Publik: {f['path']}",
                        "description": f"File sensitif ditemukan di {f['url']} dan dapat diunduh tanpa autentikasi.",
                        "remediation": f"Hapus atau blokir akses HTTP ke {f['path']} pada konfigurasi web server."
                    })

    # 8. Compute Overall Security Score & Grade
    # Deductions: CRITICAL: -35, HIGH: -20, MEDIUM: -10, LOW: -5, INFO: 0
    score = 100
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for v in vulnerabilities:
        sev = v.get("severity", "INFO")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
        if sev == "CRITICAL":
            score -= 35
        elif sev == "HIGH":
            score -= 20
        elif sev == "MEDIUM":
            score -= 10
        elif sev == "LOW":
            score -= 5

    score = max(0, min(100, score))
    if score >= 90:
        grade = "A+"
        summary_id = "Sistem memiliki pertahanan keamanan yang sangat baik."
    elif score >= 80:
        grade = "A"
        summary_id = "Keamanan sistem baik dengan sedikit rekomendasi perbaikan."
    elif score >= 70:
        grade = "B"
        summary_id = "Ditemukan beberapa kelemahan konfigurasi keamanan standar."
    elif score >= 55:
        grade = "C"
        summary_id = "Perlu perhatian segera! Ditemukan celah keamanan tingkat sedang."
    elif score >= 40:
        grade = "D"
        summary_id = "Peringatan: Sistem memiliki kerentanan berisiko tinggi."
    else:
        grade = "F"
        summary_id = "Kritis! Terdeteksi celah fatal yang membahayakan integritas sistem."

    duration_sec = round(time.time() - start_time, 2)

    return {
        "scanner": "Strix Autonomous Pentest Engine",
        "status": "completed",
        "target": target_url,
        "host": hostname,
        "ip": ip_address,
        "scan_time": duration_sec,
        "security_score": score,
        "grade": grade,
        "summary": summary_id,
        "statistics": {
            "total_vulnerabilities": len(vulnerabilities),
            "by_severity": severity_counts
        },
        "vulnerabilities": vulnerabilities,
        "security_headers": headers_audit,
        "ssl_tls": ssl_audit,
        "open_ports": open_ports,
        "sensitive_files": sensitive_files,
        "tech_stack": tech_stack
    }
