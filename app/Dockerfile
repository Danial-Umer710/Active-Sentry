FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all modular scripts
COPY bait.py guard.py start.sh ./

# Give execution rights to the starter
RUN chmod +x start.sh

# Run the orchestrator
CMD ["./start.sh"]
