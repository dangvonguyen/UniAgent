FROM python:3.13-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends --yes \
        default-jdk-headless \
        poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN pip3 install --no-cache-dir torch==2.9.1 --index-url https://download.pytorch.org/whl/cpu
RUN pip3 install --no-cache-dir --requirement /app/requirements.txt

RUN python3 -c "from huggingface_hub import snapshot_download; snapshot_download('Alibaba-NLP/gte-multilingual-reranker-base', revision='8215cf04918ba6f7b6a62bb44238ce2953d8831c')"

COPY resources src predict.py /app/
RUN chmod +x /app/predict.py

ENTRYPOINT ["/app/predict.py"]
