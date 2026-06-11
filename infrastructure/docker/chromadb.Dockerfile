FROM chromadb/chroma:latest

# Custom initialization settings can go here if needed
ENV IS_PERSISTENT=TRUE
ENV ANONYMIZED_TELEMETRY=FALSE
