FROM python:3.9-buster

WORKDIR /app

# Dependencies necessary for Qt
RUN apt-get update && apt-get install libgl1 -y

# Install Python packages
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Copy application files
COPY . .

# Enable "headless" mode i.e. with no GUI
ENV QT_QPA_PLATFORM=offscreen

# Start the app
CMD ["python", "main.py"]
