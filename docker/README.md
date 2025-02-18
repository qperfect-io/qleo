# Docker instructions

## Build from pypi

use the docker file "Dockerfile"

Run the command below from the current repository to build:
```
docker build -t qleo .
```

## Build from source

use the file "Dockerfile_source"

Run the line below from the root of the repository to build:
```
docker build -t qleo -f "docker/Dockerfile_source" .
```

## Run the container

run the container in interactive mode with teh following:
```
docker run -it qleo
```