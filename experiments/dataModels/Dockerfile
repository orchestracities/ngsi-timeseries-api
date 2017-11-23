FROM python:3.6

RUN pip install locustio

RUN mkdir -p /src/dataModels

COPY *.py /src/dataModels/

WORKDIR /src/dataModels/

ENV PYTHONPATH=$PWD:$PYTHONPATH

ENTRYPOINT ["locust"]
