#FROM ubuntu:latest
#FROM fedora:39
FROM python:3.9.19
LABEL authors="Lap6ik"

WORKDIR /app

ENV DISPLAY=:1

RUN apt-get update && apt-get install -y --no-install-recommends\
    libgl1-mesa-glx \
    x11-apps \
    xvfb \
    xauth


COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

#ENV DISPLAY=:1
#ENV SCREEN=0
#ENV DBUS_SESSION_BUS_ADDRESS=/dev/null

COPY . /app/budget
CMD ["python", "budget/budgetApp.py"]