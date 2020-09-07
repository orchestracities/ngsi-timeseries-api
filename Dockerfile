FROM python:3.8.3-alpine3.12 as base
FROM base as builder
RUN apk --no-cache --update-cache add gcc python3 python3-dev py-pip build-base wget libffi-dev
RUN ln -s /usr/include/locale.h /usr/include/xlocale.h
RUN pip install pipenv gunicorn gevent
RUN mkdir -p /src/ngsi-timeseries-api
COPY Pipfile /src/ngsi-timeseries-api/Pipfile
COPY Pipfile.lock /src/ngsi-timeseries-api/Pipfile.lock
RUN cd /src/ngsi-timeseries-api && { pipenv lock -r > /requirements.txt; }
RUN pip install -r /requirements.txt

FROM base
RUN apk --no-cache add curl
COPY --from=builder /usr/local /usr/local
COPY . /src/ngsi-timeseries-api/
WORKDIR /src/ngsi-timeseries-api/src
ENV PYTHONPATH=$PWD:$PYTHONPATH

EXPOSE 8668

CMD ["gunicorn", "-b", "0.0.0.0:8668", "uwsgi", "--log-level", "debug", "--worker-class", "gevent", "--worker-connections", "10000", "--config", "gunicorn.conf.py"]
