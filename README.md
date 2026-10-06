# Resilient Hospital IT: Reference Architecture

![tests](https://github.com/aadirani/hospital-it-resilience/actions/workflows/tests.yml/badge.svg)

How should a public hospital design its IT when the **grid fails every day, the internet is weak, and the budget is small**?

This repository is a **generic reference architecture** for that situation. It does not describe any real hospital's setup.

## The idea in one paragraph

Run clinical systems **inside the hospital** so they keep working without the internet. Protect them with an **online UPS that bridges the gap until the generator starts**. Keep **two servers** so one can fail. Separate the network into **zones** so one infected PC can't reach everything. Keep **three copies of the data**, one off-site and one offline, and **test restoring them every month**. Use the internet for backups, email and vendor support, never for treating patients.

## What's inside

| File | What it is |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | The full design: diagrams, recovery targets, 6 decision records (ADRs), risk register, cost model, rollout phases |
| [docs/runbooks.md](docs/runbooks.md) | Short checklists for power loss, internet loss, server failure and ransomware |
| [tools/ups_runtime.py](tools/ups_runtime.py) | A small calculator that sizes the UPS battery for the server room |
| [docs/code-walkthrough.md](docs/code-walkthrough.md) | Plain-language explanation of the calculator |
| [data/sample_load.csv](data/sample_load.csv) | Example (synthetic) list of server-room devices and their power draw |

## Why a calculator?

The most common power question in a setting like this is: *"Will the UPS battery last until the generator takes over, and if the generator fails, is there time to shut down safely?"* The calculator answers it from a simple list of devices.

```bash
python tools/ups_runtime.py --load-csv data/sample_load.csv --voltage 48 --capacity-ah 100 --target-minutes 15 --generator-start-seconds 60
```

Example output:

```
Total load:            1,610 W
Suggested UPS rating:  2,236 VA
Usable battery energy: 2,765 Wh (lifepo4)
Estimated runtime:     103.0 min
Needed for 15 min:    15 Ah at 48 V
Target met:            YES
Generator bridge:      OK (6,122 s spare)
```

Needs Python 3.9+ and nothing else. Run the tests with:

```bash
python -m unittest discover -s tests -v
```

## Key decisions at a glance

1. **Local-first:** clinical systems run on-site, and the cloud holds only backup copies.
2. **UPS for minutes, generator for hours:** the battery covers the generator start and a safe shutdown.
3. **Two servers with replication** instead of expensive shared storage.
4. **3-2-1-1-0 backups**, with the backup server isolated from the main network accounts.
5. **Cellular internet failover**, kept away from the clinical critical path.
6. **Network zones (VLANs)** with a firewall between them. Medical devices get their own zone.

Details and the alternatives considered are in [ARCHITECTURE.md](ARCHITECTURE.md#6-architecture-decision-records).

## Limitations

- All loads, sizes and prices are planning assumptions. Confirm them with vendors and site surveys.
- The calculator uses a simple energy model. It ignores effects like the faster capacity loss of lead-acid batteries at high discharge rates, so treat its runtime as an upper estimate and add a margin.

---

Built with AI assistance.
