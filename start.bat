Docker build -f ./Dockerfile-local . -t gpxvis:latest
Docker run -d -p 80:5000 --name gpxivs gpxvis:latest