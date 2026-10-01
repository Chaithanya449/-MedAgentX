FROM python:3.11-slim

# Basic Python container settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install the exact application dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy the existing MedAgentX project without changing its structure
COPY . .

# FastAPI + Streamlit
EXPOSE 8000
EXPOSE 8501

# Run both existing application components in the same container.
# FastAPI remains available on localhost:8000 for Streamlit,
# while Streamlit is exposed on port 8501.
CMD ["bash", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port 8000 & backend_pid=$!; streamlit run frontend/streamlit_app.py --server.address=0.0.0.0 --server.port=8501 & frontend_pid=$!; wait -n $backend_pid $frontend_pid; status=$?; kill $backend_pid $frontend_pid 2>/dev/null || true; wait 2>/dev/null || true; exit $status"]
