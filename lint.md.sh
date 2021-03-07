#!/bin/bash

docker run --rm \
    -v "$(pwd):/code" \
    avtodev/markdown-lint:v1 \
    --config /code/.github/lint/config.json /code/**/*.md