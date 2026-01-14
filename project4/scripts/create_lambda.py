import argparse

import boto3


def get_clients(region: str, profile: str | None = None):
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    return {
        "lambda": session.client("lambda", region_name=region),
        "ecr": session.client("ecr", region_name=region),
        "sts": session.client("sts"),
    }


def get_latest_image(ecr_client, sts_client, repository_name: str, region: str) -> dict:
    account_id = sts_client.get_caller_identity()["Account"]

    response = ecr_client.describe_images(repositoryName=repository_name)
    images = response["imageDetails"]
    latest_image = max(images, key=lambda x: x["imagePushedAt"])

    image_tags = latest_image.get("imageTags", [])
    image_digest = latest_image["imageDigest"]

    if image_tags:
        image_tag = image_tags[0]
        image_uri = (
            f"{account_id}.dkr.ecr.{region}.amazonaws.com/{repository_name}:{image_tag}"
        )
    else:
        image_uri = f"{account_id}.dkr.ecr.{region}.amazonaws.com/{repository_name}@{image_digest}"

    return {
        "imageDigest": image_digest,
        "imageTags": image_tags,
        "pushedAt": latest_image["imagePushedAt"],
        "imageUri": image_uri,
    }


def create_lambda_function(
    lambda_client,
    function_name: str,
    image_uri: str,
    role_arn: str,
    timeout: int,
    memory_size: int,
    architecture: str,
) -> dict:
    response = lambda_client.create_function(
        FunctionName=function_name,
        Role=role_arn,
        Code={"ImageUri": image_uri},
        PackageType="Image",
        Architectures=[architecture],
        Publish=True,
        Timeout=timeout,
        MemorySize=memory_size,
    )
    print(f"Lambda function '{function_name}' created.")
    return response


def main():
    parser = argparse.ArgumentParser(
        description="Create AWS Lambda function from ECR image"
    )
    parser.add_argument(
        "--function-name",
        type=str,
        required=True,
        help="Name of the Lambda function to create",
    )
    parser.add_argument(
        "--repository-name",
        type=str,
        required=True,
        help="Name of the ECR repository",
    )
    parser.add_argument(
        "--role-arn",
        type=str,
        required=True,
        help="IAM Role ARN for the Lambda function",
    )
    parser.add_argument(
        "--region",
        type=str,
        default="eu-west-2",
        help="AWS region (default: eu-west-2)",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default=None,
        help="AWS profile name (default: uses default profile)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Lambda function timeout in seconds (default: 10)",
    )
    parser.add_argument(
        "--memory-size",
        type=int,
        default=1024,
        help="Lambda function memory size in MB (default: 1024)",
    )
    parser.add_argument(
        "--architecture",
        type=str,
        choices=["x86_64", "arm64"],
        default="arm64",
        help="Lambda function architecture (default: arm64)",
    )
    args = parser.parse_args()

    clients = get_clients(args.region, args.profile)

    latest_image = get_latest_image(
        clients["ecr"], clients["sts"], args.repository_name, args.region
    )
    print(f"Latest Image Digest: {latest_image['imageDigest']}")
    print(f"Tags: {latest_image['imageTags']}")
    print(f"Uploaded At: {latest_image['pushedAt']}")
    print(f"Image URI: {latest_image['imageUri']}")

    create_lambda_function(
        clients["lambda"],
        args.function_name,
        latest_image["imageUri"],
        args.role_arn,
        args.timeout,
        args.memory_size,
        args.architecture,
    )


if __name__ == "__main__":
    main()
