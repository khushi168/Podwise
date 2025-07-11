FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["streamlit", "run", "scripts/search_api.py", "--server.port=8000", "--server.enableCORS=false"]
