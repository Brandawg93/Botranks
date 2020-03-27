FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7-alpine3.8
RUN apk add build-base
COPY . /app
RUN pip install --no-use-pep517 multidict
RUN pip install -r requirements.txt