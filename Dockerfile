# ---- Build stage ----
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Production stage ----
FROM python:3.11-slim

LABEL maintainer="NAS Homepage"
LABEL description="NAS智能主页 - 自动发现Lucky+Docker服务"

WORKDIR /app

# 安装后端依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./

# 复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# 数据目录
RUN mkdir -p /app/data

# 环境变量默认值
ENV HOST=0.0.0.0
ENV PORT=8000
ENV DATA_DIR=/app/data
ENV LUCKY_ENABLED=true
ENV DOCKER_ENABLED=true
ENV AUTO_DISCOVERY_INTERVAL=300
ENV THEME_DEFAULT=dark

EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
