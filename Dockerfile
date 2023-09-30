FROM python:3.8-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY Pipfile Pipfile.lock /app/

RUN pip install pipenv && \
    pipenv install --deploy --ignore-pipfile

COPY . /app/

EXPOSE 5000

CMD ["pipenv", "run", "python", "app.py"]
