FROM python:3.11-slim

WORKDIR /app

# 只安装最基础的依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libmagic1 \
        && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]