# Use the official Python 3.13 image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy all files
COPY . .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose Streamlit port
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "scripts/search_api.py", "--server.port=8501", "--server.address=0.0.0.0"]
