FROM python:3.8-alpine

RUN apk add iproute2

RUN pip3 install flask

WORKDIR /app

COPY . /app

CMD ["python3", "main.py", "--ip", "0.0.0.0"]