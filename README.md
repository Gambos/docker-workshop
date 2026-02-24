# docker-workshop
Datatalksclub Workshop Codespace

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

### Comparing Python Versions

```bash
uv run which python  # Python in the virtual environment, which is 3.13 in this case
uv run python -V

which python        # System Python
python -V
```
You'll see they're different - `uv run` uses the isolated environment.

### Adding Dependencies

Now let's add pandas:

```bash
uv add pandas pyarrow
```

This adds pandas to your `pyproject.toml` and installs it in the virtual environment.

### Running the Pipeline

Now we can execute the file with input param '10':

```bash
uv run python pipeline.py 10
```

We will see:

* `['pipeline.py', '10']`
* `job finished successfully for day = 10`

## Git Configuration

This script produces a binary (parquet) file, so let's make sure we don't accidentally commit it to git by adding parquet extensions to `.gitignore`:

```
*.parquet
```