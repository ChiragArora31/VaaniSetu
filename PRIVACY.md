# Privacy and Data Handling

VaaniSetu processes normal jobs on the configured worker. Hosted translation is disabled by default and must remain disabled for BAIF production. Runtime logs contain event metadata, status, timings, and identifiers—not raw source or translated text by design.

Uploaded temporary files and completed outputs remain on the worker until deleted/cleaned. Administrators must apply BAIF retention, access-control, backup encryption, and physical-security policies. Do not use real beneficiary data in public demos, Git, benchmarks, screenshots, or support tickets. Treat voice, names, health information, and location data as confidential.

The privacy-safe support bundle intentionally excludes auth data, job content/artifacts, model weights, log messages, and exception traces. Review any diagnostic bundle before it leaves BAIF control.
