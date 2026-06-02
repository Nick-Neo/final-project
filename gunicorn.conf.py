"""Gunicorn config — initialize Azure Monitor / OpenTelemetry per worker.

OpenTelemetry's background export thread does not survive gunicorn's fork, so
configuring it at module import (in the master) leaves workers without a live
exporter. The `post_fork` hook runs inside each worker after the fork, so the
exporter thread is created in the right process and telemetry actually ships.

Only activates when APPLICATIONINSIGHTS_CONNECTION_STRING is set (cloud only);
local dev and CI are untouched.
"""

import os


def post_fork(server, worker):
    if os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"):
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor()
        server.log.info("Azure Monitor configured for worker pid %s", worker.pid)

 