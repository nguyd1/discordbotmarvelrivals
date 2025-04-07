FROM joyzoursky/python-chromedriver:3.9-selenium

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

# Verify Chrome and ChromeDriver are installed
RUN google-chrome --version && \
    chromedriver --version

# Run the bot
CMD ["python", "botforserver.py"]