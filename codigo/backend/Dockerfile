FROM python:3.12.14-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 APP_ENV=production
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./
COPY scripts/start_hosted.py ./scripts/start_hosted.py
RUN useradd --create-home websecai && chown -R websecai:websecai /app
USER websecai
CMD ["python", "scripts/start_hosted.py"]
