from __future__ import annotations

import json
import os
import sys
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler, ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Import dashboard service and helpers
import dashboard

PORT = int(os.environ.get("PORT", 3000))
_ROOT_CANDIDATES = [
    Path(__file__).resolve().parent,
    Path(__file__).resolve().parent.parent,
    Path(os.getcwd()),
]
WEB_DIR = next((p / "web" for p in _ROOT_CANDIDATES if (p / "web").exists()), Path(__file__).resolve().parent / "web")
service = dashboard.LeviathanService()

STATIC_MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".htm": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".webp": "image/webp",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".ttf": "font/ttf",
    ".txt": "text/plain; charset=utf-8",
    ".map": "application/json",
}


class BaseApiHandler(BaseHTTPRequestHandler):

    def end_headers(self):
        headers_str = b"".join(getattr(self, "_headers_buffer", []))
        if b"Cache-Control:" not in headers_str:
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()

    def _serve_static_file(self, req_path: str):
        rel = req_path.lstrip("/")
        if not rel or rel in ("index.html", "web", "web/"):
            target = (WEB_DIR / "index.html").resolve()
        elif rel.startswith("web/"):
            target = (WEB_DIR / rel[4:]).resolve()
        else:
            target = (WEB_DIR / rel).resolve()

        # Prevent directory traversal attacks
        web_resolved = WEB_DIR.resolve()
        try:
            target.relative_to(web_resolved)
        except ValueError:
            self.send_error(403, "Access denied")
            return

        if target.is_file():
            ext = target.suffix.lower()
            mime = STATIC_MIME_TYPES.get(ext, "application/octet-stream")
            try:
                with open(target, "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(data)))
                if ext in [".png", ".jpg", ".jpeg", ".ico", ".svg", ".woff2", ".ttf"]:
                    self.send_header("Cache-Control", "public, max-age=86400")
                elif ext in [".css", ".js"]:
                    self.send_header("Cache-Control", "public, max-age=3600")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(data)
                return
            except Exception as e:
                self.send_error(500, f"Error reading file: {e}")
                return
        self.send_error(404, "File not found")

    def _send_json(self, status_code: int, data: dict):
        response_bytes = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(response_bytes)

    def _read_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0:
            return {}
        body = self.rfile.read(content_length)
        try:
            return json.loads(body.decode("utf-8"))
        except Exception:
            return {}

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def _resolve_request_path(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Support Vercel serverless rewrites via ?__path=...
        if "__path" in query:
            sub = query["__path"][0].lstrip("/")
            path = f"/api/{sub}"
        elif self.headers.get("x-forwarded-uri"):
            path = urllib.parse.urlparse(self.headers["x-forwarded-uri"]).path
        elif self.headers.get("x-invoke-path"):
            path = urllib.parse.urlparse(self.headers["x-invoke-path"]).path

        return path, query

    def do_GET(self):
        path, query = self._resolve_request_path()

        if not path.startswith("/api/"):
            return self._serve_static_file(path)

        if path == "/api/web2apk/status":
            build_id = query.get("build_id", [""])[0]
            if not build_id:
                return self._send_json(400, {"error": "Parameter build_id dibutuhkan"})
            try:
                res = service.web2apk_status(build_id)
                return self._send_json(200, res if isinstance(res, dict) else {"result": res})
            except Exception as exc:
                return self._send_json(500, {"error": str(exc)})

        if path == "/api/image-proxy":
            img_url = query.get("url", [""])[0]
            if not img_url:
                self.send_error(400, "Parameter url dibutuhkan")
                return
            try:
                proxy_headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
                }
                resp = service.http.session.get(img_url, headers=proxy_headers, timeout=20)
                if resp.ok and len(resp.content) > 500:
                    self.send_response(200)
                    self.send_header("Content-Type", resp.headers.get("Content-Type", "image/jpeg"))
                    self.send_header("Content-Length", str(len(resp.content)))
                    self.send_header("Cache-Control", "public, max-age=86400")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(resp.content)
                    return
                else:
                    self.send_error(resp.status_code, "Gagal mengambil gambar dari sumber")
                    return
            except Exception as exc:
                self.send_error(500, f"Proxy error: {exc}")
                return

        if path == "/api/downloader/proxy":
            media_url = query.get("url", [""])[0]
            filename = query.get("filename", ["media_download.mp4"])[0]
            if not media_url:
                self.send_error(400, "Parameter url dibutuhkan")
                return
            try:
                import shutil
                req = urllib.request.Request(media_url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "*/*"
                })
                with urllib.request.urlopen(req, timeout=30) as remote_stream:
                    content_type = remote_stream.headers.get("Content-Type", "application/octet-stream")
                    content_length = remote_stream.headers.get("Content-Length")
                    self.send_response(200)
                    self.send_header("Content-Type", content_type)
                    if content_length:
                        self.send_header("Content-Length", content_length)
                    safe_fn = urllib.parse.quote(filename)
                    self.send_header("Content-Disposition", f'attachment; filename="{safe_fn}"; filename*=UTF-8\'\'{safe_fn}')
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    shutil.copyfileobj(remote_stream, self.wfile)
                    return
            except Exception as exc:
                self.send_error(500, f"Gagal mengunduh media: {exc}")
                return

        self.send_error(404, "Endpoint not found")

    def do_POST(self):
        path, _ = self._resolve_request_path()
        body = self._read_json_body()

        # 1. MAGIC LINK SEND
        if path == "/api/magiclink/send":
            version = body.get("version", "v1")
            email = body.get("email", "")
            if not email:
                return self._send_json(400, {"error": "Email tidak boleh kosong"})
            try:
                res = service.send_magic_link(version, email)
                return self._send_json(200, res if isinstance(res, dict) else {"result": res})
            except Exception as exc:
                return self._send_json(500, {"error": str(exc)})

        # 2. MAGIC LINK VERIFY
        elif path == "/api/magiclink/verify":
            version = body.get("version", "v1")
            email = body.get("email", "")
            link = body.get("link", "")
            if not email or not link:
                return self._send_json(400, {"error": "Email dan Link wajib diisi"})
            try:
                res = service.verify_magic_link(version, email, link)
                code = dashboard.extract_order_code(res)
                return self._send_json(200, {"result": res, "code": code, "success": dashboard.is_success_status(res)})
            except Exception as exc:
                return self._send_json(500, {"error": str(exc)})

        # 3. WEB TO APK START
        elif path == "/api/web2apk/start":
            app_name = body.get("appName", "")
            website_url = body.get("websiteUrl", "")
            package_name = body.get("packageName", "")
            version_name = body.get("versionName", "1.0.0")
            version_code = body.get("versionCode", "1")
            icon_url = body.get("appIconUrl", "")
            if not app_name or not website_url or not package_name:
                return self._send_json(400, {"error": "Data aplikasi belum lengkap"})
            try:
                res = service.create_web2apk(app_name, website_url, package_name, version_name, version_code, icon_url)
                return self._send_json(200, res if isinstance(res, dict) else {"result": res})
            except Exception as exc:
                return self._send_json(500, {"error": str(exc)})

        # 4. PAGE SOURCE FETCH
        elif path == "/api/pagesource":
            url = body.get("url", "")
            if not url:
                return self._send_json(400, {"error": "URL website tidak boleh kosong"})
            try:
                res = service.fetch_page_source(url, stylize=True)
                return self._send_json(200, res if isinstance(res, dict) else {"result": res})
            except Exception as exc:
                return self._send_json(500, {"error": str(exc)})

        # 5. WEB TO ZIP
        elif path == "/api/webtozip":
            url = body.get("url", "")
            if not url:
                return self._send_json(400, {"error": "URL website tidak boleh kosong"})
            try:
                payload, download_url = service.web_to_zip(url)
                return self._send_json(200, {"payload": payload, "download_url": download_url})
            except Exception as exc:
                return self._send_json(500, {"error": str(exc)})

        # 6. XVOID AI CHAT
        elif path == "/api/ai/chat":
            prompt = body.get("prompt", "")
            session_id = body.get("sessionId")
            mode = body.get("mode", "strom")
            if not prompt:
                return self._send_json(400, {"error": "Prompt tidak boleh kosong"})
            try:
                res = service.ai_chat(prompt, session_id=session_id, mode=mode)
                reply = dashboard.extract_ai_response_text(res)
                new_session_id = dashboard.extract_session_id(res) or session_id
                return self._send_json(200, {"reply": reply, "sessionId": new_session_id, "mode": mode, "raw": res})
            except Exception as exc:
                return self._send_json(500, {"error": str(exc)})

        # 7. UNIVERSAL DOWNLOADER (TikTok, IG, YouTube, X/Twitter, FB, dll)
        elif path in ("/api/downloader/info", "/api/tiktok/info"):
            url = body.get("url", "").strip()
            if not url:
                return self._send_json(400, {"error": "Tautan atau URL media tidak boleh kosong"})
            try:
                info = service.universal_download_info(url)
                return self._send_json(200, info)
            except Exception as exc:
                return self._send_json(400, {"error": str(exc), "message": str(exc)})

        # 8. CEK NOMOR
        elif path == "/api/ceknomor":
            nomor = body.get("nomor", "").strip()
            lang = body.get("lang", "id")
            region = body.get("region", "ID")
            if not nomor:
                return self._send_json(400, {"error": "Nomor telepon tidak boleh kosong"})
            try:
                result = service.cek_nomor(nomor, lang=lang, region=region)
                return self._send_json(200, result)
            except Exception as exc:
                return self._send_json(500, {"error": str(exc)})

        # 9. BUAT GAMBAR AI (100% STABIL, UNIK & ANTI RATE-LIMIT)
        elif path == "/api/buatgambar":
            prompt = body.get("prompt", "").strip()
            model = body.get("model", "flux")
            aspect_ratio = body.get("aspect_ratio", "1:1")
            style = body.get("style", "none")
            negative_prompt = body.get("negative_prompt", "")
            raw_count = body.get("count", 4)
            try:
                count = max(1, min(4, int(raw_count)))
            except (ValueError, TypeError):
                count = 4

            if not prompt:
                return self._send_json(400, {"error": "Prompt gambar tidak boleh kosong"})
            try:
                import base64
                import random
                import re
                import requests
                import time

                now_ms = int(time.time() * 1000)

                # ─── AUTO TRANSLATE INDONESIAN TO ENGLISH ───
                def translate_id_to_en(text_val: str) -> str:
                    t = text_val.strip()
                    if not t:
                        return ""
                    id_indicators = {
                        "ikan", "kucing", "anjing", "burung", "kuda", "hewan", "binatang",
                        "pemandangan", "gunung", "laut", "pantai", "hutan", "danau", "bunga",
                        "mobil", "motor", "orang", "gadis", "wanita", "pria", "anak", "rumah",
                        "gedung", "langit", "senja", "malam", "pagi", "siang", "sore", "cantik",
                        "indah", "lucu", "keren", "merah", "biru", "hijau", "kuning", "hitam",
                        "putih", "emas", "di", "ke", "dari", "yang", "dan", "dengan", "untuk",
                        "saat", "sedang", "air", "kolam", "sungai", "batu", "pasir", "alam"
                    }
                    words = set(re.findall(r'\b\w+\b', t.lower()))
                    if words.intersection(id_indicators):
                        try:
                            tr_url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(t)}&langpair=id|en"
                            tr_res = requests.get(tr_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=3.5)
                            if tr_res.ok:
                                trans = tr_res.json().get("responseData", {}).get("translatedText", "")
                                if trans and not trans.startswith("MYMEMORY WARNING"):
                                    return trans
                        except Exception:
                            pass
                    return t

                en_prompt = translate_id_to_en(prompt)
                en_negative = translate_id_to_en(negative_prompt) if negative_prompt else ""

                # Anti-monster & anti-mutation negative prompt filter
                anti_monster_filter = "monster, alien, mutated, creepy, deformed, distorted, scary, disfigured, bad anatomy, lowres, ugly"
                full_negative = f"{en_negative}, {anti_monster_filter}" if en_negative else anti_monster_filter

                # Presets gaya visual dan komposisi dalam bahasa Indonesia
                STYLE_PRESET_GROUPS = {
                    "sinematik": [
                        {"style_tag": "Sinematik Layar Lebar", "prefix": "Cinematic wide-angle movie still of", "suffix": ", anamorphic lens flare, dramatic volumetric lighting, 35mm film grain, masterpiece photography"},
                        {"style_tag": "Sudut Sinematik Emas", "prefix": "Breathtaking cinematic eye-level shot of", "suffix": ", warm golden hour illumination, subtle rim light, rich color grading, award-winning cinematography"},
                        {"style_tag": "Atmosfer Film Dramatis", "prefix": "Moody cinematic atmospheric scene depicting", "suffix": ", subtle haze, cinematic depth of field, high contrast natural shadows, ultra realistic"},
                        {"style_tag": "Sinematik Close-up Tajam", "prefix": "Crisp cinematic close-up framing of", "suffix": ", soft background blur bokeh, pristine focus, professional color balance, 8k uhd"}
                    ],
                    "studio": [
                        {"style_tag": "Studio Bersih Minimalis", "prefix": "Minimalist clean studio photography of", "suffix": ", solid neutral backdrop, softbox lighting, perfectly balanced exposure, pristine aesthetic"},
                        {"style_tag": "Studio Lighting Lembut", "prefix": "Elegant studio portrait of", "suffix": ", diffuse soft studio lights, gentle highlights, crisp reflections, premium commercial photography"},
                        {"style_tag": "Studio Estetis Modern", "prefix": "Modern aesthetic high-key studio photo of", "suffix": ", bright harmonious tones, crisp edges, professional product styling, 8k resolution"},
                        {"style_tag": "Studio Kontras Elegan", "prefix": "Dramatic low-key studio portrait of", "suffix": ", artistic chiaroscuro rim lighting, subtle deep shadows, sophisticated look"}
                    ],
                    "anime": [
                        {"style_tag": "Anime Makoto Shinkai", "prefix": "Stunning anime illustration of", "suffix": ", Makoto Shinkai aesthetic, radiant atmospheric glow, vivid expressive colors, detailed scenery"},
                        {"style_tag": "Ilustrasi Anime Halus", "prefix": "Delicate Japanese anime art depicting", "suffix": ", clean digital ink linework, soft pastel gradient shading, enchanting mood, high quality"},
                        {"style_tag": "Gaya Manga Berwarna", "prefix": "Vibrant colored manga cover artwork of", "suffix": ", dynamic composition, bold aesthetic, sharp detailed rendering, masterpiece anime art"},
                        {"style_tag": "Anime Sinematik 4K", "prefix": "Epic Kyoto Animation style cinematic still of", "suffix": ", breathtaking lighting, floating dust particles, emotive atmosphere, 8k uhd"}
                    ],
                    "fantasi": [
                        {"style_tag": "Dunia Fantasi Magis", "prefix": "Epic fantasy concept artwork of", "suffix": ", mystical ethereal glow, magical shimmering particles, enchanting surreal wonderland, masterpiece"},
                        {"style_tag": "Kerajaan Mitos Megah", "prefix": "Mythical fantasy landscape featuring", "suffix": ", majestic atmosphere, ancient fantasy aesthetics, divine lighting rays, hyper-detailed digital painting"},
                        {"style_tag": "Hutan Ajaib Berkilau", "prefix": "Enchanting fairy tale scene of", "suffix": ", glowing bioluminescent flora, twilight celestial lighting, captivating fantasy environment"},
                        {"style_tag": "Mahakarya Seni Mistik", "prefix": "High fantasy artistic concept of", "suffix": ", magical aura, intricate ornate textures, vivid otherworldly colors, award-winning illustration"}
                    ],
                    "cyberpunk": [
                        {"style_tag": "Jalanan Neon Cyberpunk", "prefix": "Futuristic cyberpunk night scene of", "suffix": ", glowing neon signs, wet asphalt reflections, holographic overlays, moody dark sci-fi atmosphere"},
                        {"style_tag": "Kota Futuristik Megah", "prefix": "Breathtaking futuristic sci-fi cityscape featuring", "suffix": ", towering megastructures, flying vehicles, neon beam lighting, ray-tracing 8k"},
                        {"style_tag": "Malam Hujan Cyberpunk", "prefix": "Moody rainy cyberpunk aesthetic of", "suffix": ", glistening raindrops in neon glow, teal and magenta atmospheric lighting, highly detailed"},
                        {"style_tag": "Teknologi Futuristik", "prefix": "Sleek hi-tech cyberpunk visual of", "suffix": ", cybernetic aesthetic, clean glowing LED conduits, futuristic concept design, octane render"}
                    ],
                    "render3d": [
                        {"style_tag": "Render 3D Halus Octane", "prefix": "Stunning 3D octane render of", "suffix": ", smooth ray-traced materials, global illumination, subtle ambient occlusion, Pixar style smoothness"},
                        {"style_tag": "CGI Sinematik Modern", "prefix": "High-end cinematic 3D digital render of", "suffix": ", Unreal Engine 5 aesthetic, volumetric lighting, photorealistic subsurface scattering"},
                        {"style_tag": "Visual 3D Isometrik", "prefix": "Crisp isometric 3D render depicting", "suffix": ", cute claymation texture, miniature tilt-shift effect, soft studio lighting, ultra sharp"},
                        {"style_tag": "Render Objek Estetis", "prefix": "Clean stylized 3D model of", "suffix": ", glossy surfaces, elegant pastel color scheme, perfect 3D geometry, high poly"}
                    ],
                    "lukisan": [
                        {"style_tag": "Lukisan Minyak Klasik", "prefix": "Timeless classical oil painting of", "suffix": ", rich visible impasto brushstrokes, textured canvas, Rembrandt style golden lighting"},
                        {"style_tag": "Seni Impresionis Indah", "prefix": "Vibrant impressionist fine art painting of", "suffix": ", expressive spontaneous brushwork, luminous light dappling, artistic color harmony"},
                        {"style_tag": "Cat Air Artistik", "prefix": "Delicate watercolor painting featuring", "suffix": ", flowing pigment washes, gentle paper texture, artistic color bleeds, poetic aesthetic"},
                        {"style_tag": "Mahakarya Seni Murni", "prefix": "Museum quality fine art masterpiece depicting", "suffix": ", ornate composition, historic painting technique, rich deep pigments"}
                    ],
                    "alami": [
                        {"style_tag": "Potret Natural", "prefix": "Stunning beautiful photograph of", "suffix": ", natural vibrant colors, perfectly lit, realistic, crisp sharp details, 8k uhd"},
                        {"style_tag": "Adegan Sinematik", "prefix": "Cinematic eye-level shot of", "suffix": ", graceful posture, soft volumetric sunlight, serene peaceful atmosphere, award-winning photography"},
                        {"style_tag": "Studio Estetis", "prefix": "Clean aesthetic studio photo of", "suffix": ", soft professional studio lighting, graceful silhouette, harmonious color grading, high aesthetic"},
                        {"style_tag": "Pemandangan Luas", "prefix": "Breathtaking wide view featuring", "suffix": ", natural serene habitat, golden hour lighting, rich depth of field, masterpiece"}
                    ]
                }

                chosen_style_key = style.lower().strip() if style else "alami"
                if chosen_style_key not in STYLE_PRESET_GROUPS:
                    chosen_style_key = "alami"

                VARIATION_PRESETS = STYLE_PRESET_GROUPS[chosen_style_key]

                # Cloudflare credentials check
                cf_config_file = Path(__file__).parent / "cf_config.json"
                cf_creds = {}
                if cf_config_file.exists():
                    try:
                        cf_creds = json.loads(cf_config_file.read_text(encoding="utf-8"))
                    except Exception:
                        pass
                cf_account = cf_creds.get("account_id") or os.environ.get("CF_ACCOUNT_ID", "").strip()
                cf_token = cf_creds.get("api_token") or os.environ.get("CF_API_TOKEN", "").strip()

                # Style & model mapping
                m_lower = model.lower()
                is_cf = model.startswith("@cf/")

                if "real" in m_lower:
                    poll_model = "flux-realism"
                    model_enhancer = ", photorealistic 8k, raw dslr photograph"
                elif "anime" in m_lower:
                    poll_model = "flux-anime"
                    model_enhancer = ", anime artwork, Makoto Shinkai aesthetic, vivid colors"
                elif "3d" in m_lower or "cgi" in m_lower:
                    poll_model = "flux-3d"
                    model_enhancer = ", 3d octane render, cinema 4d, unreal engine 5"
                elif "turbo" in m_lower or "sdxl" in m_lower:
                    poll_model = "turbo"
                    model_enhancer = ", vibrant realistic illustration, ultra crisp"
                elif "flux" in m_lower:
                    poll_model = "flux"
                    model_enhancer = ", masterpiece quality, hyper-detailed"
                else:
                    poll_model = "turbo"
                    model_enhancer = ", vibrant realistic illustration, ultra crisp"

                ratio_dimensions = {
                    "1:1": (512, 512),
                    "16:9": (640, 360),
                    "9:16": (360, 640),
                    "4:3": (512, 384),
                    "3:4": (384, 512),
                }
                width, height = ratio_dimensions.get(aspect_ratio, (512, 512))

                variations = []
                for i in range(count):
                    preset = VARIATION_PRESETS[i % len(VARIATION_PRESETS)]
                    # Gunakan hasil terjemahan bahasa Inggris dengan komposisi natural
                    var_prompt = f"{preset['prefix']} {en_prompt}{preset['suffix']}{model_enhancer}"
                    p_enc = urllib.parse.quote(var_prompt)

                    # Seed unik per variasi & selalu berubah tiap regenerate (timestamp ms + jitter)
                    s = ((now_ms + (i * 382947) + random.randint(10000, 999999)) % 999999999) + 100000

                    # URL dengan parameter seed unik & cache buster agar tidak pernah mengembalikan gambar duplikat
                    neg_enc = urllib.parse.quote(full_negative)
                    img_url = f"{dashboard.POLLINATIONS_IMAGE_URL}{p_enc}?width={width}&height={height}&model={poll_model}&seed={s}&nologo=true&cb={now_ms}_{i}&negative={neg_enc}"
                    hd_url = f"{dashboard.POLLINATIONS_IMAGE_URL}{p_enc}?width=1024&height=1024&model={poll_model}&seed={s}&nologo=true&cb={now_ms}_{i}&negative={neg_enc}"
                    fallback_url = f"{dashboard.POLLINATIONS_IMAGE_URL}{p_enc}?width={width}&height={height}&model=turbo&seed={s}&nologo=true&cb={now_ms}_{i}&negative={neg_enc}"

                    proxy_url = f"/api/image-proxy?url={urllib.parse.quote(img_url)}"

                    variations.append({
                        "id": i + 1,
                        "style_tag": preset["style_tag"],
                        "url": hd_url,
                        "preview_url": img_url,
                        "proxy_url": proxy_url,
                        "fallback_url": fallback_url,
                        "b64_json": "",
                        "seed": s,
                        "prompt": var_prompt,
                        "model": model,
                        "aspect_ratio": aspect_ratio,
                        "provider": f"Pollinations AI ({poll_model})"
                    })

                return self._send_json(200, {
                    "prompt": prompt,
                    "model": model,
                    "aspect_ratio": aspect_ratio,
                    "count": count,
                    "images": variations,
                    "primary_url": variations[0]["url"]
                })
            except Exception as exc:
                return self._send_json(500, {"error": str(exc)})



        # 10. SCAN GITHUB REPO
        elif path == "/api/scanrepo":
            repo_url = body.get("url", "").strip()
            if not repo_url or "github.com" not in repo_url:
                return self._send_json(400, {"error": "URL GitHub repo tidak valid"})
            try:
                result = service.scan_github_repo(repo_url)
                return self._send_json(200, result)
            except Exception as exc:
                return self._send_json(500, {"error": str(exc)})

        # 11. INSPEKSI KEAMANAN WEB & SSL
        elif path == "/api/webinspect":
            target = body.get("url", "").strip() or body.get("target", "").strip()
            if not target:
                return self._send_json(400, {"error": "Domain atau URL target tidak boleh kosong"})
            try:
                result = service.inspect_web_ssl(target)
                return self._send_json(200, result)
            except Exception as exc:
                return self._send_json(400, {"error": str(exc), "message": str(exc), "status": "error"})

        # 12. OSINT: USERNAME SHERLOCK
        elif path == "/api/osint/sherlock":
            username = body.get("username", "").strip()
            if not username:
                return self._send_json(400, {"error": "Username tidak boleh kosong"})
            try:
                res = service.sherlock_username(username)
                return self._send_json(200, res)
            except Exception as exc:
                return self._send_json(500, {"error": str(exc)})

        # 13. OSINT: DISCORD USER LOOKUP
        elif path == "/api/osint/discord":
            user_id = str(body.get("userId") or body.get("user_id") or "").strip()
            if not user_id:
                return self._send_json(400, {"error": "Discord User ID tidak boleh kosong"})
            try:
                res = service.discord_lookup(user_id)
                return self._send_json(200, res)
            except Exception as exc:
                return self._send_json(400, {"error": str(exc)})

        # 14. OSINT: BREACH & PASSWORD LEAK CHECK
        elif path == "/api/osint/breach":
            query = body.get("query", "").strip()
            q_type = body.get("type", "auto").strip()
            if not query:
                return self._send_json(400, {"error": "Query (email / password) tidak boleh kosong"})
            try:
                res = service.check_breach(query, query_type=q_type)
                return self._send_json(200, res)
            except Exception as exc:
                return self._send_json(400, {"error": str(exc)})

        # 15. PHONE: TEMP VIRTUAL SMS NUMBERS
        elif path == "/api/phone/tempsms/numbers":
            try:
                res = service.get_temp_sms_numbers()
                return self._send_json(200, res)
            except Exception as exc:
                return self._send_json(500, {"error": str(exc)})

        # 16. PHONE: TEMP VIRTUAL SMS INBOX
        elif path == "/api/phone/tempsms/inbox":
            number = str(body.get("number", "")).strip()
            if not number:
                return self._send_json(400, {"error": "Nomor telepon virtual tidak boleh kosong"})
            try:
                res = service.get_temp_sms_inbox(number)
                return self._send_json(200, res)
            except Exception as exc:
                return self._send_json(500, {"error": str(exc)})

        # 17. RECON: SUBDOMAIN SCANNER
        elif path == "/api/recon/subdomains":
            domain = body.get("domain", "").strip() or body.get("url", "").strip()
            if not domain:
                return self._send_json(400, {"error": "Domain target tidak boleh kosong"})
            try:
                res = service.scan_subdomains(domain)
                return self._send_json(200, res)
            except Exception as exc:
                return self._send_json(400, {"error": str(exc)})

        # 18. RECON: ONLINE PORT SCANNER
        elif path == "/api/recon/ports":
            host = body.get("host", "").strip() or body.get("target", "").strip()
            if not host:
                return self._send_json(400, {"error": "Host atau IP target tidak boleh kosong"})
            try:
                res = service.scan_ports(host)
                return self._send_json(200, res)
            except Exception as exc:
                return self._send_json(400, {"error": str(exc)})

        # 19. RECON: IP INTELLIGENCE & THREAT SCORE
        elif path == "/api/recon/ipintel":
            ip = body.get("ip", "").strip() or body.get("target", "").strip()
            if not ip:
                return self._send_json(400, {"error": "Alamat IP tidak boleh kosong"})
            try:
                res = service.ip_intelligence(ip)
                return self._send_json(200, res)
            except Exception as exc:
                return self._send_json(400, {"error": str(exc)})

        # 20. GITHUB: USER DEEP PROFILER & EMAIL LEAK
        elif path == "/api/github/profiler":
            username = body.get("username", "").strip()
            if not username:
                return self._send_json(400, {"error": "Username GitHub tidak boleh kosong"})
            try:
                res = service.github_user_profiler(username)
                return self._send_json(200, res)
            except Exception as exc:
                return self._send_json(400, {"error": str(exc)})

        self.send_error(404, "Endpoint not found")


class LeviathanApiHandler(BaseApiHandler):
    pass


def run_server():
    import socket
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        local_ip = "0.0.0.0"

    class ThreadedServer(ThreadingHTTPServer):
        allow_reuse_address = True
        daemon_threads = True

    server_address = ("0.0.0.0", PORT)
    httpd = ThreadedServer(server_address, LeviathanApiHandler)
    print("═" * 58)
    print(f"🚀 PROJECT-XVOID Web App (Threaded)")
    print(f"   Local  → http://localhost:{PORT}")
    print(f"   WiFi   → http://{local_ip}:{PORT}")
    print(f"   Buka di HP: http://{local_ip}:{PORT}")
    print("═" * 58)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
