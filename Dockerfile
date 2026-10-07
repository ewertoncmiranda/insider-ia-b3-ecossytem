# Servico de IA do ecossistema B3. Sem saida para a internet em execucao (SPEC 4.3);
# a configuracao chega por variavel de ambiente.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

RUN useradd --create-home --uid 10001 app
COPY --chown=app:app app ./app
COPY --chown=app:app skills ./skills
COPY --chown=app:app conhecimento ./conhecimento
USER app

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --retries=5 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/saude', timeout=4).status == 200 else 1)"
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
