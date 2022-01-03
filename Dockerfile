
ARG BUILDER=python:3.8.5-alpine3.12
ARG DISTRO=python:3.8.5-alpine3.12
ARG PACKAGE_MANAGER=apk
ARG USER=405



########################################################################################
#
# This build stage builds the sources
#
# --target=builder
#
######################################################################################## 

FROM ${BUILDER} AS builder
ARG PACKAGE_MANAGER

# hadolint ignore=DL3002
USER root
# hadolint ignore=SC2039
RUN \
	# Ensure that the chosen package manger is supported by this Dockerfile
	# also ensure that unzip and git is installed prior to downloading sources
	if [ "${PACKAGE_MANAGER}" = "apt"  ]; then \
		echo -e "\033[0;34mINFO: Using default \"${PACKAGE_MANAGER}\".\033[0m"; \
		apt-get install -y --no-install-recommends gcc python3 python3-dev py-pip build-base wget; \
	elif [ "${PACKAGE_MANAGER}" = "yum"  ]; then \
		echo -e "\033[0;33mWARNING: Overriding default package manager. Using \"${PACKAGE_MANAGER}\" .\033[0m"; \
		yum install -y gcc python3 python3-dev py-pip build-base wget; \
		yum clean all; \
	elif [ "${PACKAGE_MANAGER}" = "apk"  ]; then \
		echo -e "\033[0;33mWARNING: Overriding default package manager. Using \"${PACKAGE_MANAGER}\" .\033[0m"; \
		apk --no-cache --update-cache add gcc python3 python3-dev py-pip build-base wget; \
	else \
	 	echo -e "\033[0;31mERROR: Package Manager \"${PACKAGE_MANAGER}\" not supported.\033[0m"; \
	 	exit 1; \
	fi

WORKDIR /usr/local
RUN ln -s /usr/include/locale.h /usr/include/xlocale.h
RUN pip install pipenv
RUN mkdir -p /src/ngsi-timeseries-api
COPY Pipfile /src/ngsi-timeseries-api/Pipfile
COPY Pipfile.lock /src/ngsi-timeseries-api/Pipfile.lock
RUN cd /src/ngsi-timeseries-api && { pipenv lock -r > /src/ngsi-timeseries-api/requirements.txt; }
RUN pip install -t /src/ngsi-timeseries-api -r /src/ngsi-timeseries-api/requirements.txt
RUN pip install supervisor


########################################################################################
#
# This build stage creates an image for production.
#
########################################################################################

FROM ${DISTRO} AS distro
ARG PACKAGE_MANAGER

RUN \
	# Ensure that the chosen package manger is supported by this Dockerfile
	# also ensure that unzip and git is installed prior to downloading sources
	if [ "${PACKAGE_MANAGER}" = "apt"  ]; then \
		echo -e "\033[0;34mINFO: Using default \"${PACKAGE_MANAGER}\".\033[0m"; \
		apt-get install -y --no-install-recommends curl; \
	elif [ "${PACKAGE_MANAGER}" = "yum"  ]; then \
		echo -e "\033[0;33mWARNING: Overriding default package manager. Using \"${PACKAGE_MANAGER}\" .\033[0m"; \
		yum install -y curl; \
		yum clean all; \
	elif [ "${PACKAGE_MANAGER}" = "apk"  ]; then \
		echo -e "\033[0;33mWARNING: Overriding default package manager. Using \"${PACKAGE_MANAGER}\" .\033[0m"; \
		apk --no-cache --update-cache add curl; \
	else \
	 	echo -e "\033[0;31mERROR: Package Manager \"${PACKAGE_MANAGER}\" not supported.\033[0m"; \
	 	exit 1; \
	fi
COPY --from=builder /usr/local /usr/local
COPY --from=builder /src/ngsi-timeseries-api/requirements.txt /src/ngsi-timeseries-api/requirements.txt
COPY . /src/ngsi-timeseries-api/
WORKDIR /src/ngsi-timeseries-api/
RUN pip install -r requirements.txt
WORKDIR /src/ngsi-timeseries-api/src

ENV PYTHONPATH=$PWD:$PYTHONPATH

USER ${USER}
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