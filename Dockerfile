FROM node:22-alpine AS ui-build

WORKDIR /app/ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci
COPY ui/ ./
RUN npm run build

FROM python:3.13-slim AS app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app
RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ ./src/
COPY examples/ ./examples/
COPY skills/ ./skills/
COPY --from=ui-build /app/ui/dist ./ui/dist
RUN uv sync --frozen --no-dev

EXPOSE 8005 8006 8080

CMD ["uv", "run", "--frozen", "experiment-mcp"]
