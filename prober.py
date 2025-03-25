#!/usr/bin/env python3

import time
import threading
import requests
import yaml
from prometheus_client import start_http_server, Counter, Histogram
import logging
import signal

shutdown_event = threading.Event()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

# A counter for request attempts, labeled by endpoint and status code.
REQUEST_COUNT = Counter(
    'synthetic_requests_total',
    'Counts synthetic HTTP request attempts by endpoint and status code',
    ['endpoint', 'status_code', 'url']
)

# A histogram for request durations, labeled by endpoint and status code.
REQUEST_DURATION = Histogram(
    'synthetic_request_duration_seconds',
    'Histogram of synthetic request durations in seconds',
    ['endpoint', 'status_code', 'url']
)

def probe_endpoint(endpoint):
    """
    Periodically send an HTTP GET to the endpoint URL. Update both
    the request counter and the duration histogram.
    """
    name = endpoint.get('name', endpoint['url'])
    url = endpoint['url']
    interval = endpoint.get('interval', 60)
    timeout = endpoint.get('timeout', 10)
    logging.info(f"Probing {url} ({name}) every {interval} seconds with a timeout of {timeout} seconds...")

    while not shutdown_event.is_set():
        logging.info(f"Probing {url} ({name})...")
        start_time = time.monotonic()
        try:
            response = requests.get(url, timeout=timeout)
            duration = time.monotonic() - start_time

            # Record the duration and status code
            REQUEST_DURATION.labels(endpoint=name, url=url,
                                    status_code=str(response.status_code)).observe(duration)
            REQUEST_COUNT.labels(endpoint=name, url=url,
                                 status_code=str(response.status_code)).inc()
        except Exception as e:
            logging.error(f"Error probing {url} ({name}): {e}")
            duration = time.monotonic() - start_time
            REQUEST_DURATION.labels(endpoint=name, url=url, status_code='error').observe(duration)
            REQUEST_COUNT.labels(endpoint=name, url=url, status_code='error').inc()

        time.sleep(interval)

    logging.info(f"Shutting down probe for {url} ({name})")

def main():
    def shutdown_handler(signum, frame):
        logging.info("Shutting down gracefully...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # Load endpoints from config
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    endpoints = config.get('endpoints', [])
    if not endpoints:
        logging.error("No endpoints defined in config.yaml. Exiting.")
        return

    # Start an HTTP server to expose Prometheus metrics
    start_http_server(8000)
    logging.info("Exporter running on port 8000...")

    # For each endpoint, start a background thread that probes it
    threads = []
    for endpoint in endpoints:
        t = threading.Thread(target=probe_endpoint, args=(endpoint,), daemon=True)
        t.start()
        threads.append(t)

    # Wait for all probe threads to finish (they won't unless interrupted)
    for t in threads:
        t.join()

if __name__ == '__main__':
    main()
