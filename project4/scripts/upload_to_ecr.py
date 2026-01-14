import argparse
from pathlib import Path

import boto3
import docker
import subprocess


def get_ecr_client(region: str, profile: str | None = None):
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    return session.client("ecr", region_name=region)


def create_or_get_ecr_repository(ecr_client, repository_name: str) -> str:
    try:
        response = ecr_client.create_repository(repositoryName=repository_name)
        print(f"Repository {repository_name} created.")
        repository_uri = response["repository"]["repositoryUri"]
    except ecr_client.exceptions.RepositoryAlreadyExistsException:
        print(f"Repository {repository_name} already exists.")
        response = ecr_client.describe_repositories(repositoryNames=[repository_name])
        repository_uri = response["repositories"][0]["repositoryUri"]
    return repository_uri


def authenticate_ecr(ecr_client, region: str, profile: str | None = None) -> None:
    token = ecr_client.get_authorization_token()["authorizationData"][0]
    ecr_url = token["proxyEndpoint"]
    print(f"ECR URL: {ecr_url}")
    profile_arg = f"--profile {profile} " if profile else ""
    login_command = f"aws ecr get-login-password {profile_arg}--region {region} | docker login --username AWS --password-stdin {ecr_url}"
    subprocess.run(login_command, shell=True, check=True)
    print("Docker authenticated with ECR")


def build_and_push_docker_image(
    docker_client, repository_uri: str, repository_name: str, image_tag: str, build_path: str
) -> None:
    print("Building Docker image:")
    docker_client.images.build(
        path=build_path,
        tag=f"{repository_name}:{image_tag}",
    )
    print("Docker image built successfully")

    full_image_name = f"{repository_uri}:{image_tag}"
    docker_client.images.get(f"{repository_name}:{image_tag}").tag(full_image_name)
    print(f"Tagged image: {full_image_name}")

    print("Pushing to ECR:")
    for line in docker_client.images.push(
        repository_uri, tag=image_tag, stream=True, decode=True
    ):
        print(line)


def main():
    parser = argparse.ArgumentParser(description="Build and push Docker image to AWS ECR")
    parser.add_argument(
        "--repository-name",
        type=str,
        required=True,
        help="Name of the ECR repository",
    )
    parser.add_argument(
        "--image-tag",
        type=str,
        default="latest",
        help="Docker image tag (default: latest)",
    )
    parser.add_argument(
        "--region",
        type=str,
        default="eu-west-2",
        help="AWS region (default: eu-west-2)",
    )
    parser.add_argument(
        "--build-path",
        type=str,
        default=str(Path(__file__).parents[1]),
        help="Path to the directory containing Dockerfile (default: project4 root)",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default=None,
        help="AWS profile name (default: uses default profile)",
    )
    args = parser.parse_args()

    ecr_client = get_ecr_client(args.region, args.profile)
    docker_client = docker.from_env()

    repository_uri = create_or_get_ecr_repository(ecr_client, args.repository_name)
    print(f"Repository URI: {repository_uri}")

    authenticate_ecr(ecr_client, args.region, args.profile)
    build_and_push_docker_image(
        docker_client, repository_uri, args.repository_name, args.image_tag, args.build_path
    )


if __name__ == "__main__":
    main()
