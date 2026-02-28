# docker-workshop
Table of Contents：

- [Basic Docker Commands](#basic-docker-commands)

- [Managing Containers](#managing-containers)

- [Volumes](#volumes)

- [Using uv - Modern Python Package Manager](#using-uv---modern-python-package-manager)

- [Dockerizing the Pipeline](#dockerizing-the-pipeline)

- [Running PostgreSQL with Docker](#running-postgresql-with-docker)

## Basic Docker Commands

Check Docker version:

```bash
docker --version
```

Run a simple container:

```bash
docker run hello-world
```

Run something more complex: Ubuntu is an official base image. This image contains a minimal Ubuntu user space, including tools such as bash, coreutils, and apt.

```bash
docker run ubuntu
```

Nothing happens. Need to run it in `-it` mode: Docker starts an Ubuntu container and allocates an interactive terminal for it.

```bash
docker run -it ubuntu
```

Install `python`in current container:

```bash
apt update && apt install python3
python3 -V
```

Run official python container:
```
docker run -it python:3.11-slim
```

## Managing Containers

The state is saved somewhere. We can see stopped containers:

```bash
docker ps -a
```

We can restart one of them, but we won't do it, because it's not a good practice. They take space, so let's delete them:

```bash
docker rm $(docker ps -aq)
```

Next time we run something, we add `--rm` to delete the container once we exit it:

```bash
docker run -it --rm ubuntu
```

## Volumes

With docker we can restore any container to its initial state in a reproducible manner. But what about data? A common way to do so is with _volumes_ to map files from host machine's directory to container's directory, so the container would be able to access to that directory but the file still exists in host machine when the container is deleted.

Let's create some data in `test`:

```bash
mkdir test
cd test
touch file1.txt file2.txt file3.txt
echo "Hello from host" > file1.txt
cd ..
```

Now let's create a simple script `test/list_files.py` that shows the files in the folder:

```python
from pathlib import Path

current_dir = Path.cwd()
current_file = Path(__file__).name

print(f"Files in {current_dir}:")

for filepath in current_dir.iterdir():
    if filepath.name == current_file:
        continue

    print(f"  - {filepath.name}")

    if filepath.is_file():
        content = filepath.read_text(encoding='utf-8')
        print(f"    Content: {content}")
```

Now let's map this to a Python container:

```bash
docker run -it \
    --rm \
    -v $(pwd)/test:/app/test \
    --entrypoint=bash \
    python:3.9.16-slim
```

Inside the container, run:

```bash
cd /app/test
ls -la
cat file1.txt
python script.py
```

You'll see the files from your host machine are accessible in the container!

## Using uv - Modern Python Package Manager
Instead of pip install globally, we want to use a **virtual environment** - an isolated Python environment that keeps dependencies for this project separate from other projects and from your system Python within your container.

Use `uv` - a modern, fast Python package and project manager written in Rust. It's much faster than pip and handles virtual environments automatically.

```bash
pip install uv
```

Now initialize a Python project with uv:

```bash
uv init --python 3.13
```

This creates a `pyproject.toml` file for managing dependencies and a `.python-version` file.

Comparing Python Versions:

```bash
uv run which python  # Python in the virtual environment, which is 3.13 in this case
uv run python -V

which python        # System Python
python -V
```
You'll see they're different - `uv run` uses the isolated environment.

Adding Dependencies. Now let's add pandas:

```bash
uv add pandas pyarrow
```

This adds pandas to your `pyproject.toml` and installs it in the virtual environment.

Running the Pipeline. Now we can execute the file with input param '10':

```bash
uv run python pipeline.py 10
```

We will see:

* `['pipeline.py', '10']`
* `job finished successfully for day = 10`

Git Configuration. This script produces a binary (parquet) file, so let's make sure we don't accidentally commit it to git by adding parquet extensions to `.gitignore`:

```
*.parquet
```

## Dockerizing the Pipeline
Create the following `Dockerfile` file:

Simple Dockerfile with pip:

```dockerfile
# base Docker image that we will build on
FROM python:3.13.11-slim

# set up our image by installing prerequisites; pandas in this case
RUN pip install pandas pyarrow

# set up the working directory inside the container
WORKDIR /app
# copy the script to the container. 1st name is source file, 2nd is destination
COPY pipeline.py pipeline.py

# define what to do first when the container runs
# in this example, we will just run the script
ENTRYPOINT ["python", "pipeline.py"]
```

**Explanation:**

- `FROM`: Base image (Python 3.13)
- `RUN`: Execute commands during build
- `WORKDIR`: Set working directory
- `COPY`: Copy files into the image
- `ENTRYPOINT`: Default command to run

Let's build the image: The image name will be `test` and its tag will be `pandas`. If the tag isn't specified it will default to `latest`. Note that when building docker image you need to exit the container.

```bash
docker build -t test:pandas .
```

We can now run the container and pass an argument to it, so that our pipeline will receive it and execute the script. Note that if when running this you are not in the container yet, this command will not let you stay in the container as it will exit once the python execution completes.

```bash
docker run -it --rm test:pandas 12
```
You should get the same output you did when you ran the pipeline script by itself.

If you simply want to run/enter this container next time, use:
```bash
docker run -it --rm --entrypoint bash test:pandas
```

> Note: these instructions assume that `pipeline.py` and `Dockerfile` are in the same directory. The Docker commands should also be run from the same directory as these files.

## Running PostgreSQL with Docker

### Running PostgreSQL in a Container
Create container, start the postgres server, intialize DB, create a folder anywhere you'd like for Postgres to store data in. We will use the example folder ny_taxi_postgres_data. Here's how to run the container:

```bash
docker run -it --rm \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v ny_taxi_postgres_data:/var/lib/postgresql \
  -p 5432:5432 \
  postgres:18
```

**Explanation of Parameters:**

* `-e` sets environment variables (user, password, database name)
* `-v ny_taxi_postgres_data:/var/lib/postgresql` creates a **named volume**
  * Docker manages this volume automatically
  * Data persists even after container is removed
  * Volume is stored in Docker's internal storage
* `-p 5432:5432` maps port 5432 from container to host
* `postgres:18` uses PostgreSQL version 18 (latest as of Dec 2025)

### Log in DB with pgcil

pgcli is a command-line client for PostgreSQL that connects to and interacts with a PostgreSQL server.

Install pgcli:

```bash
uv add --dev pgcli
```

The `--dev` flag marks this as a development dependency (not needed in production). It will be added to the `[dependency-groups]` section of `pyproject.toml` instead of the main `dependencies` section.

Now use it to connect to Postgres:

```bash
uv run pgcli -h localhost -p 5432 -u root -d ny_taxi
```

* `uv run` executes a command in the context of the virtual environment
* `-h` is the host. Since we're running locally we can use `localhost`.
* `-p` is the port.
* `-u` is the username.
* `-d` is the database name.
* The password is not provided; it will be requested after running the command.

When prompted, enter the password: `root`