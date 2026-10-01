import chromadb
from chromadb.utils import embedding_functions
import glob
import uuid
import json
from user_profile import get_profile, update_profile_from_text, profile_to_context
from llm import chat

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

known_actions = {"calculator": calculator, "search_knowledge_base": search_knowledge_base}

native_tools = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Find relevant styling rules and fashion theory.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Calculate a mathematical expression.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
            },
        },
    },
]

def query_with_native_tools(prompt: str, max_turns: int) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert personal stylist. For styling questions, search the "
                "knowledge base before answering. Use the provided tools when useful. "
                "Answer in the user's language without exposing tool calls or reasoning."
            ),
        },
        {"role": "user", "content": prompt},
    ]
    for _ in range(max_turns):
        result = chat(
            messages, tools=native_tools, temperature=0, max_tokens=1024
        )
        reply = result["message"]
        tool_calls = reply.get("tool_calls") or []
        if not tool_calls:
            content = (reply.get("content") or "").strip()
            if not content or result.get("done_reason") == "length":
                raise RuntimeError("Ollama boş veya kesilmiş agent yanıtı döndürdü.")
            return content

        messages.append({
            "role": "assistant",
            "content": reply.get("content") or "",
            "tool_calls": tool_calls,
        })
        for call in tool_calls:
            function = call.get("function") or {}
            name = function.get("name", "")
            try:
                arguments = function.get("arguments") or {}
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
                argument = arguments.get(
                    "query" if name == "search_knowledge_base" else "expression"
                )
                if name not in known_actions or not isinstance(argument, str):
                    observation = "Tool not found or invalid arguments."
                else:
                    observation = known_actions[name](argument)
            except (ValueError, TypeError, AttributeError):
                observation = "Invalid tool arguments."
            messages.append({
                "role": "tool",
                "tool_name": name,
                "content": str(observation),
            })

    return "Maksimum adım sayısına ulaşıldı."


def query(question: str, max_turns: int = 5) -> str:
    update_profile_from_text(question)
    profile_context = profile_to_context(get_profile())
    prompt = f"{profile_context}\n\nQuestion: {question}" if profile_context else question
    return query_with_native_tools(prompt, max_turns)
