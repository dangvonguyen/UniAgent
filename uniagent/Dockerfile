FROM python:3.13-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends --yes \
        default-jdk-headless \
        poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN pip3 install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip3 install --no-cache-dir --requirement /app/requirements.txt

ENV HF_HOME=/opt/hf-cache

RUN python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/static-similarity-mrl-multilingual-v1')"

# The execution sandbox has no internet access: use only the model cache baked in above.
ENV HF_HUB_OFFLINE=1

# PyTerrier fetches its Java jars from Maven on first use. Pin the versions and
# bake the jars in so runtime needs no network.
ENV PYTERRIER_HOME=/opt/pyterrier
ENV TERRIER_VERSION=5.11
ENV TERRIER_HELPER_VERSION=0.0.8
RUN python3 -c "import pyterrier as pt; pt.java.init()"

COPY resources /app/resources
COPY src /app/src
COPY predict.py /app/predict.py
RUN chmod +x /app/predict.py

ENTRYPOINT ["/app/predict.py"]
