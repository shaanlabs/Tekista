# Use Python 3.12 (stable and compatible)
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements first (for faster rebuilds)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your app files into the container
COPY . .

# Make sure app.db can be written
RUN chmod -R a+w /app

# Expose port 5000
EXPOSE 5000

# Tell Flask to run in development mode (optional but helpful)
ENV FLASK_APP=app.py
ENV FLASK_ENV=development

# Run the app
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]