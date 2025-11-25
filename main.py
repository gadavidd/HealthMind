import json
import re
from pathlib import Path
from typing import List, Dict, Any

BASE_DIR = Path(__file__).resolve().parent
INDEX_PATH = BASE_DIR / "rag" / "index_simple.json"

# Carrega o índice simples (index_simples.json) na memória
if not INDEX_PATH.exists():
    raise FileNotFoundError(f"Índice não encontrado em {INDEX_PATH}. Rode primeiro: python rag/build_index_langchain.py")

with INDEX_PATH.open("r", encoding="utf-8") as f:
    INDEX_DATA: List[Dict[str, Any]] = json.load(f)

# Tokenização
def tokenize(text: str) -> List[str]:
    return [t for t in re.findall(r"\w+", text.lower(), flags=re.UNICODE) if len(t) > 2]

# Score para definir as palavras mais próximas da query que aparecem no chunck
def score_chunk(query_tokens: set[str], text: str) -> int:
    doc_tokens = set(tokenize(text))
    return sum(1 for t in query_tokens if t in doc_tokens)

# Retorna os k chuncks mais parecidos com a query usando a sobreposição de palavras (busca lexical simples)
def retrieve(query: str, k: int = 4) -> List[Dict[str, Any]]:
    q_tokens = set(tokenize(query))
    if not q_tokens:
        return []

    scored: List[tuple[int, Dict[str, Any]]] = []
    for entry in INDEX_DATA:
        s = score_chunk(q_tokens, entry["text"])
        if s > 0:
            scored.append((s, entry))

    if not scored:
        # fallback: devolve os primeiros k se nada casar
        return INDEX_DATA[:k]

    scored.sort(key=lambda x: x[0], reverse=True)
    top_entries = [e for _, e in scored[:k]]
    return top_entries


if __name__ == "__main__":
    q = "Quais são os sinais de alarme para dengue?"
    results = retrieve(q, k=3)
    for i, r in enumerate(results, start=1):
        meta = r.get("metadata", {})
        print(f"[{i}] {meta.get('source')} p.{meta.get('page')}")
        print(r["text"][:300], "\n---\n")
