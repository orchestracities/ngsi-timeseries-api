
ARG GITHUB_ACCOUNT=orchestracities
ARG GITHUB_REPOSITORY=ngsi-timeseries-api
ARG DOWNLOAD=latest
ARG SOURCE_BRANCH=master

# Default Builder, distro version
ARG BUILDER=python:3.8.5-alpine3.12
ARG DISTRO=python:3.8.5-alpine3.12
ARG PACKAGE_MANAGER=apk

########################################################################################
#
# This build stage builds the sources
#
# --target=builder
#
######################################################################################## 

FROM ${BUILDER} AS builder
ARG GITHUB_ACCOUNT
ARG GITHUB_REPOSITORY
ARG DOWNLOAD
ARG SOURCE_BRANCH
ARG PACKAGE_MANAGER

# hadolint ignore=DL3002
USER root
# hadolint ignore=SC2039
RUN \
	# Ensure that the chosen package manger is supported by this Dockerfile
	# also ensure that unzip and git is installed prior to downloading sources
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



# As an Alternative for local development, just copy this Dockerfile into file the root of 
# the repository and replace the whole RUN statement below by the following COPY statement 
# in your local source using :
#
# COPY . /opt/quantumleap/
#

RUN \
	if [ "${DOWNLOAD}" = "latest" ] ; \
	then \
		RELEASE="${SOURCE_BRANCH}"; \
		echo "INFO: Building Latest Development from ${SOURCE_BRANCH} branch."; \
	elif [ "${DOWNLOAD}" = "stable" ]; \
	then \
		RELEASE=$(curl -s https://api.github.com/repos/"${GITHUB_ACCOUNT}"/"${GITHUB_REPOSITORY}"/releases/latest | grep 'tag_name' | cut -d\" -f4); \
		echo "INFO: Building Latest Stable Release: ${RELEASE}"; \
	else \
	 	RELEASE="${DOWNLOAD}"; \
	 	echo "INFO: Building Release: ${RELEASE}"; \
	fi && \
	RELEASE_CONCAT=$(echo "${RELEASE}" | tr / -); \
	curl -s -L https://github.com/"${GITHUB_ACCOUNT}"/"${GITHUB_REPOSITORY}"/archive/"${RELEASE}".zip > source.zip && \
	unzip source.zip -x "*/test/**" "*/rpm/**" "*/ghpages/**" "*/docs/**" "*/.*" && \
	rm source.zip && \
	mv "${GITHUB_REPOSITORY}-${RELEASE_CONCAT}" /opt/quantumleap

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /opt/quantumleap

RUN ln -s /usr/include/locale.h /usr/include/xlocale.h; \
	pip install pipenv; \
	pipenv lock -r > requirements.txt; \
	pip install -r requirements.txt;

########################################################################################
#
# This build stage creates an image for production.
#
########################################################################################

FROM ${DISTRO} AS distro
ARG PACKAGE_MANAGER
ARG GITHUB_ACCOUNT
ARG GITHUB_REPOSITORY

LABEL "maintainer"="QuantumLeap Team, Orchestra Cities"
LABEL "org.opencontainers.image.documentation"="https://quantumleap.readthedocs.io/"
LABEL "org.opencontainers.image.vendor"="Martel Innovate GmbH"
LABEL "org.opencontainers.image.licenses"="MIT"
LABEL "org.opencontainers.image.title"="QuantumLeap"
LABEL "org.opencontainers.image.description"=" FIWARE Generic Enabler to support the usage of NGSI-v2 (and NGSI-LD experimentally) data in time-series databases"
LABEL "org.opencontainers.image.source"="https://github.com/${GITHUB_ACCOUNT}/${GITHUB_REPOSITORY}"

RUN \
	# Ensure that the chosen package manger is supported by this Dockerfile
	# also ensure that unzip and git is installed prior to downloading sources
	if [ "${PACKAGE_MANAGER}" = "apt"  ]; then \
		echo -e "\033[0;33mWARNING: Overriding default package manager. Using \"${PACKAGE_MANAGER}\" .\033[0m"; \
		apt-get update; \
		apt-get install -y --no-install-recommends curl; \
	elif [ "${PACKAGE_MANAGER}" = "yum"  ]; then \
		echo -e "\033[0;33mWARNING: Overriding default package manager. Using \"${PACKAGE_MANAGER}\" .\033[0m"; \
		yum install -y curl; \
		yum clean all; \
	elif [ "${PACKAGE_MANAGER}" = "apk"  ]; then \
		echo -e "\033[0;34mINFO: Using default \"${PACKAGE_MANAGER}\".\033[0m"; \
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
	pip install -r ../requirements.txt;
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