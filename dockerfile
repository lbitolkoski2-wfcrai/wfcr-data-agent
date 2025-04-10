FROM us-central1-docker.pkg.dev/gcp-wow-food-fco-auto-dev/wfcrai-agents/wfcrai-agent-utils:latest

# Install Uvicorn
RUN uv pip install --no-cache-dir uvicorn --system

COPY . /app
WORKDIR /app

RUN uv sync
RUN . /app/.venv/bin/activate

# Install the agent-utils package
RUN uv pip install $AGENT_UTILS_PACKAGE
#Ensure the agent-utils package is installed correctly
RUN uv pip show wfcrai-agent-utils 

EXPOSE 8000


# Set the entrypoint so that additional arguments passed at runtime are appended
# ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
ENTRYPOINT ["/app/.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD []