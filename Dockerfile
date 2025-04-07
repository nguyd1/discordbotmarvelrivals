FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    gnupg \
    curl \
    xvfb \
    libgconf-2-4 \
    libnss3 \
    libxss1 \
    libasound2 \
    libglib2.0-0

# Install Chrome using the alternative method
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable

# Install ChromeDriver using Chrome For Testing
RUN chrome_version=$(google-chrome --version | awk '{print $3}' | cut -d. -f1) && \
    wget -q https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${chrome_version}.0.6261.111/linux64/chromedriver-linux64.zip && \
    unzip -j chromedriver-linux64.zip "chromedriver-linux64/chromedriver" -d /usr/bin/ && \
    chmod +x /usr/bin/chromedriver && \
    rm chromedriver-linux64.zip

# Set up working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CHROME_BINARY=/usr/bin/google-chrome
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV DISPLAY=:99

# Verify installations
RUN echo "Chrome version:" && google-chrome --version && \
    echo "ChromeDriver version:" && chromedriver --version

# Run the bot
CMD ["python", "botforserver.py"]