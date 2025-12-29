# 👗 AI Personal Fashion Stylist Agent

## 📖 Project Overview

This project is an intelligent **AI Agent** designed to act as a Personal Fashion Stylist. It leverages the **ReAct (Reasoning + Acting)** architecture to understand user needs, retrieve styling rules from a Knowledge Base (**RAG**), and search for actual products in a real-world inventory.

The agent is powered by **Llama-3-70b (via Groq API)** and utilizes **ChromaDB** for vector semantic search.

### 🚀 Key Features

* **🧠 Multi-Hop Reasoning:** The agent can break down complex queries (e.g., *"Find an outfit for a Pear body shape"*). It first researches styling rules and then searches for matching products.
* **🌍 Cross-Lingual Support:** Capable of understanding queries in **Turkish**, translating the intent to English for database search, and responding back in Turkish.
* **🛍️ Real-World Inventory:** Integrated with a subset of the Kaggle Fashion Product Images Dataset (44k+ items) for realistic product recommendations.
* **📚 RAG (Retrieval-Augmented Generation):** Uses semantic search to retrieve fashion theory (Color Analysis, Body Types, Fabric Guide) from text documents.

---

## 🛠️ Technical Architecture

* **LLM:** Llama-3.3-70b-versatile (Groq API)
* **Vector Database:** ChromaDB
* **Embedding Model:** sentence-transformers/all-MiniLM-L6-v2
* **Data Processing:** Pandas, NumPy
* **Framework:** Custom Python Agent (ReAct Loop: Thought $\to$ Action $\to$ Observation)

---

## 📂 Repository Structure

* `Agent.ipynb`: The main Jupyter Notebook containing the agent logic, tools, and test suite.
* `dataset/`: Contains the Knowledge Base text files and the product inventory sample:
    * `body_type_guide.txt`, `color_theory_analysis.txt`, etc.
    * `styles_sample.csv` (Product Inventory)
* `requirements.txt`: List of dependencies required to run the project.

---

## 📊 Benchmark & Stress Testing

The agent was subjected to a comprehensive stress test comprising **11 scenarios** with varying difficulty levels. It achieved a **100% Success Rate**.

| Scenario | Difficulty | Status | Score |
| :--- | :--- | :---: | :---: |
| **Turkish Language Query (Cross-Lingual)** | Hard | ✅ | 100/100 |
| Pear Shape + Summer Outfit (Multi-Hop) | Hard | ✅ | 100/100 |
| Apple Shape + Formal Wear | Hard | ✅ | 100/100 |
| Winter Fabric Recommendation | Hard | ✅ | 100/100 |
| Specific Item Search (Red Dress) | Medium | ✅ | 100/100 |
| Category Search (Heels) | Medium | ✅ | 100/100 |
| Usage Search (Casual) | Medium | ✅ | 100/100 |
| Color Theory (Cool Undertones) | Medium | ✅ | 100/100 |
| Styling Don'ts (Inverted Triangle) | Medium | ✅ | 100/100 |
| Unit Conversion (Calculator) | Easy | ✅ | 100/100 |
| Budget Calculation | Easy | ✅ | 100/100 |

---

## ⚙️ Installation & Usage

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/Miray243/Fashion-Stylist-Al-Agent.git](https://github.com/Miray243/Fashion-Stylist-Al-Agent.git)
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up API Key:**
    * Get your free API Key from [Groq Console](https://console.groq.com/).
    * Add it to your environment variables or Colab Secrets as `GROQ_API_KEY`.

4.  **Run the Agent:**
    Open `Agent.ipynb` and run all cells. You can query the agent using the `query()` function:
    ```python
    query("I have a Pear body shape. Find me a suitable outfit for Summer.")
    ```

---

## ⚠️ Data Disclaimer
The `styles_sample.csv` included in the `dataset` folder is a **subset (sample)** of the original [Fashion Product Images Dataset](https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-dataset) on Kaggle. It is provided for demonstration purposes to ensure the code runs immediately.

---

**Developed by:** Miray
