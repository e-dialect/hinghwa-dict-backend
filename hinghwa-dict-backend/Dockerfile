FROM python:3.10-bookworm

WORKDIR /usr/src/HinghwaDict-backend

ARG SEMANTIC_SEARCH_MODEL_NAME=BAAI/bge-small-zh-v1.5
ARG SEMANTIC_SEARCH_MODEL_REVISION=7999e1d3359715c523056ef9478215996d62a620
ENV HF_HOME=/opt/huggingface

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

# Fetch the pinned model while the image is built so production queries never
# depend on outbound Hugging Face access.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('${SEMANTIC_SEARCH_MODEL_NAME}', revision='${SEMANTIC_SEARCH_MODEL_REVISION}', cache_folder='${HF_HOME}', trust_remote_code=False)"
ENV HF_HUB_OFFLINE=1

# Copy application code
COPY . .

# Collect static files
RUN echo "yes" | python manage.py collectstatic

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000", "--insecure"]
