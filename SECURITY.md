# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.x (latest) | ✅ Active |

RealDataAgentBench is pre-1.0 software. Security fixes are applied to the latest
release only.

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Report security issues privately by emailing:

> venkatamanideep20@gmail.com

Include in your report:
- A description of the vulnerability and its potential impact
- Steps to reproduce or a proof-of-concept (if safe to share)
- Affected version(s)
- Any suggested fix (optional but appreciated)

You can expect an acknowledgement within **48 hours** and a resolution plan
within **7 days**. We will credit researchers who responsibly disclose issues
(unless they prefer to remain anonymous).

## Scope

| Area | In Scope |
|------|----------|
| Code execution sandbox (`harness/tools.py`) | ✅ High priority |
| API key handling / environment variable leakage | ✅ High priority |
| Dependency vulnerabilities | ✅ |
| CLI input validation | ✅ |
| GitHub Actions workflows | ✅ |

## API Key Safety

RealDataAgentBench reads API keys exclusively from environment variables (via
`.env` file or shell environment). Keys are **never** hardcoded in source code.

When setting up the project:
1. Copy `.env.example` to `.env`
2. Fill in your keys — **never commit `.env` to version control**
3. The `.gitignore` already excludes `.env` and `*.env`

If you believe an API key has been accidentally committed to this repository,
please report it immediately so it can be revoked.

## Code Execution Sandbox

The `run_code` tool executes arbitrary Python provided by LLM agents inside a
restricted namespace. The sandbox:
- Pre-imports only `numpy`, `pandas`, `scipy.stats`, and `sklearn`
- Blocks direct `import` statements via `__import__` removal
- Does **not** provide network or filesystem access

This sandbox is designed for benchmarking purposes only. Do not expose
`run_code` to untrusted input in a production environment without additional
hardening (e.g., process isolation, seccomp filters, container sandboxing).
