import json
import os
from datetime import datetime

PROFILE_FILE = "user_profile.json"

def get_profile() -> dict:
    """Profili dosyadan okur. Yoksa boş profil döner."""
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "height": None,
        "weight": None,
        "preferred_fit": None,
        "fabric_allergies": [],
        "disliked_colors": [],
        "body_type": None,
        "updated_at": None,
        "analysis_history": []
    }

def save_profile(profile: dict) -> None:
    """Profili dosyaya kaydeder."""
    profile["updated_at"] = datetime.now().isoformat()
    if "analysis_history" not in profile:
        profile["analysis_history"] = []
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
    print(f"✅ Profil kaydedildi.")

def save_analysis_to_history(analysis: dict) -> None:
    """
    Bir analiz sonucunu profildeki geçmişe ekler.
    En fazla 10 analiz saklar.
    """
    profile = get_profile()
    if "analysis_history" not in profile:
        profile["analysis_history"] = []

    entry = {
        "timestamp":        datetime.now().isoformat(),
        "product_name":     analysis.get("urun_adi", ""),
        "recommended_size": analysis.get("recommended_size", ""),
        "confidence":       analysis.get("confidence", 0),
        "allergy_warning":  analysis.get("allergy_warning"),
        "llm_comment":      analysis.get("llm_comment", ""),
        "source_url":       analysis.get("source_url", ""),
        "image_url":        analysis.get("image_url", ""),
        "fabric":           analysis.get("fabric", ""),
        "brand":            analysis.get("brand", "")
    }

    # En başa ekle (en yeni üstte)
    profile["analysis_history"].insert(0, entry)
    # Maksimum 10 analiz sakla
    profile["analysis_history"] = profile["analysis_history"][:10]

    save_profile(profile)

def update_profile_from_text(text: str) -> dict:
    """
    Kullanıcının yazdığı metinden profil bilgisi çıkarır.
    """
    import re
    profile = get_profile()
    updated = []

    # Boy
    match = re.search(r'boy(?:um)?\s*[=:]?\s*(\d{2,3})', text, re.IGNORECASE)
    if match:
        profile["height"] = float(match.group(1))
        updated.append(f"boy: {match.group(1)}cm")

    # Kilo
    match = re.search(r'kilo(?:m)?\s*[=:]?\s*(\d{2,3})', text, re.IGNORECASE)
    if match:
        profile["weight"] = float(match.group(1))
        updated.append(f"kilo: {match.group(1)}kg")

    # Kalıp tercihi
    if any(w in text.lower() for w in ["bol", "rahat", "loose", "oversized"]):
        profile["preferred_fit"] = "loose"
        updated.append("kalıp: bol")
    elif any(w in text.lower() for w in ["dar", "slim", "fitted"]):
        profile["preferred_fit"] = "slim"
        updated.append("kalıp: dar")

    # Vücut tipi
    body_types = {
        "pear": ["pear", "armut"],
        "apple": ["apple", "elma"],
        "hourglass": ["hourglass", "kum saati"],
        "rectangle": ["rectangle", "dikdörtgen"],
        "inverted_triangle": ["inverted triangle", "ters üçgen"]
    }
    for btype, keywords in body_types.items():
        if any(k in text.lower() for k in keywords):
            profile["body_type"] = btype
            updated.append(f"vücut tipi: {btype}")

    # Alerji çıkarma
    allergy_map = {
        "polyester": ["polyester"],
        "wool": ["wool", "yün", "yun"],
        "nylon": ["nylon", "naylon"],
        "acrylic": ["acrylic", "akrilik"],
    }
    for allergen, keywords in allergy_map.items():
        if any(k in text.lower() for k in keywords):
            if allergen not in profile["fabric_allergies"]:
                profile["fabric_allergies"].append(allergen)
                updated.append(f"alerji: {allergen}")

    if updated:
        save_profile(profile)
        print(f"📝 Güncellenen alanlar: {', '.join(updated)}")

    return profile

def profile_to_context(profile: dict) -> str:
    """Profili LLM'e context olarak verilecek formata çevirir."""
    if not any([profile.get("height"), profile.get("preferred_fit"),
                profile.get("fabric_allergies"), profile.get("body_type")]):
        return ""

    lines = ["[User Profile]"]
    if profile.get("height"):
        lines.append(f"- Height: {profile['height']}cm")
    if profile.get("weight"):
        lines.append(f"- Weight: {profile['weight']}kg")
    if profile.get("preferred_fit"):
        lines.append(f"- Preferred fit: {profile['preferred_fit']}")
    if profile.get("body_type"):
        lines.append(f"- Body type: {profile['body_type']}")
    if profile.get("fabric_allergies"):
        lines.append(f"- Fabric allergies: {', '.join(profile['fabric_allergies'])}")
    if profile.get("disliked_colors"):
        lines.append(f"- Dislikes colors: {', '.join(profile['disliked_colors'])}")

    return "\n".join(lines)