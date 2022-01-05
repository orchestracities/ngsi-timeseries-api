
# Default Builder, distro version
ARG BUILDER=python:3.8.5-alpine3.12
ARG DISTRO=python:3.8.5-alpine3.12
ARG PACKAGE_MANAGER=apk

########################################################################################
#
# This build stage builds the sources locally for testing only.
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
	# also ensure that prerequisites are installed prior to downloading sources
	if [ "${PACKAGE_MANAGER}" = "apt"  ]; then \
		echo -e "\033[0;33mWARNING: Overriding default package manager. Using \"${PACKAGE_MANAGER}\" .\033[0m"; \
		apt-get update; \
		apt-get install -y --no-install-recommends gcc python3 python3-dev python3-pip wget curl; \
	elif [ "${PACKAGE_MANAGER}" = "yum"  ]; then \
		echo -e "\033[0;33mWARNING: Overriding default package manager. Using \"${PACKAGE_MANAGER}\" .\033[0m"; \
		yum install -y gcc python3 python3-dev py-pip build-base wget curl; \
		yum clean all; \
	elif [ "${PACKAGE_MANAGER}" = "apk"  ]; then \
		echo -e "\033[0;34mINFO: Using default \"${PACKAGE_MANAGER}\".\033[0m"; \
		apk --no-cache --update-cache add gcc python3 python3-dev py-pip build-base wget curl; \
	else \
	 	echo -e "\033[0;31mERROR: Package Manager \"${PACKAGE_MANAGER}\" not supported.\033[0m"; \
	 	exit 1; \
	fi


COPY . /opt/quantumleap/
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /opt/quantumleap

RUN ln -s /usr/include/locale.h /usr/include/xlocale.h; \
	pip install pipenv; \
	pipenv lock -r > requirements.txt; \
	pip install -r requirements.txt; \
	pip install supervisor;

########################################################################################
#
# This build stage creates an image for testing only.
#
########################################################################################

FROM ${DISTRO} AS distro
ARG PACKAGE_MANAGER

LABEL "maintainer"="QuantumLeap Team, Orchestra Cities"
LABEL "org.opencontainers.image.documentation"="https://quantumleap.readthedocs.io/"
LABEL "org.opencontainers.image.vendor"="Martel Innovate GmbH"
LABEL "org.opencontainers.image.licenses"="MIT"
LABEL "org.opencontainers.image.title"="QuantumLeap - Test Image"
LABEL "org.opencontainers.image.description"=" FIWARE Generic Enabler to support the usage of NGSI-v2 (and NGSI-LD experimentally) data in time-series databases"

RUN \
	# Ensure  that prerequisites are installed
	if [ "${PACKAGE_MANAGER}" = "apt"  ]; then \
		apt-get update; \
		apt-get install -y --no-install-recommends curl; \
	elif [ "${PACKAGE_MANAGER}" = "yum"  ]; then \
		yum install -y curl; \
		yum clean all; \
	elif [ "${PACKAGE_MANAGER}" = "apk"  ]; then \
		apk --no-cache --update-cache add curl; \
	else \
	 	echo -e "\033[0;31mERROR: Package Manager \"${PACKAGE_MANAGER}\" not supported.\033[0m"; \
	 	exit 1; \
	fi
COPY --from=builder /opt/quantumleap /opt/quantumleap
COPY --from=builder /opt/venv /opt/venv

USER root
RUN \
	if [ "${PACKAGE_MANAGER}" = "apk"  ]; then \
		adduser -D -H app-user; \
	else \
	 	useradd -m app-user; \
	fi

USER app-user

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONPATH=$PWD:$PYTHONPATH

WORKDIR /opt/quantumleap/src
RUN \
	pip install -r ../requirements.txt; \
	pip install supervisor;

EXPOSE 8668
ENTRYPOINT ["python", "app.py"]