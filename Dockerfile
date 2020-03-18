FROM tiangolo/uwsgi-nginx-flask:python3.6-alpine3.7
RUN apk --update add bash nano
ENV STATIC_URL static
ENV STATIC_PATH static
COPY . /app
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt