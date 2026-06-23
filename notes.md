FUTURE ENHANCEMENT — Policy Caching with Embeddings
-----------------------------------------------------
Problem: Re-sending full policy text with every request is inefficient.
- Hits rate limits on free tier APIs
- Increases latency and token cost at scale

Solution: RAG (Retrieval Augmented Generation)
- Convert policy documents into vector embeddings once
- Store in a vector database (e.g. Pinecone, Google Vertex AI Vector Search)
- On each query, retrieve only the relevant policy chunks
- Send smaller, targeted context to the model

Benefits:
- Reduces token usage by ~70-80%
- Faster responses
- Scales to thousands of policy documents
- Standard enterprise pattern for knowledge bases

Tools: LangChain, Vertex AI Embeddings, Pinecone

BENCHMARK FINDINGS — Claude Evaluation
---------------------------------------
Date: [today's date]
Model: claude-haiku-4-5-20251001
Tests: 8 (3 Straightforward, 3 Boundary, 2 Ambiguous)

Results:
- Valid JSON:        8/8  (100%)
- Policy area:       8/8  (100%)
- Answer accuracy:   7/7  (100%, excl. ambiguous)
- Boundary/hallucination check: 3/3 (100%)
- Avg latency:       2.27s

Key finding 1: Zero hallucination on boundary cases.
Model correctly answered "no" and cited exact policy limits
every time it was asked a question with a constrained answer.

Key finding 2: Appropriate confidence on ambiguous questions.
When policy didn't cover a topic, model returned medium confidence
rather than fabricating a policy. Critical for HR trust.

Key finding 3: 100% JSON schema compliance across all tests.
Every response was parseable and contained all required fields.
Production-ready output reliability.

Gemini comparison: Blocked by free tier rate limits.
Resolution: Enable billing on Google AI Studio or use Vertex AI
in a Google Cloud project for production deployment.