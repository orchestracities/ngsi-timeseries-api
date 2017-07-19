FROM arm32v6/python:alpine3.6

RUN pip install requests

RUN mkdir -p /src/weather_station

COPY weather_station.py /src/weather_station/weather_station.py

CMD python /src/weather_station/weather_station.py
