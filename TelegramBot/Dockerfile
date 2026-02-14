
FROM python:3.10-slim

# Set the workbook inside the container
WORKDIR /app

# 1. Copy only the requirements (to take advantage of the Docker cache)
COPY requirements.txt .

# 2. Install the libraries
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy the rest of the source code
COPY . .

# Command to start the bot
CMD ["python", "-u", "main.py"]