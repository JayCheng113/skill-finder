FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    starlette uvicorn \
    faiss-cpu numpy \
    sentence-transformers \
    huggingface-hub

COPY serve.py .

EXPOSE 7860

CMD ["python", "serve.py"]
