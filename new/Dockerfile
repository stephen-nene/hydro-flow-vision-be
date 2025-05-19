FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --upgrade pip && pip install uv

# Copy dependency files first (to cache this layer)
COPY pyproject.toml uv.lock ./

# Install Python dependencies directly (no virtual env needed in container)
RUN uv pip install --no-cache-dir -e .

# Verify Django is installed
RUN python -c "import django; print(f'Django version: {django.__version__}')"

# Copy the rest of the project
COPY . .

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD ["bash", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]