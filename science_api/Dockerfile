FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app/science_api
RUN apt-get update && apt-get install -y --no-install-recommends libgdal-dev g++ && rm -rf /var/lib/apt/lists/*
COPY science_api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY science_api/ ./
COPY scripts/ /app/scripts/
EXPOSE 8000
# Do not gate startup on NASA network downloads: Site01 rasters are already bundled.
# Perform extra dataset ingestion explicitly using /app/scripts/download_science_data.py.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
