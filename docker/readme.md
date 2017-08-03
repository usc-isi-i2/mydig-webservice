# Docker image for MyDIG

There are two important directories:

- `/app`: All packages and dependencies.
- `/user_data`: All persistent data. Need to be mounted by user's directory. Make sure all following files & directories are there:
    - `projects/`: MyDIG Projects. Git repo.
    - `landmark/`: Inferlink Landmark. Git repo.
    - `resources/` Resources. Git repo. Can be cloned from `https://github.com/usc-isi-i2/dig3-resources.git`.
    - `config.py`: Config of web service.
    - `config_frontend.py`: Config of frontend.
    - `default_source_credentials.json`: Default credentials of `source` object.

## Build image

    docker build -t mydig_ws .

## Run container

    docker run -d -p 9879:9879 -p 9880:9880 -v $(pwd)/user_data:/user_data mydig_ws
    