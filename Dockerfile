FROM python:3.6

RUN mkdir -p /src/ngsi-timeseries-api

COPY requirements.txt /src/ngsi-timeseries-api/requirements.txt

RUN pip install -r /src/ngsi-timeseries-api/requirements.txt

COPY . /src/ngsi-timeseries-api/

WORKDIR /src/ngsi-timeseries-api/src

ENV PYTHONPATH=$PWD:$PYTHONPATH

CMD python app.py
