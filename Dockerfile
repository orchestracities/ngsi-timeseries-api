FROM python:3.6
RUN pip install 'pipenv==2018.10.13'

RUN mkdir -p /src/ngsi-timeseries-api

COPY Pipfile /src/ngsi-timeseries-api/Pipfile
COPY Pipfile.lock /src/ngsi-timeseries-api/Pipfile.lock

RUN cd /src/ngsi-timeseries-api && { pipenv lock -r > requirements.txt; }
RUN pip install -r /src/ngsi-timeseries-api/requirements.txt

COPY . /src/ngsi-timeseries-api/

WORKDIR /src/ngsi-timeseries-api/src

ENV PYTHONPATH=$PWD:$PYTHONPATH

CMD python app.py
