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
