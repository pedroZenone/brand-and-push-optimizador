FROM --platform=linux/amd64 python:3.10-slim

WORKDIR /app

COPY . /app

RUN apt-get -y update
RUN apt-get -y install freetds-dev freetds-bin pip

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

EXPOSE 8080

CMD [ "python3", "app.py"]