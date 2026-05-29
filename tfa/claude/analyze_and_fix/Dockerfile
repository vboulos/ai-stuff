FROM registry.access.redhat.com/ubi9/ubi-minimal:latest

# Install required packages
RUN microdnf install -y \
    python3 \
    python3-pip \
    curl \
    bash \
    shadow-utils \
    tar \
    gzip \
    && microdnf clean all

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Set working directory
WORKDIR /app

# Copy application files
COPY *.py /app/

# Expose Ollama port
EXPOSE 11434

# Create entrypoint script that starts Ollama in background
RUN echo '#!/bin/bash\n\
echo "Starting Ollama server..."\n\
ollama serve &\n\
OLLAMA_PID=$!\n\
echo "Ollama server started with PID $OLLAMA_PID"\n\
\n\
# Wait for Ollama to be ready\n\
echo "Waiting for Ollama to be ready..."\n\
for i in {1..30}; do\n\
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then\n\
        echo "Ollama is ready!"\n\
        break\n\
    fi\n\
    echo "Waiting... ($i/30)"\n\
    sleep 2\n\
done\n\
\n\
# Execute the command passed to the container\n\
exec "$@"' > /entrypoint.sh && chmod +x /entrypoint.sh

# Set environment variable for Ollama host
ENV OLLAMA_HOST=http://localhost:11434

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
