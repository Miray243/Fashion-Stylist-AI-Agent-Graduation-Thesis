from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import os
from llm import chat as ollama_chat
from decision_engine import run_decision_engine
from user_profile import save_analysis_to_history

app = FastAPI()

class Urun(BaseModel):
    urun_adi: str
    kumas: Optional[str] = None
    manken_boyu: Optional[float] = None
    fiyat: Optional[float] = None
    review_data: Optional[dict] = None
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    brand: Optional[str] = None

@app.get("/")
def merhaba():
    return {"mesaj": "Fashion Stylist AI Agent çalışıyor!"}

@app.post("/urun-analiz")
def urun_analiz(urun: Urun):
    # 1. Deterministik karar motoru çalışır
    decision = run_decision_engine(
        product_name=urun.urun_adi,
        fabric=urun.kumas or ""
    )

    size_rec  = decision["size_recommendation"]
    warnings  = decision["allergy_warnings"]

    # Yorum verisinden ek bağlam oluştur
    review_context = ""
    if urun.review_data and not urun.review_data.get("error"):
        rd = urun.review_data
        if rd.get("aiSummary"):
            review_context = f"\nCustomer review summary: {rd['aiSummary']}"
        if rd.get("sizeStats"):
            top_sizes = sorted(rd["sizeStats"].items(), key=lambda x: x[1], reverse=True)[:3]
            top_str = ", ".join([f"{s}({c})" for s, c in top_sizes])
            review_context += f"\nMost purchased sizes: {top_str}"

    # 2. LLM algoritmik kararı Türkçe anlatsın.

    llm_prompt = f"""Sen bir moda stilistisin. Aşağıdaki algoritmik kararı kullanıcıya Türkçe, samimi ve kısa (2-3 cümle) şekilde anlat.

Ürün: {urun.urun_adi}
Kumaş: {urun.kumas or 'belirtilmemiş'}
{review_context}

Karar:
- Önerilen beden: {size_rec['recommended_size']} (kullanıcının normal bedeni: {size_rec['original_size']})
- Sebep: {size_rec['reason']}
- Güven: %{int(size_rec['confidence']*100)}
- Alerji uyarısı: {', '.join(warnings) if warnings else 'Yok'}

Sadece kullanıcıya yönelik Türkçe tavsiyeyi yaz, başka bir şey ekleme."""

    llm_response = ollama_chat(
        [{"role": "user", "content": llm_prompt}],
        temperature=0.7, max_tokens=256
    )
    cevap = (llm_response["message"].get("content") or "").strip()

    if not cevap:
        cevap = (
            f"{size_rec['recommended_size']} beden önerilir. "
            f"Sebep: {size_rec['reason']} "
            f"(Güven: %{int(size_rec['confidence']*100)})"
        )

    # Alerji uyarısı — ilk uyarıyı string olarak döndür
    allergy_warning_str = warnings[0] if warnings else None

    # ── Gardırop uyumu — ürün fotoğrafıyla ──
    wardrobe_compatibility = []
    kombin_oneri = ""

    if urun.image_url:
        try:
            import requests as req_lib
            import tempfile
            from wardrobe import find_compatible_by_image, get_wardrobe

            wardrobe = get_wardrobe()
            if wardrobe:
                headers = {"User-Agent": "Mozilla/5.0"}
                img_response = req_lib.get(urun.image_url, headers=headers, timeout=10)
                if img_response.status_code == 200:
                    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                        tmp.write(img_response.content)
                        tmp_path = tmp.name

                    wardrobe_compatibility = find_compatible_by_image(tmp_path, top_k=3)
                    os.remove(tmp_path)

                    # ── LLM kombin önerisi ──
                    if wardrobe_compatibility:
                        uyumlu = [
                            f"- {r['label']} (%{int(r['score']*100)} uyum, "
                            f"kategori:{r.get('item_category','?')}, "
                            f"renk skoru:%{int(r.get('color_score',0)*100)}, "
                            f"kategori skoru:%{int(r.get('category_score',0)*100)})"
                            for r in wardrobe_compatibility
                        ]
                        kombin_prompt = f"""Sen bir moda stilistisin. Kullanıcı yeni bir ürün inceliyor ve gardırobundaki parçalarla kombinlemek istiyor.

Yeni ürün: {urun.urun_adi}
Kumaş: {urun.kumas or 'belirtilmemiş'}

Gardıroptan en uyumlu parçalar (algoritma hesapladı):
{chr(10).join(uyumlu)}

Bu bilgilere dayanarak:
1. En iyi kombinasyonu öner (hangi parçayla, nasıl giyilmeli)
2. Neden uyumlu olduğunu kısaca açıkla (renk/kategori)
3. Varsa ayakkabı veya aksesuar önerisi ekle

Türkçe, samimi, 3-4 cümle. Sadece öneriyi yaz."""

                        kombin_response = ollama_chat(
                            [{"role": "user", "content": kombin_prompt}],
                            temperature=0.7, max_tokens=512
                        )
                        if kombin_response.get("done_reason") == "length":
                            raise RuntimeError("Kombin önerisi çıktı sınırına ulaştı.")
                        kombin_oneri = (kombin_response["message"].get("content") or "").strip()
                        if not kombin_oneri:
                            raise RuntimeError("Kombin önerisi boş döndü.")

        except Exception as e:
            print(f"⚠️ Gardırop uyumu veya kombin önerisi hesaplanamadı: {e}")

    response_data = {
        "recommended_size":       size_rec["recommended_size"],
        "confidence":             size_rec["confidence"],
        "allergy_warning":        allergy_warning_str,
        "llm_comment":            cevap,
        "kombin_oneri":           kombin_oneri,
        "urun_adi":               urun.urun_adi,
        "analiz":                 cevap,
        "size_recommendation":    size_rec,
        "allergy_warnings":       warnings,
        "fabric":                 urun.kumas or "",
        "source_url":             urun.source_url or "",
        "brand":                  urun.brand or "",
        "wardrobe_compatibility": wardrobe_compatibility,
    }

    # Analizi geçmişe kaydet
    save_analysis_to_history({
        **response_data,
        "source_url": urun.source_url or "",
        "brand":      urun.brand or "",
        "image_url":  urun.image_url or "",
    })

    return response_data


class ChatMessage(BaseModel):
    message: str

@app.post("/chat")
def chat(req: ChatMessage):
    from user_profile import update_profile_from_text, get_profile, profile_to_context
    from wardrobe import get_compatibility_summary, get_wardrobe

    old_profile = get_profile()
    update_profile_from_text(req.message)
    new_profile = get_profile()
    profile_updated = old_profile != new_profile

    # ── Context katmanları ──
    context_parts = []

    # 1. Kullanıcı profili
    profile_context = profile_to_context(new_profile)
    if profile_context:
        context_parts.append(profile_context)

    # 2. Son analiz edilen ürün
    history = new_profile.get("analysis_history", [])
    if history:
        last = history[0]
        context_parts.append(
            f"[Son Analiz Edilen Ürün]\n"
            f"- Ürün: {last.get('product_name', '')}\n"
            f"- Önerilen beden: {last.get('recommended_size', '')}\n"
            f"- Kumaş: {last.get('fabric', 'belirtilmemiş')}\n"
            f"- Stilist yorumu: {last.get('llm_comment', '')}"
        )

    # 3. Gardırop uyum özeti (gardırop doluysa)
    wardrobe = get_wardrobe()
    if wardrobe and history:
        product_name = history[0].get("product_name", "")
        if product_name:
            compat_summary = get_compatibility_summary(product_name, top_k=3)
            context_parts.append(f"[Gardırop Uyum Analizi]\n{compat_summary}")

    # ── Prompt oluştur ──
    system = """Sen deneyimli bir moda stilistisin. 
Kullanıcının profili, son incelediği ürün ve gardırop bilgileri sana verildi.
Bu bilgileri kullanarak Türkçe, samimi ve yardımsever cevaplar ver.
Özellikle kombin önerileri, gardırop uyumu ve stil tavsiyeleri konusunda uzmansin.
Basit soruları kısa ve doğrudan yanıtla; gerekmedikçe uzun tablo oluşturma."""

    full_context = "\n\n".join(context_parts)
    user_message = req.message

    if full_context:
        prompt_content = f"{full_context}\n\nKullanıcı sorusu: {user_message}"
    else:
        prompt_content = user_message

    # Direkt Ollama çağrısı — ajan döngüsü yok
    llm_response = ollama_chat(
        [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt_content}
        ],
        temperature=0.7, max_tokens=512
    )
    response = (llm_response["message"].get("content") or "").strip()
    if not response:
        raise RuntimeError("Ollama boş sohbet yanıtı döndürdü.")

    return {
        "response": response,
        "profile_updated": profile_updated
    }
