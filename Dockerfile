FROM python:3.7-alpine
RUN mkdir /app
RUN mkdir /config
COPY powerstates.py /app
COPY requirements.txt /app
COPY config.json /config
WORKDIR /app
RUN apk update && apk add ipmitool
RUN pip install -r requirements.txt
CMD python -u app.py