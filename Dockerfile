FROM python:3.14

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir /usr/src/app/sound
COPY *.py /usr/src/app


CMD [ "python", "./main.py" ]