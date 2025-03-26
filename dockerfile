FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install Uvicorn
RUN uv pip install --no-cache-dir uvicorn --system
# Copy the project into the image
COPY . /app
WORKDIR /app
COPY ./agent_utils*.whl /app

RUN uv sync
RUN . /app/.venv/bin/activate

RUN uv pip install agent-utils
#Ensure the agent-utils package is installed correctly
RUN uv pip show agent-utils 

EXPOSE 8000

# Set the entrypoint so that additional arguments passed at runtime are appended
# ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
ENTRYPOINT ["/app/.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD []