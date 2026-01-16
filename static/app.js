// DOM elements
const form = document.getElementById('question-form');
const questionInput = document.getElementById('question-input');
const topKInput = document.getElementById('top-k');
const submitBtn = document.getElementById('submit-btn');
const loading = document.getElementById('loading');
const error = document.getElementById('error');
const results = document.getElementById('results');
const answerWithRag = document.getElementById('answer-with-rag');
const answerWithoutRag = document.getElementById('answer-without-rag');
const contextsContainer = document.getElementById('contexts-container');
const kbContext = document.getElementById('kb-context');
const llmContext = document.getElementById('llm-context');

// Form submission handler
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const question = questionInput.value.trim();
    const topK = parseInt(topKInput.value);

    if (!question) return;

    // UI state: loading
    setLoadingState(true);
    hideError();
    hideResults();

    try {
        const response = await fetch('/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: question,
                top_k: topK
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to get response');
        }

        const data = await response.json();
        displayResults(data);

    } catch (err) {
        showError(err.message);
    } finally {
        setLoadingState(false);
    }
});

function setLoadingState(isLoading) {
    submitBtn.disabled = isLoading;
    submitBtn.textContent = isLoading ? 'Processing...' : 'Ask Question';
    loading.classList.toggle('hidden', !isLoading);
}

function showError(message) {
    error.textContent = `Error: ${message}`;
    error.classList.remove('hidden');
}

function hideError() {
    error.classList.add('hidden');
}

function hideResults() {
    results.classList.add('hidden');
}

function displayResults(data) {
    // Display both answers for comparison
    answerWithRag.textContent = data.answer_with_rag;
    answerWithoutRag.textContent = data.answer_without_rag;

    // Display contexts
    contextsContainer.innerHTML = '';

    if (data.contexts && data.contexts.length > 0) {
        data.contexts.forEach((ctx, index) => {
            const contextCard = createContextCard(ctx, index + 1);
            contextsContainer.appendChild(contextCard);
        });
    } else {
        contextsContainer.innerHTML = '<p style="color: var(--text-secondary);">No contexts retrieved</p>';
    }

    // Display additional info
    kbContext.textContent = data.kb_context;
    llmContext.textContent = data.llm_context;

    // Show results
    results.classList.remove('hidden');

    // Smooth scroll to results
    results.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function createContextCard(ctx, index) {
    const card = document.createElement('div');
    card.className = 'context-card';

    const similarityPercent = (ctx.similarity * 100).toFixed(1);

    card.innerHTML = `
        <div class="context-header">
            <span class="context-title">${index}. ${escapeHtml(ctx.title)}</span>
            <span class="similarity-badge">${similarityPercent}% match</span>
        </div>
        <div class="context-source">Source: ${escapeHtml(ctx.source)}</div>
        <div class="context-text">${escapeHtml(ctx.text)}</div>
    `;

    return card;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
