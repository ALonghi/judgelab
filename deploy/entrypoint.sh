#!/bin/sh
set -eu
mkdir -p /data/practice
chown learner:learner /data/practice
# Drop root before serving HTTP or executing trusted learner submissions.
exec su -s /bin/sh learner -c 'exec python /app/run.py --hosted --no-browser --port 8080 --state-dir /data/practice'
