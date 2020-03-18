FROM tiangolo/meinheld-gunicorn-flask:python3.7-alpine3.8
RUN apk --update add bash nano
ENV STATIC_URL static
ENV STATIC_PATH static
COPY . /app
RUN pip install -r requirements.txt