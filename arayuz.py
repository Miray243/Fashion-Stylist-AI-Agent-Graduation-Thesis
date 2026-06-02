import streamlit as st
import requests
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from user_profile import get_profile, save_profile, profile_to_context
from wardrobe import add_to_wardrobe, get_wardrobe, remove_from_wardrobe, find_compatible, find_compatible_by_image

st.set_page_config(page_title="Fashion Stylist AI", layout="wide")
st.title("Fashion Stylist AI Agent")

col1, col2 = st.columns([1, 2])

# ── Sol: Profil ──────────────────────────────────────────────
with col1:
    st.subheader("Your Profile")
    profile = get_profile()

    with st.form("profile_form"):
        height = st.number_input("Height (cm)", min_value=140, max_value=220,
                                  value=int(profile.get("height") or 165))
        weight = st.number_input("Weight (kg)", min_value=40, max_value=150,
                                  value=int(profile.get("weight") or 60))
        fit_pref = st.selectbox("Preferred Fit",
                                 ["regular", "slim", "loose"],
                                 index=["regular","slim","loose"].index(
                                     profile.get("preferred_fit") or "regular"))
        body_type = st.selectbox("Body Type",
                                  ["unknown", "pear", "apple", "hourglass",
                                   "rectangle", "inverted_triangle"],
                                  index=["unknown","pear","apple","hourglass",
                                         "rectangle","inverted_triangle"].index(
                                      profile.get("body_type") or "unknown"))
        allergies = st.text_input("Fabric Allergies (comma separated)",
                                   value=", ".join(profile.get("fabric_allergies") or []))
        disliked = st.text_input("Disliked Colors (comma separated)",
                                  value=", ".join(profile.get("disliked_colors") or []))

        if st.form_submit_button("💾 Save Profile"):
            profile["height"] = height
            profile["weight"] = weight
            profile["preferred_fit"] = fit_pref
            profile["body_type"] = body_type if body_type != "unknown" else None
            profile["fabric_allergies"] = [a.strip() for a in allergies.split(",") if a.strip()]
            profile["disliked_colors"] = [c.strip() for c in disliked.split(",") if c.strip()]
            save_profile(profile)
            st.success("Profile saved!")
            st.rerun()

    context = profile_to_context(profile)
    if context:
        st.info(context)
    else:
        st.caption("No profile saved yet.")

# ── Sağ: Tab yapısı ──────────────────────────────────────────────
with col2:
    tab1, tab2, tab3 = st.tabs(["🛍️ Recent Analyses", "👗 My Wardrobe", "💬 Chat with Stylist"])

    # ── Tab 1: Son Analizler ─────────────────────────────────────
    with tab1:
        st.caption("Analyses made via the Chrome Extension appear here automatically.")

        profile = get_profile()
        history = profile.get("analysis_history", [])

        if not history:
            st.info("No analyses yet. Open the Chrome Extension on a product page and click **Analyze**.")
        else:
            # Yenile butonu
            if st.button("🔄 Refresh"):
                st.rerun()

            for i, entry in enumerate(history):
                # Zaman damgasını formatla
                try:
                    ts = datetime.fromisoformat(entry["timestamp"])
                    time_str = ts.strftime("%d %b %Y, %H:%M")
                except:
                    time_str = entry.get("timestamp", "")

                # Her analiz bir expander içinde
                with st.expander(
                    f"**{entry.get('product_name', 'Ürün')}** — "
                    f"{entry.get('recommended_size', '?')} beden · {time_str}",
                    expanded=(i == 0)  # İlki açık gelsin
                ):
                    col_a, col_b = st.columns([1, 2])

                    with col_a:
                        st.metric(
                            label="Recommended Size",
                            value=entry.get("recommended_size", "—"),
                        )
                        confidence = entry.get("confidence", 0)
                        st.caption(f"Confidence: %{int(confidence * 100)}")

                        if entry.get("fabric"):
                            st.caption(f"🧵 {entry['fabric']}")

                    with col_b:
                        if entry.get("allergy_warning"):
                            st.warning(f"⚠️ {entry['allergy_warning']}")

                        if entry.get("llm_comment"):
                            st.write(entry["llm_comment"])

                    if entry.get("source_url"):
                        st.markdown(
                            f"[🔗 Ürün sayfasını aç]({entry['source_url']})",
                            unsafe_allow_html=False
                        )

    # ── Tab 2: Gardırop ──────────────────────────────────────────
    with tab2:
        st.caption("Upload clothing photos to build your wardrobe. The AI will check compatibility with new products.")

        # Fotoğraf yükleme
        col_upload, col_list = st.columns([1, 1])

        with col_upload:
            st.subheader("Add Item")
            uploaded = st.file_uploader(
                "Upload a clothing photo",
                type=["jpg", "jpeg", "png", "webp"],
                key="wardrobe_upload"
            )
            label = st.text_input("Label (e.g. 'Black blazer')", key="wardrobe_label")
            category = st.selectbox(
                "Category",
                options=["top", "bottom", "dress", "shoes", "accessory"],
                format_func=lambda x: {
                    "top":       "👕 Üst (tişört, gömlek, kazak, ceket...)",
                    "bottom":    "👖 Alt (pantolon, etek, şort...)",
                    "dress":     "👗 Elbise / Tulum",
                    "shoes":     "👟 Ayakkabı",
                    "accessory": "👜 Aksesuar (çanta, şapka, kemer...)"
                }[x],
                key="wardrobe_category"
            )

            if st.button("➕ Add to Wardrobe") and uploaded:
                # Geçici dosyaya kaydet
                tmp_path = f"tmp_upload_{uploaded.name}"
                with open(tmp_path, "wb") as f:
                    f.write(uploaded.getbuffer())

                with st.spinner("CLIP vektörü hesaplanıyor..."):
                    try:
                        entry = add_to_wardrobe(tmp_path, label or "", category)
                        st.success(f"✅ '{entry['label']}' ({category}) gardıroba eklendi!")
                        os.remove(tmp_path)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Hata: {e}")
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)

        with col_list:
            st.subheader("My Wardrobe")
            wardrobe = get_wardrobe()

            if not wardrobe:
                st.info("Gardırop boş. Sol taraftan fotoğraf ekle.")
            else:
                st.caption(f"{len(wardrobe)} parça")
                for item in wardrobe:
                    c1, c2, c3 = st.columns([1, 2, 1])
                    with c1:
                        if os.path.exists(item["image_path"]):
                            st.image(item["image_path"], width=60)
                    with c2:
                        st.write(f"**{item['label']}**")
                        try:
                            ts = datetime.fromisoformat(item["added_at"])
                            st.caption(ts.strftime("%d %b %Y"))
                        except:
                            pass
                    with c3:
                        if st.button("🗑️", key=f"del_{item['id']}"):
                            remove_from_wardrobe(item["id"])
                            st.rerun()

        # Son analizle uyum kontrolü
        st.divider()
        profile = get_profile()
        history = profile.get("analysis_history", [])

        if history and wardrobe:
            last = history[0]
            product_name = last.get("product_name", "")
            image_url    = last.get("image_url", "")
            st.subheader("Compatibility Check")
            st.caption(f"Last analyzed: **{product_name}**")

            with st.spinner("Uyum hesaplanıyor..."):
                try:
                    results = []
                    if image_url:
                        # Görsel tabanlı karşılaştırma
                        import requests as req_lib
                        import tempfile
                        headers = {"User-Agent": "Mozilla/5.0"}
                        img_resp = req_lib.get(image_url, headers=headers, timeout=10)
                        if img_resp.status_code == 200:
                            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                                tmp.write(img_resp.content)
                                tmp_path = tmp.name
                            results = find_compatible_by_image(tmp_path, top_k=3)
                            os.remove(tmp_path)
                    else:
                        # Fallback: metin tabanlı
                        results = find_compatible(product_name, top_k=3)

                    if results:
                        for r in results:
                            score_pct = int(r["score"] * 100)
                            color = "🟢" if score_pct >= 70 else "🟡" if score_pct >= 50 else "🔴"
                            c1, c2, c3 = st.columns([1, 2, 1])
                            with c1:
                                if os.path.exists(r["image_path"]):
                                    st.image(r["image_path"], width=60)
                            with c2:
                                st.write(f"**{r['label']}**")
                                if r.get("item_category"):
                                    st.caption(f"Kategori: {r['item_category']}")
                            with c3:
                                st.metric("Uyum", f"{color} %{score_pct}")
                except Exception as e:
                    st.error(f"Uyum hesaplanamadı: {e}")
        elif not wardrobe:
            st.info("Uyum kontrolü için gardıroba en az 1 parça ekle.")

    # ── Tab 3: Serbest Sohbet ────────────────────────────────────
    with tab3:
        st.caption("Chat freely with your stylist. Your profile updates automatically.")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Geçmiş mesajları göster
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        # Kullanıcı girişi
        user_input = st.chat_input("Ask anything about style, or tell me about yourself...")

        if user_input:
            with st.chat_message("user"):
                st.write(user_input)
            st.session_state.messages.append({"role": "user", "content": user_input})

            try:
                r = requests.post(
                    "http://127.0.0.1:8000/chat",
                    json={"message": user_input},
                    timeout=60
                )
                result = r.json()
                response = result.get("response", "")

                if result.get("profile_updated"):
                    st.toast("✅ Profile updated!", icon="✅")

            except Exception as e:
                response = f"Error: {e}"

            with st.chat_message("assistant"):
                st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})