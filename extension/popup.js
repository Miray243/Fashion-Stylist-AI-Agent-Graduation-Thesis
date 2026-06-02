// ── Sekme geçişi ──
function switchTab(tab) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  document.getElementById('tab-' + tab).classList.add('active');
  document.getElementById('content-' + tab).classList.add('active');
}

// ── Sayfa yüklenince ürün verisini çek ──
document.addEventListener('DOMContentLoaded', () => {

  // Sekme butonlarına event listener ekle (onclick yerine)
  document.getElementById('tab-analiz').addEventListener('click', () => switchTab('analiz'));
  document.getElementById('tab-yorumlar').addEventListener('click', () => switchTab('yorumlar'));
  document.getElementById('analyze-btn').addEventListener('click', runAnalysis);

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const tab = tabs[0];

    // Site etiketi
    try {
      const host = new URL(tab.url).hostname.replace('www.', '');
      document.getElementById('site-label').textContent = host;
    } catch(e) {
      document.getElementById('site-label').textContent = '';
    }

    // executeScript ile MAIN world'deki extractProduct() fonksiyonunu çağır
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      world: 'MAIN',
      func: async () => {
        if (typeof extractProduct === 'undefined') return null;
        return await extractProduct();
      }
    }, (results) => {
      if (chrome.runtime.lastError) {
        document.getElementById('product-name').textContent =
          'Hata: ' + chrome.runtime.lastError.message;
        return;
      }
      if (!results || !results[0] || !results[0].result) {
        document.getElementById('product-name').textContent = 'Ürün bilgisi alınamadı';
        return;
      }

      const data = results[0].result;
      window._productData = data;

      // Ürün adı
      document.getElementById('product-name').textContent =
        data.product_name || 'Ürün adı bulunamadı';

      // Fiyat chip
      if (data.price) {
        document.getElementById('price-chip').textContent =
          data.price.toLocaleString('tr-TR') + ' TL';
      }

      // Kumaş chip
      if (data.fabric) {
        const short = data.fabric.length > 30
          ? data.fabric.substring(0, 30) + '…'
          : data.fabric;
        document.getElementById('fabric-chip').textContent = short;
      }

      // Yorum istatistikleri
      fillReviewTab(data.review_data);
    });
  });
});

// ── Yorumlar sekmesini doldur ──
function fillReviewTab(reviewData) {
  if (!reviewData || reviewData.error) return;

  if (reviewData.averageRating) {
    document.getElementById('avg-rating').textContent = reviewData.averageRating;
  }
  if (reviewData.totalComments) {
    document.getElementById('total-comments').textContent =
      reviewData.totalComments.toLocaleString('tr-TR');
  }

  // Beden bar chart
  if (reviewData.sizeStats && Object.keys(reviewData.sizeStats).length > 0) {
    const sizes = reviewData.sizeStats;
    const maxVal = Math.max(...Object.values(sizes));
    const container = document.getElementById('size-bars');
    container.innerHTML = '';

    Object.entries(sizes)
      .sort((a, b) => b[1] - a[1])
      .forEach(([size, count]) => {
        const pct = Math.round((count / maxVal) * 100);
        container.innerHTML += `
          <div class="size-bar-row">
            <span class="size-bar-label">${size}</span>
            <div class="size-bar-track">
              <div class="size-bar-fill" style="width:${pct}%"></div>
            </div>
            <span class="size-bar-count">${count.toLocaleString('tr-TR')}</span>
          </div>`;
      });
  }

  // Trendyol AI özeti
  if (reviewData.aiSummary) {
    document.getElementById('ai-summary-text').textContent = reviewData.aiSummary;
    document.getElementById('ai-summary-box').style.display = 'block';
  }
}

// ── Analiz Et butonu ──
async function runAnalysis() {
  const btn = document.getElementById('analyze-btn');
  const resultArea = document.getElementById('result-area');
  const errorBox = document.getElementById('error-box');

  btn.disabled = true;
  btn.innerHTML = '<div class="loading"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>';
  errorBox.style.display = 'none';
  resultArea.style.display = 'none';

  const data = window._productData;
  if (!data) {
    showError('Ürün verisi bulunamadı. Sayfayı yenileyin.');
    resetBtn();
    return;
  }

  try {
    const analysisRes = await fetch('http://127.0.0.1:8000/urun-analiz', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        urun_adi:    data.product_name,
        kumas:       data.fabric       || null,
        manken_boyu: data.model_height || null,
        fiyat:       data.price        || null,
        review_data: data.review_data  || null,
        image_url:   data.image_url    || null,
        source_url:  data.source_url   || null,
        brand:       data.brand        || null
      })
    });

    if (!analysisRes.ok) throw new Error('Sunucu yanıt vermedi: ' + analysisRes.status);
    const analysis = await analysisRes.json();

    document.getElementById('size-result').textContent =
      analysis.recommended_size || '?';
    document.getElementById('confidence-badge').textContent =
      analysis.confidence ? '%' + Math.round(analysis.confidence * 100) + ' güven' : '—';

    const alerjiWarn = document.getElementById('alerji-warn');
    if (analysis.allergy_warning) {
      document.getElementById('alerji-text').textContent = analysis.allergy_warning;
      alerjiWarn.style.display = 'flex';
    } else {
      alerjiWarn.style.display = 'none';
    }

    document.getElementById('llm-text').textContent =
      analysis.llm_comment || 'Yorum alınamadı.';

    // Gardırop uyumu
    const wardrobeSection = document.getElementById('wardrobe-section');
    const wardrobeItems   = document.getElementById('wardrobe-items');
    const compat = analysis.wardrobe_compatibility;

    if (compat && compat.length > 0) {
      wardrobeItems.innerHTML = '';
      compat.forEach(item => {
        const pct = Math.round(item.score * 100);
        const cls = pct >= 70 ? 'score-high' : pct >= 50 ? 'score-mid' : 'score-low';
        const icon = pct >= 70 ? '🟢' : pct >= 50 ? '🟡' : '🔴';
        wardrobeItems.innerHTML += `
          <div class="wardrobe-item">
            <img src="${item.image_path}" onerror="this.style.display='none'" />
            <span class="wardrobe-item-label">${item.label}</span>
            <span class="wardrobe-score ${cls}">${icon} %${pct}</span>
          </div>`;
      });
      wardrobeSection.style.display = 'block';
    } else {
      wardrobeSection.style.display = 'none';
    }

    // Kombin önerisi
    const kombinBox  = document.getElementById('kombin-box');
    const kombinText = document.getElementById('kombin-text');
    if (analysis.kombin_oneri) {
      kombinText.textContent = analysis.kombin_oneri;
      kombinBox.style.display = 'block';
    } else {
      kombinBox.style.display = 'none';
    }

    resultArea.style.display = 'block';
    btn.innerHTML = 'Analiz Tamamlandı';
    btn.style.background = '#0F6E56';

  } catch (err) {
    showError('Bağlantı hatası: ' + err.message + '\n\nFastAPI çalışıyor mu? (uvicorn main:app)');
    resetBtn();
  }
}

function showError(msg) {
  const box = document.getElementById('error-box');
  box.textContent = msg;
  box.style.display = 'block';
}

function resetBtn() {
  const btn = document.getElementById('analyze-btn');
  btn.disabled = false;
  btn.innerHTML = 'Tekrar Dene';
  btn.style.background = '#534AB7';
}