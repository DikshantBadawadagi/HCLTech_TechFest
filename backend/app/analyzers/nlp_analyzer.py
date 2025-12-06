from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def analyze_transcript(text: str):
    embedding = model.encode(text).tolist()
    return {
        "concept_embedding": embedding
    }
