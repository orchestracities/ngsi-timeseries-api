FROM python:3.8.5-alpine3.12

RUN apk --no-cache --update-cache add postgresql-client openssl

RUN mkdir -p /ngsi-timeseries-api/timescale-container

COPY ./quantumleap-db-setup.py /ngsi-timeseries-api/timescale-container/

WORKDIR /ngsi-timeseries-api/timescale-container

CMD python quantumleap-db-setup.py \
        --ql-db-pass "$QL_DB_PASS" \
        --ql-db-init-dir "$QL_DB_INIT_DIR" \
        --pg-host "$PG_HOST" \
        --pg-pass "$PG_PASS"
