FROM python:3-slim

WORKDIR /app
COPY log_generator_clean.py .

CMD ["python", "-u", "log_generator_clean.py"]
