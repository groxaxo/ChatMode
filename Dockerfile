FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

ENV CHROMA_DIR=/app/data/chroma \
    TTS_OUTPUT_DIR=/app/data/tts_out

EXPOSE 8000

CMD ["uvicorn", "chatmode.main:app", "--host", "0.0.0.0", "--port", "8000"]

