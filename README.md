# Security-Aware Distributed System Incident Diagnosis

A proof-of-concept prototype developed for BCIT COMP 8800 — Major Project 1.

## Overview

Distributed applications can produce similar symptoms when failures originate from different causes. For example, an upstream service may return HTTP 502 because a dependent service has stopped running or because a network security policy prevents communication.

This prototype investigates whether evidence collected from multiple sources can distinguish between operational failures and network-security disruptions.

**Prototype research question:**

Can a lightweight evidence-correlation and rule-based diagnosis engine distinguish between operational service failures and network-security disruptions using application logs, health checks, container state, and network telemetry?

The prototype runs a two-service application using Docker Compose and processes incident evidence to generate ranked root-cause hypotheses.

## Architecture

The prototype contains:

- **Backend service:** An HTTP service providing application data and health checks.
- **Upstream service:** An HTTP service that requests data from the backend.
- **Docker Compose:** Runs the services on an isolated bridge network.
- **Evidence collection:** Captures HTTP responses, service health, container state, firewall counters, and application logs.
- **Correlation engine:** Associates application events using request IDs.
- **Diagnosis engine:** Evaluates the collected evidence using deterministic rules and produces ranked root-cause hypotheses.
- **Command-line interface:** Generates structured JSON diagnosis reports.

The diagnosis engine operates on captured evidence rather than continuously monitoring running services.

## Requirements

For evidence replay and automated tests:

- Linux, macOS, or Windows with a compatible Python environment
- Python 3.12 or later

For running the containerized application:

- Docker Engine
- Docker Compose v2
- Available localhost ports `18080` and `18081`

For reproducing the network-security experiment:

- Linux host
- `curl`
- `nsenter`
- `iptables`
- `sudo` privileges sufficient to modify firewall rules inside the isolated Docker container network namespace

The Docker images use `python:3.12-slim`.

The prototype's Python diagnosis modules use the Python standard library.

## Quick Start — Evidence Replay

Evidence replay is the simplest way to demonstrate the diagnosis engine and does not require running Docker containers.

From the project root, run:

```bash
python3 -m diagnosis tests/fixtures/operational
```

The highest-ranked hypothesis should have the cause:

`backend_unavailable`

Run the security incident:

```bash
python3 -m diagnosis tests/fixtures/security
```

The highest-ranked hypothesis should have the cause:

`network_policy_denial`

Both commands output JSON reports containing evidence records and ranked hypotheses.

Previously generated validation reports are available in:

- `validation/operational.json`
- `validation/security.json`

## Run the Containerized Application

Build and start the services:

```bash
docker compose up -d --build
```

Inspect container status:

```bash
docker compose ps
```

Check backend health:

```bash
curl http://127.0.0.1:18081/health
```

Check upstream health:

```bash
curl http://127.0.0.1:18080/health
```

Trigger a dependency request:

```bash
curl http://127.0.0.1:18080/request
```

Under normal operating conditions, the upstream service should communicate successfully with the backend.

## Network-Security Fault Experiment

The security experiment deliberately introduces a temporary firewall rule inside the upstream container's network namespace.

The rule blocks outgoing TCP communication to the backend on port 8080.

**Important:** Run this experiment only on an authorized local development environment.

First, ensure both services are running:

```bash
docker compose up -d --build
```

Then execute:

```bash
bash scripts/run_security_fault.sh
```

The script:

1. Identifies the upstream container's process and the backend's IP address.
2. Verifies that the upstream container uses a separate network namespace.
3. Inserts a targeted firewall DROP rule.
4. Captures firewall counters before and after an upstream request.
5. Records the upstream response and backend health.
6. Collects application logs.
7. Removes the experiment rule during cleanup.

Generated observations are written to:

`results/security-001/`

Run the diagnosis engine against the captured evidence:

```bash
python3 -m diagnosis results/security-001
```

The expected highest-ranked hypothesis is:

`network_policy_denial`

The experiment requires the default Compose project and container names defined in the repository.

## Operational Failure Experiment

The operational scenario represents a backend service failure.

Previously captured evidence is provided in:

`tests/fixtures/operational/`

Run:

```bash
python3 -m diagnosis tests/fixtures/operational
```

The expected highest-ranked hypothesis is:

`backend_unavailable`

The captured evidence includes an upstream HTTP 502 response, a failed backend health probe, an exited backend container, and related application logs.

A dedicated automated script for reproducing this fault is not currently included.

## Automated Tests

From the project root, run:

```bash
python3 -m unittest discover -s tests -v
```

The current test suite contains 19 tests covering evidence extraction, event correlation, container-state parsing, firewall-rule matching, and incident diagnosis.

## Prototype Validation Results

Two controlled incident scenarios were evaluated using previously captured evidence.

| Scenario | Expected top diagnosis | Observed top diagnosis | Result |
|---|---|---|---|
| Backend service failure | `backend_unavailable` | `backend_unavailable` | PASS |
| Network-security disruption | `network_policy_denial` | `network_policy_denial` | PASS |

Each generated report contained six evidence records.

The network-security scenario included these observations:

- Upstream HTTP response: `502`
- Backend healthy: `True`
- Increase in firewall DROP counter: `2`

The results demonstrate that the prototype correctly distinguishes the two recorded incidents.

These results do not establish accuracy across arbitrary distributed systems or previously unseen incident types.

## Limitations

- The prototype uses a small, controlled two-service application.
- Diagnosis is based on deterministic rules rather than machine-learning models.
- Only two incident scenarios have been formally evaluated.
- Evidence is processed in batches rather than through a live streaming pipeline.
- The network fault experiment requires Linux networking tools and privileged access.
- Some experiment scripts depend on the default Docker Compose container names.
- The prototype provides a command-line JSON interface rather than a graphical dashboard.

## Cleanup

Stop and remove the Docker Compose containers:

```bash
docker compose down
```

The generated files under `results/` remain available locally and are excluded from Git.

## Project Status

This repository contains a working COMP 8800 technical feasibility prototype with reproducible evidence fixtures, automated regression tests, and recorded diagnosis validation results.
