FROM python:3.13-slim

ARG FASTAPI_PORT

RUN pip install uv

WORKDIR /src

COPY . /src

RUN uv sync --locked

RUN echo ${FASTAPI_HOST}:${FASTAPI_PORT}

CMD uv run hypercorn src.main:fastapi_app --bind "0.0.0.0:${FASTAPI_PORT}"