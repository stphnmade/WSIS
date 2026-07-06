FROM node:20-slim AS web

WORKDIR /workspace/apps/web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web/ ./
RUN npm run build

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000

WORKDIR /workspace
COPY pyproject.toml README.md ./
COPY src/ src/
COPY apps/ apps/
COPY data/ data/
COPY --from=web /workspace/apps/web/dist/ apps/web/dist/
RUN pip install --no-cache-dir .

EXPOSE 10000
CMD ["sh", "-c", "uvicorn apps.api.main:app --host 0.0.0.0 --port ${PORT}"]
