# Dockerfile
FROM python:3.11-slim

WORKDIR /opt/dagster/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the project files
COPY . .

# Install Python dependencies
RUN pip install -e ".[dev]"

# Create directory for data
RUN mkdir -p /opt/dagster/dagster_home/data
# populate the database
RUN python -m src.init_data.populate_db

# Set environment variables
ENV DAGSTER_HOME=/opt/dagster/dagster_home

EXPOSE 3000

CMD ["dagster", "api", "grpc", "-h", "0.0.0.0", "-p", "3000"]
