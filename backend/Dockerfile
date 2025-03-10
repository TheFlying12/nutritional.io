# Use Python 3.8 base image
FROM python:3.8-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint script
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Copy application code
COPY . .

EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Run with host 0.0.0.0 to allow external connections
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]