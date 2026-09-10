FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --uid 10001 --create-home learner
COPY app/ ./app/
COPY web/ ./web/
COPY packs/ ./packs/
COPY references/ ./references/
COPY run.py ./
COPY deploy/entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh
EXPOSE 8080
ENTRYPOINT ["/entrypoint.sh"]
