FROM python:3.5

RUN mkdir -p /src/ngsi-timeseries-api

COPY requirements.txt /src/ngsi-timeseries-api/requirements.txt

RUN pip install -r /src/ngsi-timeseries-api/requirements.txt

# TODO: WARNING! This should not copy sensitive files ignored by git.
COPY . /src/ngsi-timeseries-api/

WORKDIR /src/ngsi-timeseries-api/

ENV PYTHONPATH=$PWD:$PYTHONPATH

CMD python reporter/reporter.py
