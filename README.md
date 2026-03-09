# docker-workshop
Table of Contents：

- [1. Basic Docker Commands](#1-basic-docker-commands)

- [2. Managing Containers](#2-managing-containers)

- [3. Volumes](#3-volumes)

- [4. Using uv - Modern Python Package Manager](#4-using-uv---modern-python-package-manager)

- [5. Dockerizing the Pipeline](#5-dockerizing-the-pipeline)

- [6. Running PostgreSQL with Docker](#6-running-postgresql-with-docker)

- [7. Docker Compose](#7-docker-compose)

## 1. Basic Docker Commands

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

## 2. Managing Containers

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

## 3. Volumes

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

## 4. Using uv - Modern Python Package Manager
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

## 5. Dockerizing the Pipeline
Create the `Dockerfile` file.

Build the image: The image name will be `test` and its tag will be `pandas`. If the tag isn't specified it will default to `latest`. Note that when building docker image you need to exit the container.

```bash
docker build -t test:pandas .
```

We can now run the container and pass an argument to it, so that our pipeline will receive it and execute the script. Note that ENTRYPOINT ["python", "pipeline.py"] if when running this you are not in the container yet, this command will not let you stay in the container as it will exit once the python execution completes.

```bash
docker run -it --rm test:pandas 12
```
You should get the same output you did when you ran the pipeline script by itself.

If you simply want to run/enter this container next time, use:
```bash
docker run -it --rm --entrypoint bash test:pandas
```

> Note: these instructions assume that `pipeline.py` and `Dockerfile` are in the same directory. The Docker commands should also be run from the same directory as these files.

## 6. Running PostgreSQL with Docker

### (1) Running PostgreSQL in a Container
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
Use Ctrl+C to shut down the DB progress.

**Explanation of Parameters:**

* `-e` sets environment variables (user, password, database name)
* `-v ny_taxi_postgres_data:/var/lib/postgresql` creates a **named volume**
  * Docker manages this volume automatically
  * Data persists even after container is removed
  * Volume is stored in Docker's internal storage
* `-p 5432:5432` maps port 5432 from container to host. The script send connection request to localhost:5432 → host machine finds there is a docker port mapped for 5432 → repost to docker port → postgreSQL in container listen to 5432 and accept the connection
* `postgres:18` uses PostgreSQL version 18 (latest as of Dec 2025)

### (2) Log in DB with pgcil

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

```sql
-- List tables
\dt

-- Create a test table
CREATE TABLE test (id INTEGER, name VARCHAR(50));

-- Insert data
INSERT INTO test VALUES (1, 'Hello Docker');

-- Query data
SELECT * FROM test;

-- Exit
\q
```

### (3) Data Ingestion with Jupyter Notebook

#### a. Setting up Jupyter

Install Jupyter:

```bash
uv add --dev jupyter
```

Create a Jupyter notebook to explore the data, click through the port and go to Jupyter notebook in browser, create a new notebook and work on data ingestion in it.

```bash
uv run jupyter notebook
```

#### b. The NYC Taxi Dataset

We will use data from the [NYC TLC Trip Record Data website](https://www1.nyc.gov/site/tlc/about/tlc-trip-record-data.page).

Specifically, we will use the [Yellow taxi trip records CSV file for January 2021](https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz).

This data used to be csv, but later they switched to parquet. We want to keep using CSV because we need to do a bit of extra pre-processing (for the purposes of learning it).

A dictionary to understand each field is available [here](https://www1.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf).

> Note: The CSV data is stored as gzipped files. Pandas can read them directly.

#### c. Ingest data in Jupyter

`!` is a Jupyter command, indicating that the content after it is shell command not python.

```bash
!uv add sqlalchemy "psycopg[binary,pool]"
```

Python (Jupyter) → SQLAlchemy → psycopg driver → TCP connection → localhost:5432 → Docker port mapping → PostgreSQL Container → Database ny_taxi

Data ingestion code please check in Notebook.ipynb

#### d. Convert Notebook to Script and rename

```bash
uv run jupyter nbconvert --to=script Notebook.ipynb
mv Notebook.py Ingest_data.py
```

and run the script.

```bash
uv run python Ingest_data.py \
  --pg-user=root \
  --pg-pass=root \
  --pg-host=localhost \
  --pg-port=5432 \
  --pg-db=ny_taxi \
  --target-table=yellow_taxi_trips
```

### (4) Dockerizing the Ingestion Script

Build the Docker Image:

```bash
cd pipeline
docker build -t taxi_ingest:v001 .
```

After containerized, when this `taxi_ingest:v001` container wants to access to the postgreDB from another container, they need to be in the same network, so the pg-host can not be `localhost` anymore as it will just connects to the container itself, yet there is no DB listening to 5432 in this container.

Create virtual docker network:
```bash
docker network create pg-network
```

Rerun the postgreDB on the network:

```bash
docker run -it --rm \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v ny_taxi_postgres_data:/var/lib/postgresql \
  -p 5432:5432 \
  --network=pg-network \
  --name pgdatabase \
  postgres:18
```

Run the Containerized Ingestion script:

```bash
docker run -it \
  --network=pg-network \
  taxi_ingest:v001 \
    --pg-user=root \
    --pg-pass=root \
    --pg-host=pgdatabase \
    --pg-port=5432 \
    --pg-db=ny_taxi \
    --target-table=yellow_taxi_trips
```
### (5) pgAdmin - Database Management Tool

`pgcli` is a handy tool but it's cumbersome to use for complex queries and database management. [`pgAdmin` is a web-based tool](https://www.pgadmin.org/) that makes it more convenient to access and manage our databases.

It's possible to run pgAdmin as a container along with the Postgres container, but again both containers will have to be in the same virtual network so that they can find each other.

#### Run pgAdmin Container on the same network

```bash
docker run -it \
  -e PGADMIN_DEFAULT_EMAIL="admin@admin.com" \
  -e PGADMIN_DEFAULT_PASSWORD="root" \
  -v pgadmin_data:/var/lib/pgadmin \
  -p 8085:80 \
  --network=pg-network \
  --name pgadmin \
  dpage/pgadmin4
```
* The `-v pgadmin_data:/var/lib/pgadmin` volume mapping saves pgAdmin settings (server connections, preferences) so you don't have to reconfigure it every time you restart the container.
* The container needs 2 environment variables: a login email and a password. We use `admin@admin.com` and `root` in this example.
* pgAdmin is a web app and its default port is 80; we map it to 8085 in our localhost to avoid any possible conflicts.
* The actual image name is `dpage/pgadmin4`.

#### Connect pgAdmin to PostgreSQL

1. Open browser and go to `http://localhost:8085`
2. Login with email: `admin@admin.com`, password: `root`
3. Right-click "Servers" → Register → Server
4. Configure:
   - **General tab**: Name: `Local Docker`
   - **Connection tab**:
     - Host: `pgdatabase` (the --name of postgreDB container, as the two containers are in the same custom network, Docker DNS will resolve the container name to its corresponding IP address)
     - Port: `5432`
     - Username: `root`
     - Password: `root`
5. Save

## 7. Docker Compose

`docker-compose` allows us to launch multiple containers using a single configuration file, so that we don't have to run multiple complex `docker run` commands separately.

Docker compose makes use of YAML files: `docker-compose.yaml` file.

We don't have to specify a network because `docker compose` takes care of it: every single container (or "service", as the file states) will run within the same network and will be able to find each other according to their names (`pgdatabase` and `pgadmin` in this example).

#### Start Services with Docker Compose

We can now run Docker compose by running the following command from the same directory where `docker-compose.yaml` is found. Make sure that all previous containers aren't running anymore:

```bash
docker-compose up
```

#### Detached Mode

If you want to run the containers again in the background rather than in the foreground (thus freeing up your terminal), you can run them in detached mode:

```bash
docker-compose up -d
```

#### Stop Services

You will have to press `Ctrl+C` in order to shut down the containers when running in foreground mode. The proper way of shutting them down is with this command:

```bash
docker-compose down
```

#### Other Useful Commands

```bash
# View logs
docker-compose logs

# Stop and remove volumes
docker-compose down -v
```

#### Running the Ingestion Script with Docker Compose

If you want to re-run the dockerized ingest script when you run Postgres and pgAdmin with `docker compose`, you will have to find the name of the virtual network that Docker compose created for the containers.

```bash
# check the network link:
docker network ls

# it's pipeline_default (or similar based on directory name). Now run the script to ingest data in DB:
docker run -it --rm\
  --network=pipeline_default \
  taxi_ingest:v001 \
    --pg-user=root \
    --pg-pass=root \
    --pg-host=pgdatabase \
    --pg-port=5432 \
    --pg-db=ny_taxi \
    --target-table=yellow_taxi_trips
```