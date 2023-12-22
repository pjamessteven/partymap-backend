#!/bin/bash

# Copyright 2017 Théo Chamley
# Permission is hereby granted, free of charge, to any person obtaining a copy of 
# this software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons
# to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
# BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,

# SOURCEE : https://gist.github.com/MrTrustor/e690ba75cefe844086f5e7da909b35ce#file-clean-docker-for-mac-sh

cat <<EOF
=======================================
= SOURCE : 2017 Théo Chamley	      =
= EDITED : tyacode@gmail.com          =
= TIME   : September 2023             =
= MODIFY : Docker.qcow2 -> Docker.raw =
=======================================

============= HOW TO USE ================================================                
 1. ex. existing image : docker/getting-started, alpine
 2. active executable  : chmod +x clean-docker-for-mac.sh
 3. COMMAND : ./clean-docker-for-mac.sh docker/getting-started alpine
 4. Done       
=========================================================================
EOF

IMAGES=$@

echo ""
echo "==================================================================="
echo "This will REMOVE all your current containers and images except for:"
echo ""
for image in ${IMAGES}; do
	echo "- ${image}"
done
echo ""
echo "==================================================================="
echo ""
read -p "ARE YOU SURE? [Y/N] " -n 1 -r
echo ""   # (optional) move to a new line
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    exit 1
fi

echo ""
echo "1. MAKE TEMP DIR"
TMP_DIR=$(mktemp -d)

pushd $TMP_DIR >/dev/null

echo "TMP_DIR is set to: $TMP_DIR"
echo ""

open -a Docker
echo "2. SAVING CHOSEN IMAGES"
for image in ${IMAGES}; do
	echo "==> Saving ${image}"
	tar=$(echo -n ${image} | base64)
	docker save -o ${tar}.tar ${image}
	echo "==> Done."
done
echo ""

echo "3. CLEANING UP"
echo -n "==> Quiting Docker"
osascript -e 'quit app "Docker"'
while docker info >/dev/null 2>&1; do
	echo -n "."
	sleep 1
done;

echo "==> Removing : ~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw"
rm ~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw

echo "==> Launching Docker"
open -a Docker
echo -n "==> Waiting for Docker to start"
until docker info >/dev/null 2>&1; do
	echo -n "."
	sleep 1
done;

echo "=> Done."
echo ""

echo "4. LOADING IMAGES"
for image in ${IMAGES}; do
	echo "==> Loading ${image}"
	tar=$(echo -n ${image} | base64)
	docker load -q -i ${tar}.tar || exit 1
	echo "==> Done."
done
echo ""

popd >/dev/null
rm -r ${TMP_DIR}