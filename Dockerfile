FROM python:3.8-alpine

RUN apk add iproute2

RUN pip3 install flask

ENV TCGUI_IP=0.0.0.0

WORKDIR /app

COPY . /app

CMD ["python3", "main.py"]