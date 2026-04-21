# Stage 1: Build C++ Binary
FROM gcc:latest AS cpp-builder
COPY priority_engine.cpp .
RUN g++ -std=c++17 -O2 -o priority_engine priority_engine.cpp

# Stage 2: Python App
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libc6 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Copy compiled C++ binary from builder
COPY --from=cpp-builder /priority_engine .
RUN chmod +x priority_engine

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=TRUE

# Run the application
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
