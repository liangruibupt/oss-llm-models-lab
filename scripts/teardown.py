#!/usr/bin/env python3
"""Terminate ONLY the instance this repo launched (read from ~/.oss-llm-bench/<name>.json).

Refuses to act if the instance's Name tag does not match, so it can never terminate
another session's box. Then deletes this repo's key pair / security group if unused.

Usage: python scripts/teardown.py --name oss-llm-bench-qwen27b
"""
import argparse
import json
import os
import time

import boto3

KEY = "oss-llm-bench-key"
SG = "oss-llm-bench-sg"
STATE_DIR = os.path.expanduser("~/.oss-llm-bench")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    a = ap.parse_args()
    info = json.load(open(os.path.join(STATE_DIR, f"{a.name}.json")))
    iid, region = info["iid"], info["region"]
    ec2 = boto3.client("ec2", region_name=region)
    inst = ec2.describe_instances(InstanceIds=[iid])["Reservations"][0]["Instances"][0]
    tags = {t["Key"]: t["Value"] for t in inst.get("Tags", [])}
    if tags.get("Name") != a.name:
        raise SystemExit(f"refusing: {iid} Name tag is {tags.get('Name')!r}, expected {a.name!r}")
    print("state before:", inst["State"]["Name"], "launched", inst["LaunchTime"].isoformat())
    if inst["State"]["Name"] != "terminated":
        ec2.terminate_instances(InstanceIds=[iid])
        ec2.get_waiter("instance_terminated").wait(InstanceIds=[iid])
    inst = ec2.describe_instances(InstanceIds=[iid])["Reservations"][0]["Instances"][0]
    print("state after:", inst["State"]["Name"], inst.get("StateTransitionReason", ""))
    left = ec2.describe_instances(Filters=[
        {"Name": "tag:project", "Values": ["oss-llm-models-lab"]},
        {"Name": "instance-state-name", "Values": ["pending", "running", "stopping", "stopped"]}])
    remaining = [i["InstanceId"] for r in left["Reservations"] for i in r["Instances"]]
    print("remaining oss-llm-models-lab instances:", remaining or "NONE")
    if not remaining:
        try:
            ec2.delete_key_pair(KeyName=KEY)
            print("key pair deleted")
        except Exception as e:
            print("key:", str(e)[:80])
        for _ in range(6):
            try:
                ec2.delete_security_group(GroupId=info["sg"])
                print("sg deleted", info["sg"])
                break
            except Exception as e:
                print("sg:", str(e)[:80])
                time.sleep(10)


if __name__ == "__main__":
    main()
