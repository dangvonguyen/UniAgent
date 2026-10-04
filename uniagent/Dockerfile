FROM python:3.13-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends --yes \
        default-jdk-headless \
        poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir --requirement /app/requirements.txt

# Download the Terrier jars at build time; the TIRA sandbox has no network access.
ENV PYTERRIER_HOME=/opt/pyterrier
RUN python3 -c "import pyterrier as pt; pt.java.init()" \
    && chmod -R a+rX /opt/pyterrier
ENV PYTERRIER_OFFLINE=1

COPY resources /app/resources
COPY src /app/src
COPY predict.py /app/
RUN chmod +x /app/predict.py

ENTRYPOINT ["/app/predict.py"]
