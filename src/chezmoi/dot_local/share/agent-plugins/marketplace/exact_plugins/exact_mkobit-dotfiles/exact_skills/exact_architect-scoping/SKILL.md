---
name: architect-scoping
description: >-
  Use when sizing an assigned Docker Sandbox (SBX) work unit and checking the guest's scope and model limits.
---

# Architect scoping

Read the [assignment](../worker-handoff/references/assignment.md), project instructions, and current state.
Use the dependencies, risks, and acceptance criteria to select the smallest complete unit within the assignment.
Defer work outside that unit and record the decision through the project's existing mechanisms.

Keep the coordinator model fixed for the run.
Use only native subagent models and reasoning settings that the assignment and harness permit.
Do not start nested sandboxes or disable required checks.
If the guest lacks a required capability, record the evidence and report what is missing.
