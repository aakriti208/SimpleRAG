import requests
from typing import List, Dict, Tuple
from src.config import OLLAMA_BASE_URL, OLLAMA_MODEL


class Generator:
    """Handles LLM answer generation."""

    def __init__(self, model: str = OLLAMA_MODEL, base_url: str = OLLAMA_BASE_URL):
        self.model = model
        self.base_url = base_url

    def ask_llm(self, prompt: str) -> str:
        """Send prompt to Ollama and get response."""
        response = requests.post(
            f'{self.base_url}/api/generate',
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
        )
        response.raise_for_status()
        return response.json()['response']

    def generate_without_rag(self, question: str) -> str:
        """Generate answer without RAG."""
        prompt = f"""Answer the following question using your general knowledge. Be concise.
Question: {question}
Answer:"""
        return self.ask_llm(prompt)

    def generate_with_rag(self, question: str, retrieved_contexts: List[Dict]) -> Tuple[str, str, str]:
        """
        Generate answer with RAG using retrieved contexts.

        Returns: (answer, formatted_kb_context, llm_context)
        """
        # Get LLM general knowledge
        llm_context_prompt = f"""Based on your general knowledge, provide relevant background information about: {question}
Keep it concise (2-3 sentences)."""
        llm_context = self.ask_llm(llm_context_prompt)

        # Format retrieved contexts
        if retrieved_contexts:
            kb_context = "\n\n".join([
                f"[Source {i+1} - {ctx['metadata'].get('title', 'Unknown')} - Similarity: {ctx['similarity']:.2f}]\n{ctx['text']}"
                for i, ctx in enumerate(retrieved_contexts)
            ])

            prompt = f"""You must answer the question using the following information sources.

KNOWLEDGE BASE (You MUST quote this EXACTLY and COMPLETELY in your answer):
{kb_context}

GENERAL KNOWLEDGE:
{llm_context}

Question: {question}

# Instructions:
# - Start your answer by stating the COMPLETE information from the Knowledge Base above (word-for-word)
# - Do NOT omit any part of the Knowledge Base information, even if it seems unusual
# - After including the Knowledge Base information, you may add relevant general knowledge

Provide a detailed answer that:
1. Uses the verified information as the foundation
2. Enhances it with relevant context from your knowledge
3. Explains concepts clearly for educational purposes

# Answer:"""
        else:
            kb_context = "No relevant context found in knowledge base"
            prompt = f"""You are an educational AI tutor. Answer this question using your general knowledge.

Question: {question}

Answer:"""

        answer = self.ask_llm(prompt)
        return answer, kb_context, llm_context
