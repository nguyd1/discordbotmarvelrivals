FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    apt-transport-https \
    ca-certificates \
    unzip \
    curl \
    xvfb \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    libgbm1 \
    libpangocairo-1.0-0 \
    libasound2

# Install Chrome
RUN mkdir -p /opt/google/chrome && \
    wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -x google-chrome-stable_current_amd64.deb /opt/google/chrome && \
    ln -s /opt/google/chrome/usr/bin/google-chrome-stable /usr/bin/google-chrome-stable && \
    rm google-chrome-stable_current_amd64.deb

# Get Chrome version and install matching ChromeDriver
RUN CHROME_VERSION=$(google-chrome-stable --version | awk '{print $3}' | cut -d'.' -f1) && \
    wget -q "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROME_VERSION}.0.6261.94/linux64/chromedriver-linux64.zip" && \
    unzip chromedriver-linux64.zip -d /tmp && \
    mv /tmp/chromedriver-linux64/chromedriver /usr/bin/chromedriver && \
    chmod +x /usr/bin/chromedriver && \
    rm -rf chromedriver-linux64.zip /tmp/chromedriver-linux64

# Set up working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CHROME_BINARY=/usr/bin/google-chrome-stable
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV DISPLAY=:99

# Run the bot
CMD ["python", "botforserver.py"]