FROM python:3.10-bookworm

WORKDIR /usr/src/HinghwaDict-backend

ARG SEMANTIC_SEARCH_MODEL_NAME=BAAI/bge-small-zh-v1.5
ARG SEMANTIC_SEARCH_MODEL_REVISION=7999e1d3359715c523056ef9478215996d62a620
ARG PRELOAD_SEMANTIC_MODEL=false
ENV HF_HOME=/opt/huggingface
ENV HF_HUB_OFFLINE=1

# Update apt sources to use Huawei Cloud mirror
RUN sed -i 's@deb.debian.org@repo.huaweicloud.com@g' /etc/apt/sources.list.d/debian.sources

# Install system dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Avoid failing the Docker build on rate-limited or unavailable Hugging Face
# networks. The semantic model is loaded lazily at runtime unless an explicit
# opt-in build argument is provided.
RUN if [ "$PRELOAD_SEMANTIC_MODEL" = "true" ]; then \
        python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('${SEMANTIC_SEARCH_MODEL_NAME}', revision='${SEMANTIC_SEARCH_MODEL_REVISION}', cache_folder='${HF_HOME}', trust_remote_code=False, local_files_only=False)"; \
    fi

# Copy application code
COPY . .

# Collect static files
RUN echo "yes" | python manage.py collectstatic

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000", "--insecure"]
