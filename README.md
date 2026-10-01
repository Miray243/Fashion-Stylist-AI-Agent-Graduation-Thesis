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

This project provides **personalized, context-aware clothing recommendations** during online shopping. It combines rule-based size advice with a fashion knowledge base and optional visual wardrobe matching.

The system combines:
- A **rule-based decision engine** for deterministic, explainable size recommendations
- A **local Ollama LLM agent** (default: Llama 3.1 8B) with fashion knowledge retrieval tools
- A **CLIP-based visual wardrobe analysis** module for outfit compatibility scoring
- A **Trendyol review API integration** for community-sourced sizing statistics

---

##  System Architecture

```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│   Chrome Extension  │────▶│   FastAPI Backend     │────▶│  Streamlit Frontend │
│                     │     │                       │     │                     │
│ • Product data      │     │ • Decision engine     │     │ • Profile manager   │
│ • Review API        │     │ • LLM agent + tools   │     │ • Recent analyses   │
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
- Returns a rule-based confidence value; it is not a measured probability of fit

###  Fabric Allergy Detection
- Detects allergens (polyester, wool, nylon, acrylic) in fabric composition
- Supports Turkish and English descriptions
- Shows warning in popup before purchase

###  Trendyol Review API Integration
- Attempts to fetch size statistics and a review summary from Trendyol when available
- Adds that review context to the product analysis

###  CLIP-Based Wardrobe Compatibility
Three-layer compatibility scoring:

| Layer | Method | Weight |
|---|---|---|
| Visual similarity | CLIP cosine similarity (clip-ViT-B-32) | 40% |
| Category compatibility | Top+Bottom=1.0, Top+Top=0.1 | 40% |
| Color harmony | HSV-based color theory rules | 20% |

###  Conversational Stylist
- Context-aware chat using last analyzed product + wardrobe info
- The styling agent can retrieve fashion knowledge (body types, color theory, fabric guide)
- Persistent user profile across sessions

---

##  Project Structure

```
Fashion-Stylist-AI-Agent-Graduation-Thesis/
│
├── agent.py              # Ollama tool-call agent with RAG
├── llm.py                # Shared Ollama chat client
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
- Python 3.12 (verified installation)
- Google Chrome (for extension)
- Ollama installed and running locally; install the model with `ollama pull llama3.1:8b` if needed

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

### 3. Optional local model settings
The default is the locally installed `llama3.1:8b`. You can change the model or host in a project-root `.env` file:
```
OLLAMA_MODEL=llama3.1:8b
OLLAMA_HOST=http://127.0.0.1:11434
```
No API key is required for the local Ollama server. Existing `GROQ_API_KEY` and `GROQ_MODEL` values are ignored.

### 4. Run the system

Check that `ollama list` shows `llama3.1:8b` and Ollama is running. The first LLM request may take longer while the model loads.

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

The extension lists nine shopping sites. Product selectors are tailored for Trendyol, Hepsiburada, Amazon Turkey, and Zara. The remaining sites use generic DOM selectors, so extraction depends on each page's current markup.

| Platform | Product extraction | Review data |
|---|---|---|
| Trendyol | Site-specific selectors | API request when available |
| Hepsiburada, Amazon Turkey, Zara | Site-specific selectors | DOM extraction when present |
| Mango, N11, Boyner, LCWaikiki, Koton | Generic DOM fallback | DOM extraction when present |

---

##  Verification

The Ollama integration has been checked with a simulated local chat server for the RAG agent, `/chat`, `/urun-analiz`, and a visual wardrobe suggestion. This checks the request format and application flow; it does not measure response quality or speed. A live check with the local `llama3.1:8b` model is still needed.

---

##  Technical Stack

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.12 (verified) | Backend language |
| FastAPI | Latest | REST API |
| Streamlit | Latest | Web UI |
| ChromaDB | 0.4.22 | Vector database (RAG + wardrobe) |
| sentence-transformers | 2.5.1 | CLIP + text embeddings |
| Ollama local API | Local server | LLM inference (default: Llama 3.1 8B) |
| Pillow | Latest | Image processing |
| Chrome Extension MV3 | — | Browser integration |

---

##  License

This project was developed as a graduation thesis. All rights reserved © 2026 Miray Balıkoğlu.
