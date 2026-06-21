# ==========================================
# STAGE 1: BUILDER
# ==========================================
FROM python:3.12-slim as builder

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Cài đặt C++ Compiler để biên dịch thư viện (psycopg2)
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Đóng gói toàn bộ thư viện Python thành file .whl (Bỏ lại các file rác)
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# ==========================================
# STAGE 2: RUNTIME
# ==========================================
FROM python:3.12-slim

WORKDIR /app

# Chỉ cài đặt thư viện chạy (runtime), không cài gcc để tối ưu 60% dung lượng
RUN apt-get update && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*

# (Security) Tạo user thường để chạy app, tránh dùng root
RUN adduser --disabled-password --gecos '' glpo_user

# Copy thư viện đã đóng gói từ Stage 1 sang
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# Cài đặt từ file wheel nội bộ cực nhanh
RUN pip install --no-cache-dir --find-links=/wheels -r requirements.txt

# Copy mã nguồn
COPY . .

# Giao quyền sở hữu thư mục cho glpo_user
RUN chown -R glpo_user:glpo_user /app

# Đổi sang user thường
USER glpo_user

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
