import os
from dotenv import load_dotenv
from groq import Groq
import chromadb
from chromadb.utils import embedding_functions
import glob
import uuid
import re
from user_profile import get_profile, update_profile_from_text, profile_to_context

load_dotenv()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

chroma_client = chromadb.Client()
emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

try:
    chroma_client.delete_collection(name="fashion_knowledge")
except:
    pass

collection = chroma_client.create_collection(
    name="fashion_knowledge",
    embedding_function=emb_fn
)

def load_knowledge_base():
    txt_files = glob.glob("dataset/*.txt")
    documents, ids, metadatas = [], [], []

    for f_name in txt_files:
        try:
            with open(f_name, "r", encoding="utf-8") as f:
                content = f.read()
                chunks = [c.strip() for c in content.split('\n\n') if len(c.strip()) > 50]
                for chunk in chunks:
                    documents.append(chunk)
                    ids.append(str(uuid.uuid4()))
                    metadatas.append({"source": f_name})
        except Exception as e:
            print(f"Dosya okuma hatası {f_name}: {e}")

    if documents:
        collection.add(documents=documents, ids=ids, metadatas=metadatas)
        print(f"✅ {len(documents)} chunk yüklendi.")

load_knowledge_base()

def calculator(expression: str) -> str:
    """Calculates mathematical expressions."""
    try:
        allowed_chars = set("0123456789+-*/(). ")
        if not all(c in allowed_chars for c in expression):
            return "Error: Invalid characters."
        return str(eval(expression))
    except Exception as e:
        return f"Error: {e}"

def search_knowledge_base(query: str) -> str:
    """Use this tool to find stylistic rules, fabric details, and fashion theory."""
    try:
        results = collection.query(query_texts=[query], n_results=3)
        if not results['documents'] or not results['documents'][0]:
            return "Veritabanında bilgi bulunamadı."
        output = "📚 Bulunanlar:\n"
        for i, text in enumerate(results['documents'][0]):
            output += f"---\n{text}\n"
        return output
    except Exception as e:
        return f"Veritabanı hatası: {e}"

system_prompt = """
You are an expert Personal Stylist.
You MUST run in a loop of Thought, Action, PAUSE, Observation.
At the end output an Answer.

STRICT RULES:
- ALWAYS think and act in ENGLISH only.
- ALWAYS use exact format below. Never deviate.
- If user writes in Turkish, still think in English. Only the final Answer can be in Turkish.

EXACT FORMAT YOU MUST USE:
Thought: [your reasoning in English]
Action: search_knowledge_base: [search query in English]
PAUSE

After Observation, continue:
Thought: [reasoning]
Answer: [final answer - can be in Turkish if user asked in Turkish]

Available actions:
- search_knowledge_base: Search for styling rules and fashion theory
- calculator: Calculate mathematical expressions

Example:
Question: What fits a Pear body shape?
Thought: I need to find styling rules for Pear body shape.
Action: search_knowledge_base: Pear body shape styling rules
PAUSE
Observation: A-line skirts work well...
Thought: I have enough info to answer.
Answer: For a Pear shape, A-line skirts work best...
""".strip()

class Agent:
    def __init__(self, system=""):
        self.system = system
        self.messages = []
        if self.system:
            self.messages.append({"role": "system", "content": system})

    def __call__(self, message):
        self.messages.append({"role": "user", "content": message})
        result = self.execute()
        self.messages.append({"role": "assistant", "content": result})
        return result

    def execute(self):
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=self.messages,
            temperature=0,
            stop=["PAUSE", "Gözlem:", "Observation:"]
        )
        return completion.choices[0].message.content

action_re = re.compile(r'^(?:Action|Eylem|Aksiyon): (\w+): (.*)$')
known_actions = {"calculator": calculator, "search_knowledge_base": search_knowledge_base}

def query(question: str, max_turns: int = 5) -> str:
    # Metinden profil bilgisi çıkar ve kaydet
    update_profile_from_text(question)
    
    # Profili context olarak al
    profile = get_profile()
    profile_context = profile_to_context(profile)
    
    # Profil varsa soruya ekle
    if profile_context:
        next_prompt = f"{profile_context}\n\nQuestion: {question}"
    else:
        next_prompt = question
    
    bot = Agent(system_prompt)

    for i in range(max_turns):
        result = bot(next_prompt)
        actions = [action_re.match(a) for a in result.split('\n') if action_re.match(a)]

        if actions:
            action, action_input = actions[0].groups()
            if action in known_actions:
                observation = known_actions[action](action_input)
                next_prompt = f"Observation: {observation}"
            else:
                next_prompt = "Observation: Tool not found."
        else:
            if "Answer:" in result or "Cevap:" in result:
                if "Answer:" in result:
                    return result.split("Answer:")[-1].strip()
                return result.split("Cevap:")[-1].strip()
            lines = [l for l in result.split('\n') 
                    if not l.startswith("Thought:") 
                    and not l.startswith("Action:")
                    and not l.startswith("PAUSE")
                    and l.strip()]
            answer = "\n".join(lines).strip()
            return answer if answer else result.strip()

    return "Maksimum adım sayısına ulaşıldı."