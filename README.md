# Fashion Stylist AI Agent

**Graduation Thesis — Çukurova University, Computer Engineering Department**

| | |
|---|---|
| **Student** | Miray Balıkoğlu |
| **Advisor** | Prof. Dr. Umut Orhan |
| **University** | Çukurova University |
| **Department** | Computer Engineering |
| **Date** | June 2026 |

---

##  Overview

E-commerce fashion return rates have reached **30–40% globally**, with size mismatches being the leading cause. This project presents a multi-layered AI decision agent that provides **personalized, context-aware clothing recommendations** during active shopping sessions.

The system combines:
- A **rule-based decision engine** for deterministic, explainable size recommendations
- A **ReAct-framework LLM agent** (LLaMA 3.3 70B via Groq) for natural language styling advice
- A **CLIP-based visual wardrobe analysis** module for outfit compatibility scoring
- A **Trendyol review API integration** for community-sourced sizing statistics

---

##  System Architecture

```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│   Chrome Extension  │────▶│   FastAPI Backend     │────▶│  Streamlit Frontend │
│                     │     │                       │     │                     │
│ • Product data      │     │ • Decision engine     │     │ • Profile manager   │
│ • Review API        │     │ • LLM agent (ReAct)   │     │ • Recent analyses   │
│ • Popup UI          │     │ • CLIP wardrobe        │     │ • Wardrobe tab      │
│ • 9 e-commerce sites│     │ • Combo suggestions   │     │ • Chat with stylist │
└─────────────────────┘     └──────────────────────┘     └─────────────────────┘
```

---

##  Key Features

###  Smart Size Recommendation
- Rule-based engine detects product fit type (slim/regular/loose) from product name
- Adjusts recommendation based on user's fit preference (+/- 1 size step)
- BMI-based size estimation from user profile
- **88% accuracy** on test set with calibrated confidence scores (85–95%)

###  Fabric Allergy Detection
- Detects allergens (polyester, wool, nylon, acrylic) in fabric composition
- Supports Turkish and English descriptions
- Shows warning in popup before purchase

###  Trendyol Review API Integration
- Fetches size distribution, height/weight stats of actual buyers
- Retrieves AI-generated review summary from Trendyol
- Enriches recommendations with community-validated data

###  CLIP-Based Wardrobe Compatibility
Three-layer compatibility scoring:

| Layer | Method | Weight |
|---|---|---|
| Visual similarity | CLIP cosine similarity (clip-ViT-B-32) | 40% |
| Category compatibility | Top+Bottom=1.0, Top+Top=0.1 | 40% |
| Color harmony | HSV-based color theory rules | 20% |

###  Conversational Stylist
- Context-aware chat using last analyzed product + wardrobe info
- RAG over fashion knowledge base (body types, color theory, fabric guide)
- Persistent user profile across sessions

---

##  Project Structure

```
Fashion-Stylist-AI-Agent-Graduation-Thesis/
│
├── agent.py              # ReAct LLM agent with RAG
├── main.py               # FastAPI backend (endpoints)
├── decision_engine.py    # Rule-based size recommendation
├── wardrobe.py           # CLIP wardrobe compatibility
├── arayuz.py             # Streamlit frontend
├── user_profile.py       # Persistent user profile management
│
├── extension/
│   ├── manifest.json     # Chrome Extension MV3
│   ├── content.js        # Product data extraction + Trendyol API
│   ├── popup.html        # Extension popup UI
│   └── popup.js          # Popup logic
│
├── dataset/              # Fashion knowledge base (RAG)
│   ├── body_type_guide.txt
│   ├── color_theory_analysis.txt
│   └── fabric_and_care_guide.txt
│
├── requirements.txt
└── README.md
```

---

##  Installation & Setup

### Prerequisites
- Python 3.10+
- Google Chrome (for extension)
- Groq API key → [console.groq.com](https://console.groq.com)

### 1. Clone the repository
```bash
git clone https://github.com/Miray243/Fashion-Stylist-AI-Agent-Graduation-Thesis.git
cd Fashion-Stylist-AI-Agent-Graduation-Thesis
```

### 2. Install dependencies
```bash
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Set up environment variables
Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Run the system

**Terminal 1 — FastAPI backend:**
```bash
uvicorn main:app
```

**Terminal 2 — Streamlit frontend:**
```bash
streamlit run arayuz.py
```

The app creates `user_profile.json`, `wardrobe_meta.json`, `wardrobe_db/`, and `wardrobe_images/` locally as you use it. These generated files are excluded from version control.

### 5. Install Chrome Extension
1. Open Chrome → `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked** → select the `extension/` folder

---

##  Supported E-Commerce Platforms

| Platform | Review Integration | Product Data |
|---|---|---|
| Trendyol |  API (full stats) |  Full |
| Hepsiburada | DOM |  Full |
| Amazon Turkey | DOM |  Full |
| Zara | DOM |  Full |
| Mango | DOM |  Full |
| N11 | DOM | Partial |
| Boyner | DOM | Partial |
| LCWaikiki | DOM | Partial |
| Koton | DOM | Partial |

---

##  Results

| Metric | Result |
|---|---|
| Decision engine accuracy | 88% |
| Allergy detection recall | 100% |
| Review API success rate | 100% (20/20 pages) |
| End-to-end analysis latency | ~4.2 seconds |
| Wardrobe compatibility (top+bottom) | ~84–87% |
| Wardrobe compatibility (top+top) | ~49–53% (correctly low) |

---

##  Technical Stack

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.13.3 | Backend language |
| FastAPI | Latest | REST API |
| Streamlit | Latest | Web UI |
| ChromaDB | 0.4.22 | Vector database (RAG + wardrobe) |
| sentence-transformers | 2.5.1 | CLIP + text embeddings |
| Groq SDK | 0.5.0 | LLM inference (LLaMA 3.3 70B) |
| Pillow | Latest | Image processing |
| Chrome Extension MV3 | — | Browser integration |

---

##  License

This project was developed as a graduation thesis. All rights reserved © 2026 Miray Balıkoğlu.
