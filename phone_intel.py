from __future__ import annotations

import re
import urllib.parse
from typing import Any, Dict, List, Optional
from datetime import datetime

try:
    import phonenumbers
    from phonenumbers import carrier as pn_carrier
    from phonenumbers import geocoder as pn_geocoder
    from phonenumbers import timezone as pn_timezone
    HAS_PHONENUMBERS = True
except ImportError:
    HAS_PHONENUMBERS = False


# =====================================================================
# 1. GHOSTINTEL MULTI-COUNTRY PROVIDER DATABASE (Resource: GhostIntel)
# =====================================================================
GHOSTINTEL_PROVIDER_DB: Dict[str, Dict[str, str]] = {
    'ID': {
        # Telkomsel
        '0811': 'Telkomsel (Halo)', '0812': 'Telkomsel (SimPATI/Halo)', '0813': 'Telkomsel (SimPATI)',
        '0821': 'Telkomsel (SimPATI)', '0822': 'Telkomsel (Loop)', '0823': 'Telkomsel (Keluarga)',
        '0851': 'Telkomsel (By.U/AS)', '0852': 'Telkomsel (Kartu AS)', '0853': 'Telkomsel (Kartu AS)',
        # Indosat Ooredoo Hutchison
        '0814': 'Indosat (Broadband)', '0815': 'Indosat (Matrix/Mentari)', '0816': 'Indosat (Matrix/Mentari)',
        '0855': 'Indosat (Matrix)', '0856': 'Indosat (IM3)', '0857': 'Indosat (IM3)',
        '0858': 'Indosat (Mentari)', '0859': 'Indosat / XL',
        # XL Axiata
        '0817': 'XL Axiata', '0818': 'XL Axiata', '0819': 'XL Axiata',
        '0877': 'XL Axiata', '0878': 'XL Axiata', '0879': 'XL Axiata',
        '0831': 'Axis (XL Axiata)', '0832': 'Axis (XL Axiata)', '0833': 'Axis (XL Axiata)', '0838': 'Axis (XL Axiata)',
        # Three (Tri)
        '0895': 'Tri (3 / IOH)', '0896': 'Tri (3 / IOH)', '0897': 'Tri (3 / IOH)',
        '0898': 'Tri (3 / IOH)', '0899': 'Tri (3 / IOH)',
        # Smartfren
        '0881': 'Smartfren', '0882': 'Smartfren', '0883': 'Smartfren',
        '0884': 'Smartfren', '0885': 'Smartfren', '0886': 'Smartfren',
        '0887': 'Smartfren', '0888': 'Smartfren', '0889': 'Smartfren',
    },
    'US': {
        '212': 'AT&T', '213': 'AT&T', '404': 'AT&T', '415': 'AT&T',
        '510': 'AT&T', '626': 'AT&T', '818': 'AT&T', '858': 'AT&T',
        '909': 'AT&T', '917': 'AT&T', '617': 'Verizon', '646': 'Verizon',
        '718': 'Verizon', '847': 'Verizon', '914': 'Verizon',
        '310': 'T-Mobile', '702': 'T-Mobile', '832': 'T-Mobile', '929': 'T-Mobile',
    },
    'GB': {
        '7700': 'EE', '7701': 'EE', '7702': 'EE', '7703': 'EE', '7704': 'EE',
        '7710': 'O2', '7711': 'O2', '7712': 'O2', '7713': 'O2',
        '7720': 'Vodafone', '7721': 'Vodafone', '7722': 'Vodafone',
        '7730': 'Three', '7731': 'Three', '7732': 'Three',
    },
    'MY': {
        '012': 'Maxis', '017': 'Maxis', '013': 'Celcom', '019': 'Celcom',
        '010': 'DiGi', '016': 'DiGi', '011': 'U Mobile', '018': 'U Mobile',
        '015': 'Tune Talk',
    },
    'SG': {
        '811': 'Singtel', '812': 'Singtel', '813': 'Singtel',
        '800': 'StarHub', '810': 'M1', '880': 'SIMBA (TPG)',
    },
    'AU': {
        '041': 'Telstra', '040': 'Optus', '042': 'Vodafone', '047': 'Amaysim', '048': 'Boost',
    },
    'PH': {
        '917': 'Globe', '918': 'Smart', '991': 'DITO', '922': 'Sun/Smart',
    },
    'IN': {
        '981': 'Airtel', '982': 'Vodafone Idea', '987': 'Jio', '888': 'BSNL',
    }
}

LINE_TYPE_MAP = {
    0: "Fixed Line (Telepon Rumah/Kantor)",
    1: "Mobile (Seluler)",
    2: "Fixed/Mobile",
    3: "Toll Free (Bebas Pulsa)",
    4: "Premium Rate",
    5: "Shared Cost",
    6: "VoIP (Internet Calling)",
    7: "Personal Number",
    8: "Pager",
    9: "UAN (Universal Access)",
    10: "Unknown",
}

# =====================================================================
# 2. OSINT INDONESIA V3 DATA & DORK TARGETS (Resource: osint-indonesia-v3)
# =====================================================================
OSINT_ID_TELCO_PREFIX = {
    "0811": "Telkomsel Halo", "0812": "Telkomsel SimPATI", "0813": "Telkomsel SimPATI",
    "0821": "Telkomsel SimPATI", "0822": "Telkomsel Loop", "0823": "Telkomsel Kartu AS",
    "0851": "Telkomsel By.U / AS", "0852": "Telkomsel AS", "0853": "Telkomsel AS",
    "0814": "Indosat Broadband", "0815": "Indosat Matrix", "0816": "Indosat Mentari",
    "0855": "Indosat Matrix", "0856": "Indosat IM3", "0857": "Indosat IM3", "0858": "Indosat Mentari",
    "0817": "XL Axiata", "0818": "XL Axiata", "0819": "XL Axiata",
    "0877": "XL Axiata", "0878": "XL Axiata", "0879": "XL Axiata",
    "0831": "Axis", "0832": "Axis", "0838": "Axis",
    "0895": "Tri (3)", "0896": "Tri (3)", "0897": "Tri (3)", "0898": "Tri (3)", "0899": "Tri (3)",
    "0881": "Smartfren", "0882": "Smartfren", "0887": "Smartfren", "0888": "Smartfren"
}

# =====================================================================
# 3. PHONEINFOGA DISPOSABLE PROVIDERS LIST (Resource: phoneinfoga)
# =====================================================================
DISPOSABLE_SMS_DOMAINS = [
    "receive-sms-now.com", "freesmscode.com", "catchsms.com", "smstibo.com",
    "smsreceiving.com", "getfreesmsnumber.com", "smslisten.com", "hs3x.com",
    "smsnumbersonline.com", "temp-sms.org", "quackr.io", "anonymsms.com"
]

US_CARRIER_GATEWAYS = {
    "AT&T": "txt.att.net",
    "Verizon": "vtext.com",
    "T-Mobile": "tmomail.net",
    "Sprint": "messaging.sprintpcs.com",
    "Boost Mobile": "sms.myboostmobile.com",
    "Cricket": "sms.cricketwireless.net",
}


class MultiEnginePhoneScanner:
    """
    Modular Multi-Engine Phone Scanner combining:
    1. Kaspersky WhoCallsID (primary live lookup)
    2. GhostIntel v2.5 (multi-country provider db, line type, handles)
    3. GhostTrack (carrier, id geocoder, timezone, maps link)
    4. OSINT-Indonesia-v3 (national prefix resolver & indonesian dorks)
    5. PhoneInfoga (burner/disposable sms checks, reputation dorks)
    6. PhoneOsint (deep messaging links, gateways, osint dork matrix)
    """

    @staticmethod
    def normalize_number(raw_phone: str, default_region: str = "ID") -> Dict[str, Any]:
        """Bersihkan dan format nomor ke bentuk standar internasional & nasional."""
        raw = raw_phone.strip()
        digits = re.sub(r"\D", "", raw)
        
        # Heuristik awal
        if digits.startswith("0"):
            digits = "62" + digits[1:]
        elif digits.startswith("620"):
            digits = "62" + digits[3:]
        elif not digits.startswith("62") and len(digits) in (9, 10, 11, 12, 13) and default_region == "ID":
            digits = "62" + digits

        e164 = f"+{digits}"
        national = f"0{digits[2:]}" if digits.startswith("62") else digits
        return {
            "raw": raw_phone,
            "digits": digits,
            "e164": e164,
            "national": national,
            "default_region": default_region
        }

    @classmethod
    def scan(cls, raw_phone: str, kaspersky_func=None, default_region: str = "ID") -> Dict[str, Any]:
        norm = cls.normalize_number(raw_phone, default_region)
        digits = norm["digits"]
        e164 = norm["e164"]
        national = norm["national"]

        resources: Dict[str, Dict[str, Any]] = {}
        detected_operator: Optional[str] = None
        operator_source: Optional[str] = None
        display_format: str = e164
        country_name: str = "Indonesia" if digits.startswith("62") else "International"
        country_iso: str = default_region
        country_code: int = 62 if digits.startswith("62") else 1
        location: str = "Indonesia" if digits.startswith("62") else "Global"
        line_type: str = "Mobile (Seluler)"
        timezones: List[str] = ["Asia/Jakarta"] if digits.startswith("62") else []
        similar_numbers: List[Dict[str, Any]] = []

        # -------------------------------------------------------------
        # STAGE 1: Kaspersky WhoCallsID (Primary Remote Query)
        # -------------------------------------------------------------
        k_hit = False
        k_info: Dict[str, Any] = {}
        if kaspersky_func:
            try:
                k_raw = kaspersky_func(raw_phone)
                k_info = k_raw.get("info") or {}
                similar_numbers = k_raw.get("similar") or []
                op = k_info.get("operator")
                if op:
                    op_str = ", ".join(op) if isinstance(op, list) else str(op)
                    if op_str.strip() and op_str.strip().lower() != "tidak diketahui":
                        detected_operator = op_str
                        operator_source = "Kaspersky WhoCallsID"
                        k_hit = True
                if k_info.get("display_format"):
                    display_format = str(k_info["display_format"])
                if k_info.get("international_code"):
                    country_code = int(k_info["international_code"])
                if k_info.get("region"):
                    location = str(k_info["region"])
            except Exception as exc:
                k_info = {"error": str(exc)}

        resources["kaspersky"] = {
            "name": "Kaspersky WhoCallsID",
            "tier": 1,
            "status": "HIT" if k_hit else "FALLBACK (No operator / Rate Limit)",
            "operator": detected_operator or "Tidak ditemukan di database WhoCalls",
            "display_format": display_format,
            "similar_count": len(similar_numbers)
        }

        # -------------------------------------------------------------
        # STAGE 2: GhostIntel Engine (Provider DB, Line Type, Handles)
        # -------------------------------------------------------------
        gi_provider = None
        gi_handles: List[str] = []
        # Cek provider DB dari GhostIntel
        prefix_table = GHOSTINTEL_PROVIDER_DB.get(country_iso, {})
        for p_len in (4, 3, 2):
            sub = national[:p_len]
            if sub in prefix_table:
                gi_provider = prefix_table[sub]
                break

        # Generate handle variations (dari GhostIntel phone.py)
        gi_handles = [digits, national]
        if len(national) >= 8:
            gi_handles.append(national[-8:])

        if not detected_operator and gi_provider:
            detected_operator = gi_provider
            operator_source = "GhostIntel Provider DB"

        resources["ghostintel"] = {
            "name": "GhostIntel v2.5",
            "tier": 2,
            "status": "HIT" if gi_provider else "PARTIAL",
            "provider_db_match": gi_provider or "Unknown",
            "supported_country": country_iso,
            "line_type": line_type,
            "sample_handles": gi_handles[:3]
        }

        # -------------------------------------------------------------
        # STAGE 3: GhostTrack Engine (libphonenumber geocoder/carrier/tz)
        # -------------------------------------------------------------
        gt_carrier = None
        gt_geo = None
        gt_tz: List[str] = []
        is_possible = True
        is_valid = True

        if HAS_PHONENUMBERS:
            try:
                parsed = phonenumbers.parse(e164, country_iso)
                is_valid = phonenumbers.is_valid_number(parsed)
                is_possible = phonenumbers.is_possible_number(parsed)
                country_code = int(parsed.country_code or 62)
                country_iso = phonenumbers.region_code_for_number(parsed) or country_iso
                
                gt_carrier = pn_carrier.name_for_number(parsed, "en")
                gt_geo = pn_geocoder.description_for_number(parsed, "id") or pn_geocoder.description_for_number(parsed, "en")
                gt_tz = list(pn_timezone.time_zones_for_number(parsed))
                ntype = phonenumbers.number_type(parsed)
                line_type = LINE_TYPE_MAP.get(ntype, "Mobile (Seluler)")

                if gt_carrier and not detected_operator:
                    detected_operator = gt_carrier
                    operator_source = "GhostTrack (Carrier Lib)"
                if gt_geo:
                    location = gt_geo
                if gt_tz:
                    timezones = gt_tz
                display_format = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            except Exception:
                pass

        resources["ghosttrack"] = {
            "name": "GhostTrack PhoneGW",
            "tier": 3,
            "status": "HIT" if (gt_carrier or gt_geo) else "PARTIAL",
            "carrier": gt_carrier or detected_operator or "Unknown",
            "geocoder_location": gt_geo or location,
            "timezones": timezones,
            "valid_number": is_valid,
            "possible_number": is_possible,
            "maps_query": f"https://www.google.com/maps/search/{urllib.parse.quote(location)}"
        }

        # -------------------------------------------------------------
        # STAGE 4: OSINT-Indonesia-v3 Engine (Indonesian Carrier & Dorks)
        # -------------------------------------------------------------
        osint_id_match = None
        pref4 = national[:4]
        if pref4 in OSINT_ID_TELCO_PREFIX:
            osint_id_match = OSINT_ID_TELCO_PREFIX[pref4]
            if not detected_operator:
                detected_operator = osint_id_match
                operator_source = "OSINT-Indonesia-v3"

        # Specialized Indonesian Dork Queries
        q_gov = f'site:go.id "{national}" OR "{e164}"'
        q_edu = f'site:ac.id "{national}" OR "{e164}"'
        q_tokopedia = f'site:tokopedia.com "{national}"'
        q_shopee = f'site:shopee.co.id "{national}"'
        q_olx = f'site:olx.co.id "{national}"'
        q_fb = f'site:facebook.com "{national}" OR "{e164}"'
        q_ig = f'site:instagram.com "{national}"'

        id_dorks = {
            "Pemerintah (.go.id)": f"https://www.google.com/search?q={urllib.parse.quote(q_gov)}",
            "Akademik / Kampus (.ac.id)": f"https://www.google.com/search?q={urllib.parse.quote(q_edu)}",
            "Tokopedia": f"https://www.google.com/search?q={urllib.parse.quote(q_tokopedia)}",
            "Shopee": f"https://www.google.com/search?q={urllib.parse.quote(q_shopee)}",
            "OLX / Forum Jual Beli": f"https://www.google.com/search?q={urllib.parse.quote(q_olx)}",
            "Facebook Indonesia": f"https://www.google.com/search?q={urllib.parse.quote(q_fb)}",
            "Instagram Indonesia": f"https://www.google.com/search?q={urllib.parse.quote(q_ig)}",
        }

        resources["osint_id"] = {
            "name": "OSINT-Indonesia-v3",
            "tier": 4,
            "status": "HIT" if osint_id_match else "APPLIED",
            "prefix_detected": pref4,
            "telco_provider": osint_id_match or "Non-Indonesian / Prefix Khusus",
            "dorks_generated": len(id_dorks)
        }

        # -------------------------------------------------------------
        # STAGE 5: PhoneInfoga Engine (Disposable SMS & Reputation)
        # -------------------------------------------------------------
        infoga_disposable_links = []
        for domain in DISPOSABLE_SMS_DOMAINS[:6]:
            q_disp = f'site:{domain} "{e164}" OR "{national}"'
            infoga_disposable_links.append({
                "provider": domain,
                "url": f"https://www.google.com/search?q={urllib.parse.quote(q_disp)}"
            })

        q_pastebin = f'site:pastebin.com "{e164}" OR "{national}"'
        q_ghostbin = f'site:ghostbin.co OR site:hastebin.com "{e164}"'
        q_spam = f'"{national}" OR "{e164}" penipuan OR spam OR telemarketing'

        infoga_reputation_dorks = {
            "Pastebin Leaks": f"https://www.google.com/search?q={urllib.parse.quote(q_pastebin)}",
            "Ghostbin / Hastebin": f"https://www.google.com/search?q={urllib.parse.quote(q_ghostbin)}",
            "Spam / Telemarketing Check": f"https://www.google.com/search?q={urllib.parse.quote(q_spam)}",
        }

        resources["phoneinfoga"] = {
            "name": "PhoneInfoga Scanner",
            "tier": 5,
            "status": "HIT",
            "disposable_services_audited": len(infoga_disposable_links),
            "reputation_scanners": len(infoga_reputation_dorks),
            "ovh_telecom_capable": country_code in (33, 32, 44, 34, 41)
        }

        # -------------------------------------------------------------
        # STAGE 6: PhoneOsint Engine (Deep Links, Direct Dorks, Gateways)
        # -------------------------------------------------------------
        direct_links = {
            "whatsapp": f"https://wa.me/{digits}",
            "telegram": f"https://t.me/{digits}",
            "viber": f"viber://chat?number={digits}",
            "sms": f"sms:{e164}"
        }

        q_truecaller = f'site:truecaller.com "{e164}" OR "{national}"'
        q_linkedin = f'site:linkedin.com/in/ "{national}" OR "{e164}"'
        q_github = f'site:github.com "{e164}" OR "{national}"'
        q_twitter = f'site:twitter.com OR site:x.com "{national}" OR "{e164}"'
        q_doc = f'filetype:pdf OR filetype:xls OR filetype:xlsx "{national}"'

        osint_dorks = {
            "Truecaller Web": f"https://www.google.com/search?q={urllib.parse.quote(q_truecaller)}",
            "LinkedIn Profile": f"https://www.google.com/search?q={urllib.parse.quote(q_linkedin)}",
            "GitHub Commits/Code": f"https://www.google.com/search?q={urllib.parse.quote(q_github)}",
            "Twitter / X Mention": f"https://www.google.com/search?q={urllib.parse.quote(q_twitter)}",
            "Document / PDF Leak": f"https://www.google.com/search?q={urllib.parse.quote(q_doc)}",
        }

        resources["phoneosint"] = {
            "name": "PhoneOsint Master",
            "tier": 6,
            "status": "HIT",
            "direct_messaging_links": len(direct_links),
            "osint_dorks_count": len(osint_dorks),
            "gateway_candidates": US_CARRIER_GATEWAYS if country_iso == "US" else "Non-US Region"
        }

        # -------------------------------------------------------------
        # FINAL AGGREGATION & FALLBACK RESOLUTION
        # -------------------------------------------------------------
        final_operator = detected_operator or "Tidak Teridentifikasi"
        if not operator_source:
            operator_source = "Multi-Engine Heuristic"

        return {
            "nomor_normalized": digits,
            "e164": e164,
            "national": national,
            "display_format": display_format,
            "operator": final_operator,
            "operator_source": operator_source,
            "country": country_name,
            "country_code": country_code,
            "country_iso": country_iso,
            "location": location,
            "line_type": line_type,
            "timezones": timezones,
            "valid": is_valid,
            "possible": is_possible,
            "direct_links": direct_links,
            "similar": similar_numbers,
            "dorks": {
                "indonesia": id_dorks,
                "osint": osint_dorks,
                "reputation": infoga_reputation_dorks,
                "disposable": infoga_disposable_links
            },
            "resources": resources,
            "timestamp": datetime.now().isoformat()
        } 
