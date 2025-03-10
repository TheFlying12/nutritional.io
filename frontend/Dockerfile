FROM python:3.8-slim

# Set working directory
WORKDIR /app

# Set build argument for cache busting (default value is current timestamp)
ARG CACHE_BUST=1

# Copy application code
COPY . .

EXPOSE 8080

# Add a command to verify the content of script.js when building
RUN cat script.js | head -n 5

CMD ["python", "-m", "http.server", "8080"]