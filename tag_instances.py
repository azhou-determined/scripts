import argparse
from enum import Enum
from typing import Dict, List, Tuple

import boto3
import googleapiclient.discovery

TAGS = {
    # Functional team tags
    "det-group": ["mlgroup"]
}


class TagType(Enum):
    GROUP = "det-group"


def main():
    return


def tag_aws_instances(keypair: str, tags: List[Tuple]):
    client = boto3.client("ec2")
    for region in client.describe_regions()["Regions"]:
        region_name = region["RegionName"]

        conn = boto3.resource("ec2", region_name=region_name)
        instances = conn.instances.all()
        for instance in instances:
            if instance.state["Name"] == "running" and instance.key_name == keypair:
                aws_tags = [get_aws_tag(tag_key, tag_value) for (tag_key, tag_value) in tags]
                tag = instance.create_tags(
                    DryRun=False,
                    Tags=aws_tags
                )
                print(f"Added tag {tag} for {instance.id} (keypair: {instance.key_name})")


def get_aws_tag(key: str, value: str):
    tag = {
        "Key": key,
        "Value": value
    }
    return tag


def find_and_tag_gcp_instances(query: str, tags: List[Tuple]):
    instances = find_gcp_instances(query)
    selected = []
    for i in instances:
        if query in i["name"]:
            confirm = input(f"Set tags on instance {i['name']}? [y/n]")
            if confirm.upper() == "Y":
                selected.append(i)
    update_gcp_instances_labels(selected, dict(tags))


def update_gcp_instances_labels(instances, labels: Dict):
    compute = googleapiclient.discovery.build("compute", "v1")
    project = "determined-ai"
    for instance in instances:
        instance.get("labels", {}).update(labels)
        request_body = {
            "labels": labels,
            "labelFingerprint": instance["labelFingerprint"]
        }
        zone = instance["zone"].split("/")[-1]
        request = compute.instances().setLabels(project=project,
                                                zone=zone,
                                                instance=instance["name"],
                                                body=request_body)
        response = request.execute()
        print(f"Set tags {labels} on {instance['name']}")


def find_gcp_instances(query: str):
    compute = googleapiclient.discovery.build("compute", "v1")
    project = "determined-ai"
    request = compute.instances().aggregatedList(project=project)
    found = []
    while request is not None:
        response = request.execute()
        instances = response.get("items", {})
        for instance in instances.values():
            for i in instance.get("instances", []):
                if query in i["name"]:
                    found.append(i)
        request = compute.instances().aggregatedList_next(previous_request=request, previous_response=response)
    return found


def parse_tags(tags_str: str):
    tags = [tuple(tag.split("=")) for tag in tags_str.split(",")]
    return tags


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("provider")
    parser.add_argument("--keypair")
    parser.add_argument("--query")
    parser.add_argument("--group")
    parser.add_argument("--tags")
    args = parser.parse_args()
    assert args.group or args.tags, "No tags specified"

    tags = parse_tags(args.tags or "")
    if args.group:
        assert args.group in TAGS[TagType.GROUP.value], f"{args.group} not in recognized group tags"
        tags.append((TagType.GROUP.value, args.group))

    if args.provider == "gcp":
        assert args.query, "Must specify a search query for GCP"
        find_and_tag_gcp_instances(args.query, tags)
    elif args.provider == "aws":
        assert args.keypair, "Keypair argument required"
        tag_aws_instances(args.keypair, tags)