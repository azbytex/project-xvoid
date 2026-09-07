from __future__ import annotations

import datetime
import re
import urllib.parse
from typing import Any, Dict, List, Optional


# =====================================================================
# 1. DAFTAR PROVINSI RESMI INDONESIA (38 PROVINSI - Permendagri)
# Resource: osint-indonesia-v3 & Badan Pusat Statistik (BPS)
# =====================================================================
PROVINSI_DB: Dict[str, str] = {
    "11": "Aceh",
    "12": "Sumatera Utara",
    "13": "Sumatera Barat",
    "14": "Riau",
    "15": "Jambi",
    "16": "Sumatera Selatan",
    "17": "Bengkulu",
    "18": "Lampung",
    "19": "Kepulauan Bangka Belitung",
    "21": "Kepulauan Riau",
    "31": "DKI Jakarta",
    "32": "Jawa Barat",
    "33": "Jawa Tengah",
    "34": "DI Yogyakarta",
    "35": "Jawa Timur",
    "36": "Banten",
    "51": "Bali",
    "52": "Nusa Tenggara Barat",
    "53": "Nusa Tenggara Timur",
    "61": "Kalimantan Barat",
    "62": "Kalimantan Tengah",
    "63": "Kalimantan Selatan",
    "64": "Kalimantan Timur",
    "65": "Kalimantan Utara",
    "71": "Sulawesi Utara",
    "72": "Sulawesi Tengah",
    "73": "Sulawesi Selatan",
    "74": "Sulawesi Tenggara",
    "75": "Gorontalo",
    "76": "Sulawesi Barat",
    "81": "Maluku",
    "82": "Maluku Utara",
    "91": "Papua Barat",
    "92": "Papua Barat Daya",
    "93": "Papua Selatan",
    "94": "Papua Tengah",
    "95": "Papua Pegunungan",
    "96": "Papua",
}

# =====================================================================
# 2. DAFTAR KABUPATEN / KOTA TERPOPULER & REPRESENTATIF DI INDONESIA
# =====================================================================
KABUPATEN_KOTA_DB: Dict[str, str] = {
    # DKI Jakarta (31)
    "3101": "Kabupaten Administrasi Kepulauan Seribu",
    "3171": "Kota Administrasi Jakarta Selatan",
    "3172": "Kota Administrasi Jakarta Timur",
    "3173": "Kota Administrasi Jakarta Pusat",
    "3174": "Kota Administrasi Jakarta Barat",
    "3175": "Kota Administrasi Jakarta Utara",
    # Jawa Barat (32)
    "3201": "Kabupaten Bogor",
    "3202": "Kabupaten Sukabumi",
    "3203": "Kabupaten Cianjur",
    "3204": "Kabupaten Bandung",
    "3205": "Kabupaten Garut",
    "3206": "Kabupaten Tasikmalaya",
    "3207": "Kabupaten Ciamis",
    "3208": "Kabupaten Kuningan",
    "3209": "Kabupaten Cirebon",
    "3210": "Kabupaten Majalengka",
    "3211": "Kabupaten Sumedang",
    "3212": "Kabupaten Indramayu",
    "3213": "Kabupaten Subang",
    "3214": "Kabupaten Purwakarta",
    "3215": "Kabupaten Karawang",
    "3216": "Kabupaten Bekasi",
    "3217": "Kabupaten Bandung Barat",
    "3218": "Kabupaten Pangandaran",
    "3271": "Kota Bogor",
    "3272": "Kota Sukabumi",
    "3273": "Kota Bandung",
    "3274": "Kota Cirebon",
    "3275": "Kota Bekasi",
    "3276": "Kota Depok",
    "3277": "Kota Cimahi",
    "3278": "Kota Tasikmalaya",
    "3279": "Kota Banjar",
    # Banten (36)
    "3601": "Kabupaten Pandeglang",
    "3602": "Kabupaten Lebak",
    "3603": "Kabupaten Tangerang",
    "3604": "Kabupaten Serang",
    "3671": "Kota Tangerang",
    "3672": "Kota Cilegon",
    "3673": "Kota Serang",
    "3674": "Kota Tangerang Selatan",
    # Jawa Tengah (33)
    "3301": "Kabupaten Cilacap",
    "3302": "Kabupaten Banyumas",
    "3303": "Kabupaten Purbalingga",
    "3304": "Kabupaten Banjarnegara",
    "3305": "Kabupaten Kebumen",
    "3306": "Kabupaten Purworejo",
    "3307": "Kabupaten Wonosobo",
    "3308": "Kabupaten Magelang",
    "3309": "Kabupaten Boyolali",
    "3310": "Kabupaten Klaten",
    "3311": "Kabupaten Sukoharjo",
    "3312": "Kabupaten Wonogiri",
    "3313": "Kabupaten Karanganyar",
    "3314": "Kabupaten Sragen",
    "3315": "Kabupaten Grobogan",
    "3316": "Kabupaten Blora",
    "3317": "Kabupaten Rembang",
    "3318": "Kabupaten Pati",
    "3319": "Kabupaten Kudus",
    "3320": "Kabupaten Jepara",
    "3321": "Kabupaten Demak",
    "3322": "Kabupaten Semarang",
    "3323": "Kabupaten Temanggung",
    "3324": "Kabupaten Kendal",
    "3325": "Kabupaten Batang",
    "3326": "Kabupaten Pekalongan",
    "3327": "Kabupaten Pemalang",
    "3328": "Kabupaten Tegal",
    "3329": "Kabupaten Brebes",
    "3371": "Kota Magelang",
    "3372": "Kota Surakarta (Solo)",
    "3373": "Kota Salatiga",
    "3374": "Kota Semarang",
    "3375": "Kota Pekalongan",
    "3376": "Kota Tegal",
    # DI Yogyakarta (34)
    "3401": "Kabupaten Kulon Progo",
    "3402": "Kabupaten Bantul",
    "3403": "Kabupaten Gunungkidul",
    "3404": "Kabupaten Sleman",
    "3471": "Kota Yogyakarta",
    # Jawa Timur (35)
    "3501": "Kabupaten Pacitan",
    "3502": "Kabupaten Ponorogo",
    "3503": "Kabupaten Trenggalek",
    "3504": "Kabupaten Tulungagung",
    "3505": "Kabupaten Blitar",
    "3506": "Kabupaten Kediri",
    "3507": "Kabupaten Malang",
    "3508": "Kabupaten Lumajang",
    "3509": "Kabupaten Jember",
    "3510": "Kabupaten Banyuwangi",
    "3511": "Kabupaten Bondowoso",
    "3512": "Kabupaten Situbondo",
    "3513": "Kabupaten Probolinggo",
    "3514": "Kabupaten Pasuruan",
    "3515": "Kabupaten Sidoarjo",
    "3516": "Kabupaten Mojokerto",
    "3517": "Kabupaten Jombang",
    "3518": "Kabupaten Nganjuk",
    "3519": "Kabupaten Madiun",
    "3520": "Kabupaten Magetan",
    "3521": "Kabupaten Ngawi",
    "3522": "Kabupaten Bojonegoro",
    "3523": "Kabupaten Tuban",
    "3524": "Kabupaten Lamongan",
    "3525": "Kabupaten Gresik",
    "3526": "Kabupaten Bangkalan",
    "3527": "Kabupaten Sampang",
    "3528": "Kabupaten Pamekasan",
    "3529": "Kabupaten Sumenep",
    "3571": "Kota Kediri",
    "3572": "Kota Blitar",
    "3573": "Kota Malang",
    "3574": "Kota Probolinggo",
    "3575": "Kota Pasuruan",
    "3576": "Kota Mojokerto",
    "3577": "Kota Madiun",
    "3578": "Kota Surabaya",
    "3579": "Kota Batu",
    # Bali (51)
    "5101": "Kabupaten Jembrana",
    "5102": "Kabupaten Tabanan",
    "5103": "Kabupaten Badung",
    "5104": "Kabupaten Gianyar",
    "5105": "Kabupaten Klungkung",
    "5106": "Kabupaten Bangli",
    "5107": "Kabupaten Karangasem",
    "5108": "Kabupaten Buleleng",
    "5171": "Kota Denpasar",
    # Sumatera Utara (12)
    "1271": "Kota Medan",
    "1272": "Kota Pematangsiantar",
    "1273": "Kota Sibolga",
    "1274": "Kota Tanjungbalai",
    "1275": "Kota Binjai",
    "1276": "Kota Tebing Tinggi",
    "1277": "Kota Padangsidimpuan",
    "1278": "Kota Gunungsitoli",
    "1207": "Kabupaten Deli Serdang",
    # Sumatera Barat (13)
    "1371": "Kota Padang",
    "1372": "Kota Solok",
    "1373": "Kota Sawahlunto",
    "1374": "Kota Padang Panjang",
    "1375": "Kota Bukittinggi",
    "1376": "Kota Payakumbuh",
    "1377": "Kota Pariaman",
    # Riau (14) & Kepri (21)
    "1471": "Kota Pekanbaru",
    "1472": "Kota Dumai",
    "2171": "Kota Batam",
    "2172": "Kota Tanjungpinang",
    # Sumsel (16) & Lampung (18)
    "1671": "Kota Palembang",
    "1801": "Kabupaten Lampung Barat",
    "1802": "Kabupaten Tanggamus",
    "1803": "Kabupaten Lampung Selatan",
    "1804": "Kabupaten Lampung Timur",
    "1805": "Kabupaten Lampung Tengah",
    "1806": "Kabupaten Lampung Utara",
    "1807": "Kabupaten Lampung Timur",
    "1808": "Kabupaten Way Kanan",
    "1809": "Kabupaten Tulang Bawang",
    "1810": "Kabupaten Pesawaran",
    "1811": "Kabupaten Pringsewu",
    "1812": "Kabupaten Mesuji",
    "1813": "Kabupaten Tulang Bawang Barat",
    "1814": "Kabupaten Pesisir Barat",
    "1871": "Kota Bandar Lampung",
    "1872": "Kota Metro",
    # Kalimantan
    "6171": "Kota Pontianak",
    "6271": "Kota Palangka Raya",
    "6371": "Kota Banjarmasin",
    "6372": "Kota Banjarbaru",
    "6471": "Kota Balikpapan",
    "6472": "Kota Samarinda",
    "6474": "Kota Bontang",
    "6571": "Kota Tarakan",
    # Sulawesi
    "7171": "Kota Manado",
    "7271": "Kota Palu",
    "7371": "Kota Makassar",
    "7471": "Kota Kendari",
    "7571": "Kota Gorontalo",
}

# Shio & Zodiak Helpers
ZODIAC_LIST = [
    (1, 20, "Capricorn"), (2, 19, "Aquarius"), (3, 20, "Pisces"),
    (4, 20, "Aries"), (5, 21, "Taurus"), (6, 21, "Gemini"),
    (7, 22, "Cancer"), (8, 23, "Leo"), (9, 23, "Virgo"),
    (10, 23, "Libra"), (11, 22, "Scorpio"), (12, 22, "Sagittarius"),
    (12, 31, "Capricorn")
]

SHIO_ANIMALS = [
    "Tikus", "Kerbau", "Harimau", "Kelinci",
    "Naga", "Ular", "Kuda", "Kambing",
    "Monyet", "Ayam", "Anjing", "Babi"
]


def get_zodiac(day: int, month: int) -> str:
    for m, d, name in ZODIAC_LIST:
        if month == m and day <= d:
            return name
        elif month == m - 1 and day > d:
            return name
    return "Capricorn"


def get_shio(year: int) -> str:
    # 1900 was Year of the Rat (index 0)
    idx = (year - 1900) % 12
    return SHIO_ANIMALS[idx]


def parse_nik_indonesia(nik_input: str) -> Dict[str, Any]:
    """
    Bedah & Rekonstruksi NIK KTP Indonesia (Resource: osint-indonesia-v3).
    Formula Standar Dukcapil:
    [PP][KK][CC][DDMMYY][NNNN]
    - PP: Kode Provinsi (2 digit)
    - KK: Kode Kabupaten / Kota (2 digit)
    - CC: Kode Kecamatan (2 digit)
    - DDMMYY: Tanggal Lahir (6 digit). Jika perempuan, DD + 40.
    - NNNN: Nomor Registrasi Komputer Dukcapil (4 digit).
    """
    raw = re.sub(r'[^0-9]', '', str(nik_input).strip())
    if len(raw) != 16:
        return {
            "status": "error",
            "message": f"NIK harus tepat 16 digit angka. NIK yang dimasukkan: {len(raw)} digit ({raw})."
        }

    prov_code = raw[0:2]
    kab_code = raw[0:4]
    kec_code = raw[0:6]
    dd_raw = int(raw[6:8])
    mm_raw = int(raw[8:10])
    yy_raw = int(raw[10:12])
    seq_code = raw[12:16]

    # Deteksi Gender & Tanggal Lahir Asli
    is_female = dd_raw > 40
    real_day = dd_raw - 40 if is_female else dd_raw
    gender = "Perempuan" if is_female else "Laki-laki"

    # Penentuan Abad Lahir (Heuristik Berdasarkan Tahun Berjalan)
    current_date = datetime.date.today()
    current_year_2digit = current_date.year % 100
    birth_year = (2000 + yy_raw) if yy_raw <= current_year_2digit else (1900 + yy_raw)

    # Validasi Tanggal Kalender
    is_valid_date = True
    try:
        birth_dt = datetime.date(birth_year, mm_raw, real_day)
    except ValueError:
        is_valid_date = False
        birth_dt = None

    # Kalkulasi Umur Presisi
    age_str = "Tidak Valid"
    age_years = 0
    if is_valid_date and birth_dt:
        days_diff = (current_date - birth_dt).days
        age_years = current_date.year - birth_dt.year - ((current_date.month, current_date.day) < (birth_dt.month, birth_dt.day))
        age_str = f"{age_years} Tahun"

    # Resolusi Nama Wilayah Administrasi
    provinsi_nama = PROVINSI_DB.get(prov_code, f"Provinsi Kode {prov_code} (Pemekaran Baru)")
    kabupaten_nama = KABUPATEN_KOTA_DB.get(kab_code)
    if not kabupaten_nama:
        # Menentukan apakah Kabupaten atau Kota dari angka ke 3-4
        sub_code = int(raw[2:4])
        type_str = "Kota" if sub_code >= 71 else "Kabupaten"
        kabupaten_nama = f"{type_str} (Kode Wilayah {kab_code})"

    kecamatan_nama = f"Kecamatan Kode {raw[4:6]} (Sub-wilayah {kab_code})"

    # Zodiak & Shio
    zodiac_sign = get_zodiac(real_day, mm_raw) if is_valid_date else "-"
    shio_sign = get_shio(birth_year) if is_valid_date else "-"

    # Dorking & OSINT Links
    encoded_nik = urllib.parse.quote(f'"{raw}"')
    dork_links = [
        {
            "name": "KPU DPT Online",
            "badge": "Nasional",
            "url": "https://cekdptonline.kpu.go.id/",
            "desc": "Portal Cek Data Pemilih Tetap KPU RI (Cek TPS & Domisili Terdaftar)"
        },
        {
            "name": "Google Dork (.GO.ID)",
            "badge": "Pemerintah",
            "url": f"https://www.google.com/search?q={encoded_nik}+site:go.id",
            "desc": "Pencarian jejak NIK di seluruh domain instansi pemerintahan RI"
        },
        {
            "name": "Google Dork (.AC.ID)",
            "badge": "Akademik",
            "url": f"https://www.google.com/search?q={encoded_nik}+site:ac.id",
            "desc": "Pencarian jejak NIK di repository skripsi, jurnal, dan wisuda kampus"
        },
        {
            "name": "Mahkamah Agung",
            "badge": "Hukum",
            "url": f"https://www.google.com/search?q={encoded_nik}+site:putusan3.mahkamahagung.go.id",
            "desc": "Pencarian risalah putusan sidang pengadilan Mahkamah Agung"
        },
        {
            "name": "Google Web Global",
            "badge": "Publik",
            "url": f"https://www.google.com/search?q={encoded_nik}",
            "desc": "Pencarian indeks global dokumen, PDF bansos, CPNS, dan sertifikasi"
        },
        {
            "name": "Facebook & Sosmed",
            "badge": "Sosmed",
            "url": f"https://www.google.com/search?q={encoded_nik}+(site:facebook.com+OR+site:instagram.com+OR+site:twitter.com)",
            "desc": "Pencarian nomor identitas di platform media sosial terbuka"
        }
    ]

    return {
        "status": "success",
        "nik": raw,
        "valid_format": True,
        "is_valid_date": is_valid_date,
        "provinsi": provinsi_nama,
        "provinsi_kode": prov_code,
        "kabupaten": kabupaten_nama,
        "kabupaten_kode": kab_code,
        "kecamatan": kecamatan_nama,
        "kecamatan_kode": kec_code,
        "tanggal_lahir": f"{real_day:02d}-{mm_raw:02d}-{birth_year}",
        "hari": real_day,
        "bulan": mm_raw,
        "tahun": birth_year,
        "usia": age_str,
        "usia_angka": age_years,
        "jenis_kelamin": gender,
        "nomor_urut": seq_code,
        "zodiak": zodiac_sign,
        "shio": shio_sign,
        "dorks": dork_links,
        "engine_attribution": "osint-indonesia-v3 (Dukcapil Algorithm & Administrative Wilayah Decoder)"
    } 
