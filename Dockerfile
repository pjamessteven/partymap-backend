# syntax=docker/dockerfile:1

FROM python:3.8.3

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND=noninteractive

# install system dependencies (I think the PIL library requires all this qt5 shit)
RUN pip install --upgrade pip
RUN apt update && apt install -y qtbase5-dev qtchooser qt5-qmake qtbase5-dev-tools pyqt5-dev qt5-default postgresql && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# install python dependencies
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# copy project files to WORKDIR
COPY . .

# expose port to host
EXPOSE 5000

# run entrypoint.sh to init db
# ENTRYPOINT ["/app/entrypoint.sh"]

# run server
CMD [ "python3", "manage.py", "runserver", "--host=0.0.0.0"]
