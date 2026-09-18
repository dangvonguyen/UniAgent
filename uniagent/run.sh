#!/usr/bin/sh

export inputDataset=../data/datasets/business-trip-spot-check/inputs
export outputDir=./runs

export OPENAI_BASE_URL=http://localhost:8000/v1
export OPENAI_API_KEY=dummy
export OPENAI_MODEL=Qwen/Qwen3-4B-Instruct-2507-FP8

export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64

python3 predict.py \
  --input $inputDataset \
  --output $outputDir \
  --max-tokens 4000
