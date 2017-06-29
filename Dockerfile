FROM python:3.5

RUN mkdir /src

# TODO: WARNING! This should not copy sensitive files ignored by git.
COPY . /src/ngsi-timeseries-api/

WORKDIR /src/ngsi-timeseries-api/

RUN pip install -r requirements.txt

ENV PYTHONPATH=$PWD:$PYTHONPATH

ENTRYPOINT python reporter/reporter.py
