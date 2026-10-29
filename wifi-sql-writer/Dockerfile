FROM python:3.14.9-slim-bookworm@sha256:945c2676dc2b18e0c1f16879244122c57c0ffede60006bf3df159c507a31bcae AS wheels
RUN apt-get update && apt-get install -y --no-install-recommends gcc libmariadb-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.14.9-slim-bookworm@sha256:945c2676dc2b18e0c1f16879244122c57c0ffede60006bf3df159c507a31bcae
RUN apt-get update && apt-get install -y --no-install-recommends libmariadb3 ca-certificates && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 dms && useradd --uid 10001 --gid 10001 --no-create-home dms
COPY --from=wheels /wheels /wheels
RUN pip install --no-cache-dir --no-index /wheels/*.whl && rm -rf /wheels
WORKDIR /app
COPY wifi_sqlwriter.py .
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
USER 10001:10001
ENTRYPOINT ["python3", "wifi_sqlwriter.py"]
