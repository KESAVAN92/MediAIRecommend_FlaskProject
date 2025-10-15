import os
import pandas as pd
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain.docstore.document import Document
from langchain.chains import RetrievalQA

# Load dataset
df = pd.read_csv(os.path.join(os.path.dirname(__file__), "medicines.csv"))

# Convert rows to Documents
docs = []
for _, row in df.iterrows():
    text = f"""
    Medicine: {row['Medicine_Name']} {row['Strength']}
    Use Case: {row['Use_Case']}
    Alternative: {row['Alternative']}
    Stock: {row['Stock']}
    Dosage: {row['Dosage_Instruction']}
    """
    docs.append(Document(page_content=text))

# Embeddings + Vector DB
embeddings = OllamaEmbeddings(model="mistral")
vectordb = Chroma.from_documents(docs, embeddings)

# RetrievalQA chain
llm = Ollama(model="mistral")
qa = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectordb.as_retriever(search_kwargs={"k": 3})
)

def ask_agent(query):
    return qa.run(query)
