import os
import pandas as pd
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain.docstore.document import Document
from langchain.chains import RetrievalQA


df = pd.read_csv(os.path.join(os.path.dirname(__file__), "medicines.csv"))


docs = []
for _, row in df.iterrows():
    text = f"""
    Symptom: {row['Symptom']}
    Medicine: {row['Medicine']}
    Description: {row['Description']}
    Alternatives: {row['Alternatives']}
    """
    docs.append(Document(page_content=text))

embeddings = OllamaEmbeddings(model="mistral")
vectordb = Chroma.from_documents(docs, embeddings)

llm = Ollama(model="mistral")
qa = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectordb.as_retriever(search_kwargs={"k": 3})
)

def ask_agent(query):
    return qa.run(query)
