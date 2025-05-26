# Use official Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot code
COPY bot.py .

# Set environment variables at runtime (do NOT hardcode tokens here)

# Command to run the bot
CMD ["python", "bot.py"]
