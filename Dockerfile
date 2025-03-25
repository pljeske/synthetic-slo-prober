FROM bitnami/python:3.13.2

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY --chown=65534:0 --chmod=550 prober.py /app/prober.py
COPY --chown=65534:0 --chmod=550 config/config.yaml /app/config/config.yaml

EXPOSE 8000

USER 65534:0

ENTRYPOINT ["python3"]
CMD ["prober.py"]
