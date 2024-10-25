# syntax=docker/dockerfile:1

FROM python:3.8-bullseye

# install system dependencies (I think the PIL python library requires all this qt5 shit)
RUN pip install --upgrade pip
RUN apt update && apt install -y uwsgi qtbase5-dev qtchooser qt5-qmake qtbase5-dev-tools pyqt5-dev postgresql ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN pip3 --version

# install python dependencies
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
# install flask-track-usage AFTER other dependancies have been installed (depends onsphinxcontrib-applehelp)
RUN pip3 install git+https://github.com/ashcrow/flask-track-usage@baeec4d#egg=Flask-Track-Usage

# copy project files to WORKDIR
COPY . .

# expose port to host
EXPOSE 5000

# run entrypoint.sh to init db
ENTRYPOINT ["/app/entrypoint.sh"]