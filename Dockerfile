FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY setup.py .

# Install the application
RUN pip install -e .

# Create non-root user
RUN useradd -m -u 1000 appuser
RUN mkdir -p /home/appuser/.calctl && chown appuser:appuser /home/appuser/.calctl

# Switch to non-root user
USER appuser

# Volume for data persistence
VOLUME ["/home/appuser/.calctl"]

# Set entrypoint
ENTRYPOINT ["calctl"]
