FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot file
COPY ielts_bot.py .

# Create data directory
RUN mkdir -p data

# Run bot
CMD ["python", "ielts_bot.py"]
