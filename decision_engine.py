from user_profile import get_profile

# Beden sıralaması
SIZE_ORDER = ["XXS", "XS", "S", "M", "L", "XL", "XXL", "3XL"]

# Alerji anahtar kelimeleri
ALLERGY_KEYWORDS = {
    "polyester": ["polyester", "poly"],
    "wool":      ["wool", "yün", "yun"],
    "nylon":     ["nylon", "naylon"],
    "acrylic":   ["acrylic", "akrilik"],
    "latex":     ["latex"],
}

def detect_fit_from_text(text: str) -> str:
    """
    Ürün adı veya açıklamasından kalıp bilgisi çıkarır.
    Döner: 'slim' | 'loose' | 'regular'
    """
    text = text.lower()
    slim_keywords  = ["slim", "slim fit", "fitted", "tight", "skinny", "dar"]
    loose_keywords = ["loose", "oversized", "baggy", "relaxed", "wide", "bol"]

    slim_score  = sum(1 for k in slim_keywords  if k in text)
    loose_score = sum(1 for k in loose_keywords if k in text)

    if slim_score > loose_score:
        return "slim"
    elif loose_score > slim_score:
        return "loose"
    return "regular"


def recommend_size(product_name: str, user_size: str = "M") -> dict:
    """
    Deterministik beden önerisi.
    Kural 1: Ürün slim fit + kullanıcı loose sever → +1 beden
    Kural 2: Ürün loose fit + kullanıcı slim sever → -1 beden
    Kural 3: Uyumlu → aynı beden
    """
    profile = get_profile()
    user_pref = profile.get("preferred_fit") or "regular"

    if user_size not in SIZE_ORDER:
        user_size = "M"

    current_idx = SIZE_ORDER.index(user_size)
    product_fit = detect_fit_from_text(product_name)

    # Karar kuralları
    if product_fit == "slim" and user_pref == "loose":
        new_idx = min(current_idx + 1, len(SIZE_ORDER) - 1)
        reason = (f"This product has a slim fit, but you prefer loose. "
                  f"Sizing up from {user_size} to {SIZE_ORDER[new_idx]} is recommended.")
        confidence = 0.90

    elif product_fit == "loose" and user_pref == "slim":
        new_idx = max(current_idx - 1, 0)
        reason = (f"This product has a loose fit, but you prefer slim. "
                  f"Sizing down from {user_size} to {SIZE_ORDER[new_idx]} is recommended.")
        confidence = 0.85

    else:
        new_idx = current_idx
        reason = (f"The product fit ({product_fit}) matches your preference ({user_pref}). "
                  f"Your regular size {user_size} should work well.")
        confidence = 0.95

    return {
        "recommended_size": SIZE_ORDER[new_idx],
        "original_size": user_size,
        "product_fit": product_fit,
        "reason": reason,
        "confidence": confidence
    }


def check_allergies(fabric: str) -> list:
    """
    Kullanıcının kumaş alerjilerini kontrol eder.
    """
    profile = get_profile()
    allergies = profile.get("fabric_allergies") or []
    warnings = []

    fabric_lower = fabric.lower()
    for allergen in allergies:
        keywords = ALLERGY_KEYWORDS.get(allergen.lower(), [allergen.lower()])
        if any(k in fabric_lower for k in keywords):
            warnings.append(
                f"⚠️ Warning: This product contains {allergen}, "
                f"which you are allergic to."
            )

    return warnings


def estimate_size_from_profile() -> str:
    """
    Kullanıcının boy ve kilosundan beden tahmini yapar.
    """
    profile = get_profile()
    height = profile.get("height")
    weight = profile.get("weight")

    if not height or not weight:
        return "M"

    bmi = weight / ((height / 100) ** 2)

    if bmi < 18.5: return "XS"
    if bmi < 21:   return "S"
    if bmi < 24:   return "M"
    if bmi < 27:   return "L"
    if bmi < 30:   return "XL"
    return "XXL"


def run_decision_engine(product_name: str, fabric: str) -> dict:
    """
    Ana karar motoru — tüm kontrolleri çalıştırır.
    FastAPI ve agent tarafından çağrılır.
    """
    user_size    = estimate_size_from_profile()
    size_result  = recommend_size(product_name, user_size)
    allergy_warnings = check_allergies(fabric)

    return {
        "estimated_user_size": user_size,
        "size_recommendation": size_result,
        "allergy_warnings": allergy_warnings
    }