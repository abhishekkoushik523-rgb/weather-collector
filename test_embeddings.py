from sentence_transformers import SentenceTransformer

print("Loading model...")

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

print("Model loaded successfully!")

sentences = [
    "Heavy rain reported in Whitefield, Bengaluru",
    "Whitefield is experiencing heavy rainfall"
]

embeddings = model.encode(sentences)

print("Number of sentences:", len(embeddings))
print("Embedding shape:", embeddings.shape)