#!/usr/bin/env python3
import argparse
import sys
import urllib.error
import urllib.request


def request_once(url, timeout_seconds):
    with urllib.request.urlopen(url, timeout=timeout_seconds) as response:
        response.read()


def parse_args():
    parser = argparse.ArgumentParser(description="Run one batch of HTTP requests")
    parser.add_argument("--url", required=True)
    parser.add_argument("--requests", required=True, type=int)
    parser.add_argument("--timeout", type=float, default=5.0)
    return parser.parse_args()


def main():
    args = parse_args()
    successes = 0

    for _ in range(args.requests):
        try:
            request_once(args.url, args.timeout)
            successes += 1
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            continue
        except Exception:
            continue

    if successes == 0:
        raise SystemExit("no successful requests in batch")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        raise SystemExit(str(exc)) from exc
