import os
import json
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Caminhos para os docs de RAG
DATA_DIR = "rag/docs"
OUT_FILE = "rag/index_simple.json"

def load_pdfs():
    documents = []
    total_pages = 0

    for file in os.listdir(DATA_DIR):
        if file.endswith(".pdf"):
            path = os.path.join(DATA_DIR, file)
            print(f"Carregando: {file}")
            loader = PyPDFLoader(path)
            pages = loader.load()
            total_pages += len(pages)
            documents.extend(pages)

    print(f"Total de páginas carregadas: {total_pages}")
    return documents

def chunk_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200
    )
    chunks = splitter.split_documents(docs)
    print(f"Total de chunks gerados: {len(chunks)}")
    return chunks


def save_index(chunks):
    index_data = [
        {"text": c.page_content, "metadata": c.metadata}
        for c in chunks
    ]

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

    print(f"Índice salvo em: {OUT_FILE}")


def main():
    docs = load_pdfs()
    chunks = chunk_documents(docs)
    save_index(chunks)


if __name__ == "__main__":
    main()
