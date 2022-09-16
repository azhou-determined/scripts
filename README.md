## Usage

Requires google-cloud-compute and boto3 libraries.
```
pip install google-cloud-compute
pip install boto3
```

### AWS
```
python3 tag_instances.py aws --keypair anda-determined --tags tag1=test1,tag2=test2 --group mlgroup
```
- keypair is required for finding instances
- tags must be a comma/equals delimited string
- group is optional, will automatically add a det-group label for convenience

### GCP
```
python3 tag_instances.py gcp --query anda --tags tag1=test1,tag2=test2 --group mlgroup
```
- query is required and will do a simple substring match on all instance names
- script will ask for confirmation on which instances to tag since the match is not 100% accurate
- tags must be a comma/equals delimited string
- group is optional, will automatically add a det-group label for convenience

