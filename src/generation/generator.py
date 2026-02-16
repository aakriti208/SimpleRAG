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
        # Get LLM general knowledge to supplement Canvas materials
        llm_context_prompt = f"""As an educational AI, provide brief background context about: {question}
Keep it concise (2-3 sentences) and focus on foundational concepts that would help a student understand this topic."""
        llm_context = self.ask_llm(llm_context_prompt)

        # Format retrieved contexts
        if retrieved_contexts:
            kb_context = "\n\n".join([
                f"[Source {i+1} - {ctx['metadata'].get('title', 'Unknown')} - Similarity: {ctx['similarity']:.2f}]\n{ctx['text']}"
                for i, ctx in enumerate(retrieved_contexts)
            ])

            prompt = f"""You are an educational AI assistant. A student has asked a question, and I have retrieved relevant information from Canvas LMS course materials to help answer it.

CANVAS COURSE MATERIALS (Retrieved from Canvas API):
{kb_context}

YOUR GENERAL KNOWLEDGE:
{llm_context}

STUDENT'S QUESTION: {question}

INSTRUCTIONS:
- The Canvas materials contain tables with | (pipe) separators like this format:
  Week # | Day, Date | Topic | Reading | Notes
  7 | Thu, Mar 12 | Midterm | |
  This means: Week 7, on Thursday March 12, the topic is "Midterm"
- For date/schedule questions: Find the line containing the exact date, then read ALL columns in that row
- When you find the date row, report what appears in the "Topic" column (3rd position after the date)
- DO NOT hallucinate - only report what is explicitly in the retrieved text
- Quote the exact table row when reporting schedule information
- If you cannot find the specific date after thoroughly searching, clearly state that

Please search the Canvas materials for the exact information requested:"""
        else:
            kb_context = "No relevant context found in knowledge base"
            prompt = f"""You are an educational AI tutor. Answer this question using your general knowledge.

Question: {question}

Answer:"""

        answer = self.ask_llm(prompt)
        return answer, kb_context, llm_context
