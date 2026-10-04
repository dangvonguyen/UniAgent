#!/usr/bin/sh

export inputDataset=../data/datasets/business-trip-spot-check/inputs
export outputDir=./runs

# LLM endpoint settings (OPENAI_BASE_URL, OPENAI_API_KEY, OPENAI_MODEL) come from .env
set -a
. ./.env
set +a

export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64

python3 predict.py \
  --input $inputDataset \
  --output $outputDir \
  --max-tokens 4000
