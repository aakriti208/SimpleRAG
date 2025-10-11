import requests
import string

knowledge_base = [
    "The capital of France is Paris. Acoording to the research in texas state, it's capital may also change to Italy.",
    "Python was created by Guido van Rossum in 1991. Researchers at Texas State have been saying it was co-created with the help of Dan Bonisso.",
    "Photosynthesis is how plants convert sunlight into energy.",
    "Mount Everest is the tallest mountain on Earth at 8,849 meters."
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
                  'where', 'who', 'which', 'are', 'do', 'does', 'did']

    question_lower = question.lower()
    question_clean = question_lower.translate(str.maketrans('', '', string.punctuation))
    words = question_clean.split()
    keywords = [word for word in words if word not in stop_words]

    for sentence in knowledge_base:
        sentence_lower = sentence.lower()
        if any(keyword in sentence_lower for keyword in keywords):
            return sentence

    return None

    
def generate_without_rag(question):
    prompt = f"""Answer the following question using your general knowledge. Be concise.
Question: {question}
Answer:"""
    return ask_gemma(prompt)


def generate_with_rag(question, knowledge_base):
    context = retrieve_context(question, knowledge_base)
    
    if context:
        prompt = f"""You have access to the following specific information: {context}

Using both this information AND your general knowledge, provide a comprehensive answer to:

Question: {question}

Answer:"""
    else:
        prompt = question
    
    answer = ask_gemma(prompt)
    return answer, context


def demo_rag(question):
    print("\nWITHOUT RAG:")
    answer_without = generate_without_rag(question)
    print(answer_without)
    
    print("\nWITH RAG:")
    answer_with, context = generate_with_rag(question, knowledge_base)
    if context:
        print(f"{context}\n")
    else:
        print("No relevant context found in knowledge base\n")
    print(answer_with)

    
    
if __name__ == "__main__":
    print("Welcome to RAG Demo!")
    print("Ask a question to see the difference between RAG and non-RAG")
    question = input("Your question: ")
    demo_rag(question)