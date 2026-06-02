"""
wardrobe.py — CLIP Tabanlı Gardırop Modülü
==========================================
Üç katmanlı uyum analizi:
1. CLIP görsel benzerliği (cosine similarity)
2. Kategori uyumu (üst+alt = tamamlayıcı, üst+üst = çakışan)
3. Renk uyumu (renk teorisi)

Final skor = CLIP×0.4 + Kategori×0.4 + Renk×0.2
"""

import os
import json
import uuid
import shutil
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image
import chromadb
from sentence_transformers import SentenceTransformer

# ── Sabitler ──────────────────────────────────────────────────
WARDROBE_DIR    = "wardrobe_images"
WARDROBE_META   = "wardrobe_meta.json"
CLIP_MODEL      = "clip-ViT-B-32"
COLLECTION_NAME = "wardrobe"

# ── Kategori Sistemi ──────────────────────────────────────────
CATEGORIES = {
    "top":       "a photo of a top, shirt, t-shirt, blouse, sweater, hoodie, jacket, coat",
    "bottom":    "a photo of pants, trousers, skirt, shorts, jeans, leggings",
    "dress":     "a photo of a dress, jumpsuit, overall, romper",
    "shoes":     "a photo of shoes, sneakers, boots, heels, sandals",
    "accessory": "a photo of a bag, hat, scarf, belt, jewelry, accessory",
}

# Kategori uyum matrisi
CATEGORY_COMPATIBILITY = {
    ("top",       "bottom"):    1.0,
    ("bottom",    "top"):       1.0,
    ("top",       "shoes"):     0.8,
    ("shoes",     "top"):       0.8,
    ("bottom",    "shoes"):     0.8,
    ("shoes",     "bottom"):    0.8,
    ("top",       "accessory"): 0.7,
    ("accessory", "top"):       0.7,
    ("bottom",    "accessory"): 0.7,
    ("accessory", "bottom"):    0.7,
    ("dress",     "shoes"):     0.9,
    ("shoes",     "dress"):     0.9,
    ("dress",     "accessory"): 0.8,
    ("accessory", "dress"):     0.8,
    ("top",       "top"):       0.1,
    ("bottom",    "bottom"):    0.1,
    ("top",       "dress"):     0.1,
    ("dress",     "top"):       0.1,
    ("bottom",    "dress"):     0.1,
    ("dress",     "bottom"):    0.1,
}

# ── Model ve ChromaDB (singleton) ─────────────────────────────
_model = None
_chroma_client = None
_collection = None

def _get_model():
    global _model
    if _model is None:
        print("🔄 CLIP modeli yükleniyor...")
        _model = SentenceTransformer(CLIP_MODEL)
        print("✅ CLIP modeli hazır.")
    return _model

def _get_collection():
    global _chroma_client, _collection
    if _collection is None:
        _chroma_client = chromadb.PersistentClient(path="./wardrobe_db")
        try:
            _collection = _chroma_client.get_collection(COLLECTION_NAME)
        except:
            _collection = _chroma_client.create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
    return _collection

def _get_meta() -> list:
    if os.path.exists(WARDROBE_META):
        with open(WARDROBE_META, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def _save_meta(meta: list) -> None:
    with open(WARDROBE_META, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

# ── Kategori Tespiti ──────────────────────────────────────────

def detect_category(image: Image.Image) -> str:
    """CLIP ile görselin kıyafet kategorisini tespit eder."""
    model = _get_model()
    img_embedding = model.encode(image)
    
    best_cat = "top"
    best_score = -1

    for cat, description in CATEGORIES.items():
        text_embedding = model.encode(description)
        # Cosine similarity
        score = float(np.dot(img_embedding, text_embedding) / 
                     (np.linalg.norm(img_embedding) * np.linalg.norm(text_embedding)))
        if score > best_score:
            best_score = score
            best_cat = cat

    return best_cat

def get_category_score(cat1: str, cat2: str) -> float:
    """İki kategori arasındaki uyum skorunu döndürür."""
    return CATEGORY_COMPATIBILITY.get((cat1, cat2), 0.5)

# ── Renk Analizi ─────────────────────────────────────────────

def get_dominant_hsv(image: Image.Image) -> tuple:
    """Görselin dominant rengini HSV olarak döndürür."""
    img = image.copy().convert("RGB").resize((50, 50))
    pixels = np.array(img).reshape(-1, 3).astype(float)
    avg_rgb = pixels.mean(axis=0) / 255.0
    r, g, b = avg_rgb

    mx = max(r, g, b)
    mn = min(r, g, b)
    diff = mx - mn

    # Hue
    if diff == 0:
        h = 0.0
    elif mx == r:
        h = (60 * ((g - b) / diff)) % 360
    elif mx == g:
        h = (60 * ((b - r) / diff) + 120) % 360
    else:
        h = (60 * ((r - g) / diff) + 240) % 360

    s = 0.0 if mx == 0 else diff / mx
    v = mx

    return (h, s, v)

def is_neutral(hsv: tuple) -> bool:
    """Nötr renk mi? (siyah, beyaz, gri, bej...)"""
    h, s, v = hsv
    if s < 0.15:   return True  # Gri tonları
    if v < 0.15:   return True  # Siyah
    if v > 0.92 and s < 0.12: return True  # Beyaz
    return False

def get_color_harmony_score(hsv1: tuple, hsv2: tuple) -> float:
    """
    Renk teorisine göre iki renk arasındaki uyum skoru (0-1).
    
    Kurallar:
    - İkisi nötr: 0.90
    - Biri nötr: 0.85
    - Tamamlayıcı (~180°): 0.90
    - Analog (≤30°): 0.75
    - Triadic (~120°): 0.70
    - Çakışan (60-90°): 0.40
    """
    n1 = is_neutral(hsv1)
    n2 = is_neutral(hsv2)

    if n1 and n2: return 0.90
    if n1 or n2:  return 0.85

    hue_diff = abs(hsv1[0] - hsv2[0])
    if hue_diff > 180:
        hue_diff = 360 - hue_diff

    if 150 <= hue_diff <= 210: return 0.90  # Tamamlayıcı
    if hue_diff <= 30:          return 0.75  # Analog
    if 100 <= hue_diff <= 140:  return 0.70  # Triadic
    if 130 <= hue_diff <= 150:  return 0.72  # Split-complementary
    return 0.40                              # Çakışan

# ── Ana Fonksiyonlar ───────────────────────────────────────────

def add_to_wardrobe(image_path: str, label: str = "", user_category: str = None) -> dict:
    """
    Bir fotoğrafı gardıroba ekler.
    user_category verilirse CLIP tespiti yerine o kullanılır.
    """
    os.makedirs(WARDROBE_DIR, exist_ok=True)
    model = _get_model()
    collection = _get_collection()

    item_id = str(uuid.uuid4())[:8]
    ext = Path(image_path).suffix or ".jpg"
    dest_path = os.path.join(WARDROBE_DIR, f"{item_id}{ext}")
    shutil.copy2(image_path, dest_path)

    img = Image.open(dest_path).convert("RGB")
    embedding = model.encode(img).tolist()

    # Kategori: kullanıcı seçtiyse onu kullan, yoksa CLIP tespit etsin
    if user_category and user_category in CATEGORIES:
        category = user_category
        print(f"📌 Kullanıcı kategorisi: {category}")
    else:
        category = detect_category(img)
        print(f"🤖 CLIP kategori tespiti: {category}")

    hsv = get_dominant_hsv(img)

    collection.add(
        embeddings=[embedding],
        ids=[item_id],
        metadatas=[{
            "label":      label or f"Kıyafet {item_id}",
            "image_path": dest_path,
            "category":   category,
            "hue":        float(hsv[0]),
            "saturation": float(hsv[1]),
            "value":      float(hsv[2]),
            "added_at":   datetime.now().isoformat()
        }]
    )

    entry = {
        "id":         item_id,
        "label":      label or f"Kıyafet {item_id}",
        "image_path": dest_path,
        "category":   category,
        "added_at":   datetime.now().isoformat()
    }
    meta = _get_meta()
    meta.append(entry)
    _save_meta(meta)

    print(f"✅ Gardıroba eklendi: {entry['label']} ({category})")
    return entry


def find_compatible_by_image(query_image_path: str, top_k: int = 3) -> list:
    """
    Üç katmanlı uyum analizi:
    1. CLIP cosine similarity
    2. Kategori uyumu
    3. Renk uyumu
    Final = CLIP×0.4 + Kategori×0.4 + Renk×0.2
    """
    model = _get_model()
    collection = _get_collection()

    try:
        count = collection.count()
    except:
        count = 0
    if count == 0:
        return []

    query_img       = Image.open(query_image_path).convert("RGB")
    query_embedding = model.encode(query_img).tolist()
    query_category  = detect_category(query_img)
    query_hsv       = get_dominant_hsv(query_img)

    n = min(max(top_k * 2, 5), count)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n,
        include=["metadatas", "distances"]
    )

    scored = []
    if results and results["metadatas"] and results["metadatas"][0]:
        for meta, distance in zip(
            results["metadatas"][0],
            results["distances"][0]
        ):
            if meta is None:
                continue
            clip_score     = round(1 - distance, 3)
            item_category  = meta.get("category", "top")
            category_score = get_category_score(query_category, item_category)
            item_hsv       = (meta.get("hue", 0), meta.get("saturation", 0), meta.get("value", 0))
            color_score    = get_color_harmony_score(query_hsv, item_hsv)

            final_score = round(
                clip_score     * 0.4 +
                category_score * 0.4 +
                color_score    * 0.2,
                3
            )

            scored.append({
                "label":          meta.get("label", ""),
                "image_path":     meta.get("image_path", ""),
                "score":          final_score,
                "clip_score":     clip_score,
                "category_score": category_score,
                "color_score":    color_score,
                "query_category": query_category,
                "item_category":  item_category,
                "added_at":       meta.get("added_at", "")
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def find_compatible(product_name: str, top_k: int = 3) -> list:
    """Metin tabanlı uyum — image_url yoksa fallback olarak kullanılır."""
    model = _get_model()
    collection = _get_collection()

    try:
        count = collection.count()
    except:
        count = 0
    if count == 0:
        return []

    text_embedding = model.encode(product_name).tolist()
    results = collection.query(
        query_embeddings=[text_embedding],
        n_results=min(top_k, count),
        include=["metadatas", "distances"]
    )

    compatible = []
    if results and results["metadatas"] and results["metadatas"][0]:
        for meta, distance in zip(
            results["metadatas"][0],
            results["distances"][0]
        ):
            compatible.append({
                "label":      meta.get("label", ""),
                "image_path": meta.get("image_path", ""),
                "score":      round(1 - distance, 3),
                "added_at":   meta.get("added_at", "")
            })

    compatible.sort(key=lambda x: x["score"], reverse=True)
    return compatible


def get_wardrobe() -> list:
    return _get_meta()


def remove_from_wardrobe(item_id: str) -> bool:
    collection = _get_collection()
    meta = _get_meta()
    entry = next((m for m in meta if m["id"] == item_id), None)
    if not entry:
        return False
    if os.path.exists(entry["image_path"]):
        os.remove(entry["image_path"])
    try:
        collection.delete(ids=[item_id])
    except:
        pass
    _save_meta([m for m in meta if m["id"] != item_id])
    print(f"🗑️ Gardıruptan silindi: {entry['label']}")
    return True


def get_compatibility_summary(product_name: str, top_k: int = 3) -> str:
    """Chat context'i için Türkçe uyum özeti."""
    results = find_compatible(product_name, top_k)
    wardrobe = get_wardrobe()

    if not wardrobe:
        return "Kullanıcının gardırobunda henüz kıyafet yok."
    if not results:
        return f"Gardıropta {len(wardrobe)} parça var ama uyum hesaplanamadı."

    lines = [f"Gardırop ({len(wardrobe)} parça) uyum analizi — '{product_name}':"]
    for r in results:
        pct = int(r["score"] * 100)
        lines.append(f"- {r['label']}: %{pct} uyumlu")

    best = results[0]
    if best["score"] > 0.7:
        lines.append(f"✅ En uyumlu: {best['label']} (%{int(best['score']*100)})")
    elif best["score"] > 0.5:
        lines.append(f"⚠️ Orta uyum: {best['label']} (%{int(best['score']*100)})")
    else:
        lines.append("❌ Gardıropla düşük uyum.")

    return "\n".join(lines)