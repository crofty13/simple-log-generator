# Simple log generator for Elastic

This project emits fake furniture-checkout events as JSON lines. It is meant for demos with Elastic Cloud: stdout logs you can collect from Kubernetes, or a direct send to Elastic Streams over the Managed OTLP **logs-otel** endpoint.

`log_generator_clean.py` is the version in git. Keep real cluster URLs and API keys in a local `log_generator.py` (that file is gitignored) or in environment variables.

## Python libraries

The generator uses only the Python 3 standard library. There is nothing to `pip install`.

You do need:

- Python 3
- `curl` on `PATH` (used to POST each batch to Elastic)

## Variables you need to set

Edit the constants at the top of `log_generator_clean.py`, or export the API key:

| Variable | Required | What to set |
| --- | --- | --- |
| `ELASTIC_OTLP_LOGS_URL` | Yes | Managed OTLP logs URL: `https://<your-deployment>.ingest.<region>.gcp.elastic-cloud.com/v1/logs` |
| `ELASTIC_API_KEY` | Yes | Elastic API key with permission to write OTLP/Streams data (`event:write` for Managed OTLP). Prefer `export ELASTIC_API_KEY='...'` instead of hardcoding. |
| `OTEL_SERVICE_NAME` | No | Defaults to `checkout`. Shown as `service.name` on the documents. |
| `OTEL_INDEX` | No | Defaults to `logs.otel`, the Elastic **9.4** Streams wired endpoint. Do not set this to a custom data-stream dataset name if you want events in Streams **logs-otel**. |

Find the ingest host in Elastic Cloud: **Manage deployment → Application endpoints → Managed OTLP**. Append `/v1/logs`. In Kibana, create an API key from **Add data → Applications → OpenTelemetry**, or from Stack Management.

On Elastic 9.4.x, native Elasticsearch `/_otlp/v1/logs` is not available. Use the Managed OTLP `/v1/logs` path and route with `elasticsearch.index=logs.otel`.

## Run locally

```bash
export ELASTIC_API_KEY='your-api-key'
# Also set ELASTIC_OTLP_LOGS_URL in the script to your cluster
python3 -u log_generator_clean.py
```

Every ~10 seconds it prints JSON checkout lines and POSTs that batch to Elastic. In Kibana, open **Streams** and look at `logs.otel`.

## Deploy on Kubernetes

1. Put your URL and API key into the image you build (or pass `ELASTIC_API_KEY` as a secret/env var).
2. Build and load the image, then apply `deployment.yml`:

```bash
docker build -t log-generator:v5 .
kubectl apply -f deployment.yml
kubectl logs -l app=checkout
```

`deployment.yml` currently runs `log-generator:v5` with `imagePullPolicy: IfNotPresent`. The Elastic pod annotations are for Elastic Agent container-log collection. For Streams over OTLP, the script still needs a reachable Managed OTLP URL and API key inside the container.
