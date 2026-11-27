#!/usr/bin/env python3
"""Launch one GPU instance for an LLM benchmark run, via boto3 (host instance role).

Adapted from oss-image-models-lab/scripts/launch.py. Differences:
  * own Name tag / key pair / security group, so it never touches other runs;
  * SSH key and launch.json live in a STABLE dir (~/.oss-llm-bench), not $KIROCREW_SCRATCH;
  * SSH ingress limited to this host's public IP;
  * AMI = Deep Learning Base OSS Nvidia Driver GPU AMI (Ubuntu 24.04): recent driver + Docker,
    needed by the CUDA 12.9/13 framework images.

Usage: python scripts/launch.py --name oss-llm-bench-qwen27b [--type g6e.xlarge] [--disk 200]
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request

import boto3

REGION_PLAN = {  # g6e capacity was found in Tokyo by the image repo; others as fallback
    "ap-northeast-1": ["ap-northeast-1a", "ap-northeast-1c", "ap-northeast-1d"],
    "us-west-2": ["us-west-2a", "us-west-2b", "us-west-2c", "us-west-2d"],
    "us-east-1": ["us-east-1a", "us-east-1b", "us-east-1c", "us-east-1d"],
}
AMI_SSM = "/aws/service/deeplearning/ami/x86_64/base-oss-nvidia-driver-gpu-ubuntu-24.04/latest/ami-id"
KEY = "oss-llm-bench-key"
SG = "oss-llm-bench-sg"
STATE_DIR = os.path.expanduser("~/.oss-llm-bench")
KEYFILE = os.path.join(STATE_DIR, "ssh_key")


def ensure_local_key():
    os.makedirs(STATE_DIR, mode=0o700, exist_ok=True)
    if not os.path.exists(KEYFILE):
        subprocess.run(["ssh-keygen", "-t", "ed25519", "-N", "", "-f", KEYFILE, "-q"], check=True)
    return open(KEYFILE + ".pub").read().strip()


def my_ip():
    return urllib.request.urlopen("https://checkip.amazonaws.com", timeout=10).read().decode().strip()


def setup_region(ec2, pub, cidr):
    try:
        ec2.import_key_pair(KeyName=KEY, PublicKeyMaterial=pub.encode())
    except Exception:
        pass  # already imported
    vpc = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])["Vpcs"][0]["VpcId"]
    found = ec2.describe_security_groups(Filters=[{"Name": "group-name", "Values": [SG]},
                                                  {"Name": "vpc-id", "Values": [vpc]}])["SecurityGroups"]
    sg = found[0]["GroupId"] if found else ec2.create_security_group(
        GroupName=SG, Description="oss llm bench (ssh from bench host only)", VpcId=vpc)["GroupId"]
    try:
        ec2.authorize_security_group_ingress(GroupId=sg, IpPermissions=[
            {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "IpRanges": [{"CidrIp": cidr}]}])
    except Exception:
        pass  # rule exists
    return sg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="Name tag, e.g. oss-llm-bench-qwen27b")
    ap.add_argument("--type", default="g6e.xlarge")
    ap.add_argument("--disk", type=int, default=200, help="root gp3 GB")
    a = ap.parse_args()
    pub = ensure_local_key()
    cidr = my_ip() + "/32"
    for region, azs in REGION_PLAN.items():
        ec2 = boto3.client("ec2", region_name=region)
        ami = boto3.client("ssm", region_name=region).get_parameter(Name=AMI_SSM)["Parameter"]["Value"]
        sg = setup_region(ec2, pub, cidr)
        for az in azs:
            try:
                r = ec2.run_instances(
                    ImageId=ami, InstanceType=a.type, KeyName=KEY, SecurityGroupIds=[sg],
                    MinCount=1, MaxCount=1, Placement={"AvailabilityZone": az},
                    InstanceInitiatedShutdownBehavior="terminate",
                    BlockDeviceMappings=[{"DeviceName": "/dev/sda1", "Ebs": {
                        "VolumeSize": a.disk, "VolumeType": "gp3", "Throughput": 500, "Iops": 6000,
                        "DeleteOnTermination": True}}],
                    TagSpecifications=[{"ResourceType": "instance", "Tags": [
                        {"Key": "Name", "Value": a.name}, {"Key": "project", "Value": "oss-llm-models-lab"}]}])
            except Exception as e:
                print(f"{az}: {type(e).__name__}: {str(e)[:80]}")
                continue
            iid = r["Instances"][0]["InstanceId"]
            ec2.get_waiter("instance_running").wait(InstanceIds=[iid])
            d = ec2.describe_instances(InstanceIds=[iid])["Reservations"][0]["Instances"][0]
            info = {"name": a.name, "region": region, "az": az, "iid": iid, "type": a.type,
                    "ip": d.get("PublicIpAddress"), "ami": ami, "sg": sg, "keyfile": KEYFILE,
                    "launch_time": d["LaunchTime"].isoformat()}
            json.dump(info, open(os.path.join(STATE_DIR, f"{a.name}.json"), "w"), indent=2)
            print(json.dumps(info))
            return
    sys.exit("no capacity in any region/AZ tried")


if __name__ == "__main__":
    main()
