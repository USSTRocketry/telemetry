import argparse
import redis
import time
import json

r = redis.Redis(host='localhost', port=6379, decode_responses=True)
TASKS_KEY = "gs:tasks"

def push_task(task_name, params):
    task = {
        "task": task_name,
        "params": params,
        "timestamp": time.time(),
    }
    r.rpush(TASKS_KEY, json.dumps(task))
    print(f"Pushed task: {task_name} with params: {params}")

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

    args = parser.parse_args()

    # Map CLI commands to task format
    if args.command == "change_freq":
        push_task("change_frequency", {"frequency": args.frequency})
    elif args.command == "force_ground_freq":
        push_task("force_ground_frequency", {"frequency": args.frequency})
    elif args.command == "send_flight_ready":
        push_task("send_flight_ready", {})
    elif args.command == "set_gs_id":
        push_task("set_ground_station_id", {"id": args.id})
    elif args.command == "set_rocket_id":
        push_task("set_rocket_id", {"id": args.id})
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
