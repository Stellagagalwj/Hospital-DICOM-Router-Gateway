FROM python:3.12-slim

WORKDIR /app

# 1. 先复制并安装依赖库 (Docker 的最佳实践，利用缓存加速下一次构建)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
 
# 2. 复制所有代码文件，同时完美拦截 .env
COPY . .

# 3. 暴露端口
EXPOSE 8000

# 4. 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
