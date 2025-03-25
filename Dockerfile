FROM bitnami/python:3.13.2

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY prober.py /app/prober.py
COPY config/config.yaml /app/config/config.yaml

EXPOSE 8000

ENTRYPOINT ["python3"]
CMD ["prober.py"]