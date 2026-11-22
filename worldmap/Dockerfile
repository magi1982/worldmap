ARG BUILD_FROM
FROM ${BUILD_FROM}

# tzdata: local dates for trips; no compilers needed (binary wheels only)
RUN apk add --no-cache tzdata

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --only-binary=:all: -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

COPY app /app
COPY run.sh /run.sh
RUN chmod a+x /run.sh

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 WORLDMAP_DATA=/data
CMD [ "/run.sh" ]
