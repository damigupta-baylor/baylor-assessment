FROM python:3.12-slim

# Install system dependencies and clean up
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY main.py gene_metadata.py init.sql pub.pdf ./

# Run the application
CMD ["python3", "main.py"]