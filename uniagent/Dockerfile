FROM python:3.13-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends --yes \
        default-jdk-headless \
        poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir --requirement /app/requirements.txt

COPY resources src predict.py /app/
RUN chmod +x /app/predict.py

ENTRYPOINT ["/app/predict.py"]
