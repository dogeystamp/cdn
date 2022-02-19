FROM python:3

MAINTAINER dogeystamp "dogeystamp@disroot.org"

WORKDIR /app

COPY ./requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "./main.py"]
