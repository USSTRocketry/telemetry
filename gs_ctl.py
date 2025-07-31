#!/usr/bin/env python3


import argparse
import redis
import time
import json
from gs_data.data import TelemetryDataProcess

r = redis.Redis(host='localhost', port=6379, decode_responses=True)
TASKS_KEY = "gs:tasks"

def push_task_wait_response(task_name, params, timeout=5.0):
    task_id = str(time.time())  # Epoch time as task ID
    task = {
        "task_id": task_id,
        "task": task_name,
        "params": params
    }

    # Push task
    r.rpush(TASKS_KEY, json.dumps(task))

    # Wait for response
    response_key = f"gs:response:{task_id}"
    start = time.time()
    while time.time() - start < timeout:
        response = r.get(response_key)
        if response:
            r.delete(response_key)
            print(f"[RESPONSE] {response}")
            return
        time.sleep(0.1)

    print("[ERROR] No response received (timeout)")

def main():
    parser = argparse.ArgumentParser(description="Ground Station Control Commands")

    subparsers = parser.add_subparsers(dest="command")

    # Change frequency
    freq_cmd = subparsers.add_parser("change_freq")
    freq_cmd.add_argument("frequency", type=float, help="Frequency in MHz")

    # Force local frequency
    force_cmd = subparsers.add_parser("force_ground_freq")
    force_cmd.add_argument("frequency", type=float, help="Local frequency override")

    # Flight ready
    flight_cmd = subparsers.add_parser("send_flight_ready")

    # Set ground ID
    gid_cmd = subparsers.add_parser("set_gs_id")
    gid_cmd.add_argument("id", type=int, help="New ground station ID")

    # Set rocket ID
    rid_cmd = subparsers.add_parser("set_rocket_id")
    rid_cmd.add_argument("id", type=int, help="New rocket ID")

    # Run telemetry daemon command
    telemetry_cmd = subparsers.add_parser("telemetry_daemon", help="Run telemetry daemon")

    args = parser.parse_args()

    # Map CLI commands to task format
    if args.command == "change_freq":
        push_task_wait_response("change_frequency", {"frequency": args.frequency})
    elif args.command == "force_ground_freq":
        push_task_wait_response("force_ground_frequency", {"frequency": args.frequency})
    elif args.command == "send_flight_ready":
        push_task_wait_response("send_flight_ready", {})
    elif args.command == "set_gs_id":
        push_task_wait_response("set_ground_station_id", {"id": args.id})
    elif args.command == "set_rocket_id":
        push_task_wait_response("set_rocket_id", {"id": args.id})
    elif args.command == "telemetry_daemon":
        print("Starting telemetry daemon...")
        telemetry_process = TelemetryDataProcess()
        telemetry_process.start()
        try:
            while telemetry_process.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping telemetry daemon...")
            telemetry_process.terminate()
            telemetry_process.join()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
