FROM python:3.13-slim

# Install urirun from the LOCAL source wheel (the published PyPI build lags the
# mesh/key-auth code under audit). Build it first: cd adapters/python && python -m build --wheel
COPY urirun-*.whl /tmp/
RUN pip install --no-cache-dir /tmp/urirun-*.whl cryptography

WORKDIR /app
COPY node.bindings.json probe.py /app/
RUN urirun compile node.bindings.json --out node.registry.json

EXPOSE 8765

# Deliberately PERMISSIVE node to exercise the attack surface:
#   --execute        run routes for real (not dry-run)
#   --allow 'demo://*'  broad allow INCLUDING the command route (the risky case)
#   --key-auth       enrollment + signed /deploy enabled
# A hardened node would scope --allow to query routes only and front this with TLS.
CMD ["sh", "-c", "urirun node serve --registry node.registry.json --host 0.0.0.0 --port 8765 --execute --allow 'demo://*' --key-auth"]
