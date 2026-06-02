// ============================================================
// FASHION STYLIST AI AGENT — content.js
// Trendyol: API ile yorum çekme (Seçenek B)
// Diğer siteler: DOM okuma (Seçenek A)
// ============================================================

// Her site için DOM seçicileri
function getSelectors() {
  const host = window.location.hostname;
  if (host.includes("trendyol")) {
    return {
      name:        ".product-title",
      fabric:      ".attribute-item",
      modelHeight: ".attribute-item",
      image:       ".product-slide img, [class*='product-image'] img",
      price:       ".new-price, .campaign-price .new-price"
    };
  }
  if (host.includes("hepsiburada")) {
    return {
      name:        "h1[itemprop='name']",
      fabric:      ".technical-details td",
      modelHeight: ".technical-details td",
      image:       ".product-image img",
      price:       ".price-value",
      reviews:     ".herContent .comment-text, .reviewText"
    };
  }
  if (host.includes("amazon")) {
    return {
      name:        "#productTitle",
      fabric:      ".prodDetTable tr",
      modelHeight: ".prodDetTable tr",
      image:       "#landingImage",
      price:       ".a-price-whole",
      reviews:     "[data-hook='review-body'] span, .review-text"
    };
  }
  if (host.includes("zara")) {
    return {
      name:        ".product-detail-info__header-name",
      fabric:      ".product-detail-extra-detail__composition",
      modelHeight: ".product-detail-extra-detail__measurements",
      image:       ".media-image__image",
      price:       ".money-amount__main",
      reviews:     ".review-content__description"
    };
  }
  // Genel fallback
  return {
    name:        "h1",
    fabric:      "[class*='fabric'], [class*='material']",
    modelHeight: "[class*='model'], [class*='size']",
    image:       ".product-image img, .main-image img",
    price:       "[class*='price']",
    reviews:     "[class*='review'] [class*='text'], [class*='comment'] [class*='body']"
  };
}

// ── YARDIMCI: Kumaş ve manken boyunu çıkar ──
// Hem eski tablo (tr) hem yeni Trendyol (div.attribute-item) yapısını destekler
function extractFabricAndHeight(selector) {
  let fabric = "";
  let modelHeight = null;
  const rows = document.querySelectorAll(selector);

  rows.forEach(row => {
    const nameEl  = row.querySelector(".name");
    const valueEl = row.querySelector(".value");
    let key   = nameEl  ? nameEl.textContent.trim().toLowerCase() : "";
    let value = valueEl ? valueEl.textContent.trim() : "";
    if (!key) key = row.textContent.toLowerCase();

    if (
      key.includes("kumaş") || key.includes("materyal") ||
      key.includes("fabric") || key.includes("material") ||
      key.includes("composition") || key.includes("içerik")
    ) {
      fabric = value || row.textContent.trim();
    }
    if (key.includes("model") || key.includes("manken")) {
      const match = (value || row.textContent).match(/(\d{2,3})\s*cm/i);
      if (match) modelHeight = parseFloat(match[1]);
    }
  });

  return { fabric, modelHeight };
}

// ── SEÇENEK A: DOM'dan yorum çekme (Trendyol dışı siteler) ──
function extractReviewsFromDOM(selector) {
  if (!selector) return [];
  const elements = document.querySelectorAll(selector);
  const reviews = [];
  elements.forEach(el => {
    const text = el.textContent.trim();
    if (text.length > 10) {  // Çok kısa metinleri atla
      reviews.push(text);
    }
  });
  // İlk 10 yorumu döndür (çok fazla veri göndermeyelim)
  return reviews.slice(0, 10);
}

// ── SEÇENEK B: Trendyol API'sinden yorum çekme ──
// URL'den contentId'yi çıkar: ".../...-p-696118489" → "696118489"
function getTrendyolContentId() {
  const match = window.location.href.match(/[^/]+-p-(\d+)/);
  return match ? match[1] : null;
}

// Trendyol review API'sine fetch at, özet istatistikleri döndür
async function fetchTrendyolReviews(contentId) {
  const url =
    `https://apigw.trendyol.com/discovery-storefront-trproductgw-service/` +
    `api/review-read/product-reviews/detailed` +
    `?contentId=${contentId}&page=0&pageSize=20&order=DESC&orderBy=Score&channelId=1`;

  try {
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Accept": "application/json",
        // Trendyol aynı origin'den geldiğini görür — ek header gerekmez
      }
    });

    if (!response.ok) {
      return { error: `API yanıt vermedi: ${response.status}` };
    }

    const data = await response.json();

    if (!data.isSuccess || !data.result) {
      return { error: "API başarısız döndü" };
    }

    const { summary, reviews, aiSummary } = data.result;

    // ── Beden istatistiği: en çok hangi beden alınmış ──
    const sizeStats = {};
    if (summary.productSizes) {
      summary.productSizes.forEach(s => {
        sizeStats[s.name] = s.count;
      });
    }

    // ── Boy dağılımı ──
    const heightStats = {};
    if (summary.heightTags) {
      summary.heightTags.forEach(h => {
        heightStats[h.name] = h.count;
      });
    }

    // ── Kilo dağılımı ──
    const weightStats = {};
    if (summary.weightTags) {
      summary.weightTags.forEach(w => {
        weightStats[w.name] = w.count;
      });
    }

    // ── İlk 20 yorumdan boy/kilo/beden üçlüsünü çıkar ──
    const reviewSamples = [];
    if (reviews) {
      reviews.forEach(r => {
        if (r.height && r.weight && r.productSize) {
          reviewSamples.push({
            height: parseInt(r.height),
            weight: parseInt(r.weight),
            size:   r.productSize,
            comment: r.comment ? r.comment.substring(0, 100) : ""
          });
        }
      });
    }

    return {
      averageRating:     summary.averageRatingFixed,
      totalComments:     summary.totalCommentCount,
      aiSummary:         aiSummary || "",
      sizeStats,          // { S: 1986, M: 1743, ... }
      heightStats,        // { "151-160": 1107, "161-170": 2146, ... }
      weightStats,        // { "51-60": 1616, "61-70": 1021, ... }
      reviewSamples       // [ { height, weight, size, comment }, ... ]
    };

  } catch (err) {
    return { error: `Fetch hatası: ${err.message}` };
  }
}

// ── ANA FONKSİYON: Sayfadan tüm ürün verisini çeker ──
async function extractProduct() {
  const sel  = getSelectors();
  const host = window.location.hostname;

  // Temel ürün bilgileri (tüm siteler için aynı)
  const nameEl  = document.querySelector(sel.name);
  const imageEl = document.querySelector(sel.image);
  const priceEl = document.querySelector(sel.price);

  const name      = nameEl  ? nameEl.textContent.trim()  : "Ürün adı bulunamadı";
  const image     = imageEl ? (imageEl.src || imageEl.dataset.src || "") : "";
  const priceText = priceEl ? priceEl.textContent.trim() : "";
  const price     = parseFloat(priceText.replace(/[^0-9,]/g, "").replace(",", ".")) || null;

  const { fabric, modelHeight } = extractFabricAndHeight(sel.fabric);

  const ogSite = document.querySelector('meta[property="og:site_name"]');
  const brand  = ogSite ? ogSite.content : window.location.hostname.split(".")[1] || "";

  // Yorum verisi — siteye göre farklı yöntem
  let reviewData = null;

  if (host.includes("trendyol")) {
    // SEÇENEK B — Trendyol API
    const contentId = getTrendyolContentId();
    if (contentId) {
      reviewData = await fetchTrendyolReviews(contentId);
    } else {
      reviewData = { error: "contentId URL'den çıkarılamadı" };
    }
  } else {
    // SEÇENEK A — DOM okuma
    const domReviews = extractReviewsFromDOM(sel.reviews);
    reviewData = {
      domReviews,   // [ "yorum metni", ... ]
      source: "dom"
    };
  }

  return {
    product_name: name,
    fabric:       fabric,
    model_height: modelHeight,
    image_url:    image,
    price:        price,
    brand:        brand,
    source_url:   window.location.href,
    review_data:  reviewData   // 👈 YENİ ALAN
  };
}

// extractProduct() fonksiyonu popup tarafından
// chrome.scripting.executeScript ile doğrudan çağrılır.
// Mesajlaşma gerekmez — fonksiyonlar global scope'ta tanımlı.