# Docker image for MyDIG

## Build image

    docker build -t mydig_ws .

## Run container

    docker run -p 9879:9879 -p 9880:9880 -v $(pwd)/user_data:/user_data -it mydig_ws
    
`/user_data` volume needs to be mounted while running. Make sure all following files & directories are there:

- `projects/`: MyDIG Projects. Git repo.
- `landmark/`: Inferlink Landmark. Git repo.
- `resources/` Resources. Git repo. Can be cloned from `https://github.com/usc-isi-i2/dig3-resources.git`.
- `config.py`: Config of web service.
- `config_frontendpy`: Config of frontend.
- `default_source_credentials.json`: Default credentials of `source` object.