FROM python:3.8-alpine

RUN apk add --no-cache iproute2 && \
    rm -rf /var/cache/apk/*

RUN pip3 install Flask

ENV TCGUI_IP=0.0.0.0

WORKDIR /app

COPY . /app

CMD ["python3", "main.py"]
