FROM python:3.8.5-alpine3.12 as base
FROM base as builder
RUN apk --no-cache --update-cache add gcc python3 python3-dev py-pip build-base wget
RUN ln -s /usr/include/locale.h /usr/include/xlocale.h
RUN pip install pipenv
RUN mkdir -p /src/ngsi-timeseries-api
COPY Pipfile /src/ngsi-timeseries-api/Pipfile
COPY Pipfile.lock /src/ngsi-timeseries-api/Pipfile.lock
RUN cd /src/ngsi-timeseries-api && { pipenv requirements > /requirements.txt; }
RUN pip install -r /requirements.txt
RUN pip install supervisor

FROM base
RUN apk --no-cache add curl
COPY --from=builder /usr/local /usr/local
COPY . /src/ngsi-timeseries-api/
WORKDIR /src/ngsi-timeseries-api/src
ENV PYTHONPATH=$PWD:$PYTHONPATH

EXPOSE 8668
ENTRYPOINT ["python", "app.py"]
# NOTE.
# The above is basically the same as running:
#
#     gunicorn server.wsgi --config server/gconfig.py
#
# You can also pass any valid Gunicorn option as container command arguments
# to add or override options in server/gconfig.py---see `server.grunner` for
# the details.
# In particular, a convenient way to reconfigure Gunicorn is to mount a config
# file on the container and then run the container with the following option
#
#     --config /path/to/where/you/mounted/your/gunicorn.conf.py
#
# as in the below example
#
#     $ echo 'workers = 2' > gunicorn.conf.py
#     $ docker run -it --rm \
#                  -p 8668:8668 \
#                  -v $(pwd)/gunicorn.conf.py:/gunicorn.conf.py
#                  orchestracities/quantumleap --config /gunicorn.conf.py
#
