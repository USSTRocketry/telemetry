#!/usr/bin/env python3

import argparse
import time
from multiprocessing import Process
from gs_data.data import TelemetryDataProcess
from common.redis_helper import TelemetryKeys

def run_data_test():
    print("[telemetry-ctl] Starting telemetry data test...")
    telemetry_process = TelemetryDataProcess()
    telemetry_process.start()

    try:
        while True:
            print("\033[2J\033[H", end="")  # clear terminal
            print(telemetry_process.db_str())
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[telemetry-ctl] Stopping telemetry test.")
        telemetry_process.terminate()
        telemetry_process.join()


def run_redis_test():
    print("[telemetry-ctl] Starting Redis telemetry test...")
    telemetry_process = TelemetryDataProcess()
    telemetry_process.start()

    try:
        redis = telemetry_process.redis_helper
        redis.redis.ping()  # sanity check
        print("[telemetry-ctl] Connected to Redis")

        while True:
            print("\033[2J\033[H", end="")  # clear terminal
            print("---- Latest Redis Telemetry ----")
            for key in TelemetryKeys.KEYS:
                try:
                    result = redis.ts_get_last(key)
                    if result:
                        timestamp, value = result
                        print(f"{key:20}: {value:>10} @ {timestamp}")
                    else:
                        print(f"{key:20}: No data")
                except Exception as e:
                    print(f"{key:20}: [ERR] {e}")
            print("--------------------------------")
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n[telemetry-ctl] Stopping Redis test.")
        telemetry_process.terminate()
        telemetry_process.join()
    except Exception as e:
        print(f"[telemetry-ctl] Redis error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Telemetry control CLI",
        prog="telemetry-ctl"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("run-test", help="Run telemetry data process and print output")
    subparsers.add_parser("redis-test", help="Run telemetry and show latest Redis values")

    args = parser.parse_args()

    if args.command == "run-test":
        run_data_test()
    elif args.command == "redis-test":
        run_redis_test()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
