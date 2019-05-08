FROM python:3.6-alpine as base
FROM base as builder
RUN apk --no-cache --update-cache add gcc python python-dev py-pip build-base wget
RUN ln -s /usr/include/locale.h /usr/include/xlocale.h
RUN pip install pipenv
RUN mkdir -p /src/ngsi-timeseries-api
COPY Pipfile /src/ngsi-timeseries-api/Pipfile
COPY Pipfile.lock /src/ngsi-timeseries-api/Pipfile.lock
RUN mkdir /install
WORKDIR /install
RUN cd /src/ngsi-timeseries-api && { pipenv lock -r > /requirements.txt; }
RUN pip install --install-option="--prefix=/install" -r /requirements.txt

FROM base
RUN apk --no-cache add curl
COPY --from=builder /install /usr/local
COPY . /src/ngsi-timeseries-api/
WORKDIR /src/ngsi-timeseries-api/src
ENV PYTHONPATH=$PWD:$PYTHONPATH

CMD python app.py
