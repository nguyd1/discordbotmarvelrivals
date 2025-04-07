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

# Install Chrome
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get install -y ./google-chrome-stable_current_amd64.deb && \
    rm ./google-chrome-stable_current_amd64.deb

# Get Chrome version and install matching ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | cut -d " " -f3 | cut -d "." -f1) && \
    wget -q "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}" -O CHROME_DRIVER_VERSION && \
    wget -q "https://chromedriver.storage.googleapis.com/$(cat CHROME_DRIVER_VERSION)/chromedriver_linux64.zip" && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/bin/ && \
    chmod +x /usr/bin/chromedriver && \
    rm chromedriver_linux64.zip CHROME_DRIVER_VERSION

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

# Verify installations and versions match
RUN CHROME_VER=$(google-chrome --version | cut -d " " -f3) && \
    DRIVER_VER=$(chromedriver --version | cut -d " " -f2) && \
    echo "Chrome version: $CHROME_VER" && \
    echo "ChromeDriver version: $DRIVER_VER" && \
    if [ "${CHROME_VER%%.*}" != "${DRIVER_VER%%.*}" ]; then \
        echo "Version mismatch!" && exit 1; \
    fi

# Run the bot
CMD ["python", "botforserver.py"]