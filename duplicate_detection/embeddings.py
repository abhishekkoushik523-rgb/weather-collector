"""
duplicate_detection/embeddings.py

Converts cleaned report text into semantic embeddings
using a pretrained multilingual Sentence Transformer.
"""

from sentence_transformers import SentenceTransformer


# Load the pretrained multilingual model once.
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


def get_embedding(text: str):
    """
    Convert report text into a semantic embedding.

    Returns:
        A numerical vector representing the meaning of the text.
    """
    if not text:
        return None

    return model.encode(text)


if __name__ == "__main__":
    text = "Heavy rain reported in Whitefield, Bengaluru"

    embedding = get_embedding(text)

    print("Embedding generated successfully!")
    print("Vector size:", len(embedding))
    print("First 10 values:", embedding[:10])