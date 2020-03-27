FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7-alpine3.8
COPY . /app
RUN pip install -r requirements.txt