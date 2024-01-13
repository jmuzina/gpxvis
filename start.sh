#!/bin/bash

Docker build -f ./Dockerfile-local . -t gpxvis:latest
Docker run -p 80:5000 gpxvis:latest