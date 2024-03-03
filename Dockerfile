FROM python:3.8

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/

COPY enterypoint.sh /app/

RUN pip install -r requirements.txt

COPY . /app/

ADD . /app

EXPOSE 8000

ENTRYPOINT ["sh", "/app/enterypoint.sh"]
