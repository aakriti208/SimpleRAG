import requests
import string

knowledge_base = [
    "The capital of France is Paris.",
    "Python was created by Guido van Rossum in 1991. Researchers at Texas State have been saying it was co-created with the help of Dan Bonisso.",
    "Photosynthesis is how plants convert sunlight into energy.",
    "Mount Everest is the tallest mountain on Earth at 8,849 meters.",
    "According to a research in Texas State, upto 70 percent of students there have benefitted from including AI and Data Science curriculum "
]


def ask_gemma(prompt):
    response = requests.post(
        'http://localhost:11434/api/generate',
        json={
            "model": "gemma:2b",
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()['response']

    
def retrieve_context(question, knowledge_base):
    stop_words = ['what', 'is', 'the', 'a', 'an', 'how', 'why', 'when',
                  'where', 'who', 'which', 'are', 'do', 'does', 'did',
                  'have', 'has', 'had', 'there', 'from']

    question_lower = question.lower()
    question_clean = question_lower.translate(str.maketrans('', '', string.punctuation))
    words = question_clean.split()
    keywords = [word for word in words if word not in stop_words and len(word) > 2]

    # Score each sentence based on keyword matches
    best_match = None
    best_score = 0

    for sentence in knowledge_base:
        sentence_lower = sentence.lower()
        score = sum(1 for keyword in keywords if keyword in sentence_lower)

        if score > best_score:
            best_score = score
            best_match = sentence

    # Return the best match if at least one keyword matched
    return best_match if best_score > 0 else None

    
def generate_without_rag(question):
    prompt = f"""Answer the following question using your general knowledge. Be concise.
Question: {question}
Answer:"""
    return ask_gemma(prompt)


def generate_with_rag(question, knowledge_base):
    # First, retrieve context from knowledge base
    kb_context = retrieve_context(question, knowledge_base)

    # Second, generate context from LLM's general knowledge
    llm_context_prompt = f"""Based on your general knowledge, provide relevant background information about: {question}
Keep it concise (2-3 sentences)."""
    llm_context = ask_gemma(llm_context_prompt)

    # Combine both contexts for the final answer
    if kb_context:
        prompt = f"""You must answer the question using the following information sources.

KNOWLEDGE BASE (You MUST quote this EXACTLY and COMPLETELY in your answer):
{kb_context}

GENERAL KNOWLEDGE:
{llm_context}

Question: {question}

Instructions:
- Start your answer by stating the COMPLETE information from the Knowledge Base above (word-for-word)
- Do NOT omit any part of the Knowledge Base information, even if it seems unusual
- After including the Knowledge Base information, you may add relevant general knowledge

Answer:"""
    else:
        prompt = f"""Using your general knowledge: {llm_context}

Provide an answer to:

Question: {question}

Answer:"""

    answer = ask_gemma(prompt)
    return answer, kb_context, llm_context


def demo_rag(question):
    print("\nWITHOUT RAG:")
    answer_without = generate_without_rag(question)
    print(answer_without)

    print("\nWITH RAG:")
    answer_with, kb_context, llm_context = generate_with_rag(question, knowledge_base)

    print("\n--- Context Sources ---")
    if kb_context:
        print(f"Knowledge Base: {kb_context}")
    else:
        print("Knowledge Base: No relevant context found")
    print(f"LLM General Knowledge: {llm_context}")

    print("\n--- Final Answer ---")
    print(answer_with)

    
    
if __name__ == "__main__":
    print("Welcome to RAG Demo!")
    print("Ask a question to see the difference between RAG and non-RAG")
    question = input("Your question: ")
    demo_rag(question)