FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    ca-certificates \
    curl \
    unzip \
    xvfb

# Install Chrome
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb

# Verify Chrome installation
RUN ln -s /usr/bin/google-chrome-stable /usr/bin/chrome \
    && chrome --version

# Install ChromeDriver
RUN CHROME_VERSION=$(google-chrome-stable --version | cut -d " " -f3) \
    && MAJOR_VERSION=$(echo $CHROME_VERSION | cut -d "." -f1) \
    && wget -q "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${MAJOR_VERSION}.0.6261.94/linux64/chromedriver-linux64.zip" \
    && unzip chromedriver-linux64.zip \
    && mv chromedriver-linux64/chromedriver /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf chromedriver-linux64.zip chromedriver-linux64

# Set up working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Verify installations
RUN which google-chrome-stable && \
    which chromedriver && \
    google-chrome-stable --version && \
    chromedriver --version

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CHROME_BINARY=/usr/bin/google-chrome-stable
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver
ENV DISPLAY=:99

# Run the bot
CMD ["python", "botforserver.py"]