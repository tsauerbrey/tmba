# ADR-0016: First bootable TMBA-OS runtime

- Status: Accepted
- Date: 2026-07-26

## Context

The reproducible pi-gen builder existed, but the target image did not yet guarantee a valid runtime configuration, diagnostics, or an observable backend startup.

## Decision

The image installs application code and configuration below `/opt/tmba`, creates a dedicated Python virtual environment, starts the backend through systemd, records hardware and boot diagnostics, and verifies the HTTP health endpoint after startup.

## Consequences

The first Raspberry Pi test can distinguish build, configuration, hardware, service, and API failures using systemd and `/var/log/tmba`. The UI remains outside this milestone.
