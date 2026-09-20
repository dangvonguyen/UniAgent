FROM ghcr.io/uniagent-webis-de/uniagent-pyterrier-baseline:dev-0.0.1

RUN apt-get update \
    && apt-get install --yes --no-install-recommends poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip3 install --no-cache-dir --requirement /app/requirements.txt

ENV HF_HOME=/opt/huggingface

RUN python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"

ENV HF_HUB_OFFLINE=1
ENV TRANSFORMERS_OFFLINE=1

COPY german-stopwords.txt \
     event_logging.py \
     business_trip_tools.py \
     retrieval_tools.py \
     predict.py \
     dedup.py \
     hybrid_retrieval.py \
     offline_rule_retrieval.py \
     administrative_checks.json \
     /app/

RUN chmod +x /app/predict.py

ENTRYPOINT ["/app/predict.py"]