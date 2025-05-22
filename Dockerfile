FROM python:3.11-alpine

RUN apk add --no-cache bash

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --upgrade pip
COPY ./requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY . /app/
RUN chmod +x /wait-for-it.sh 

EXPOSE 5000
