set -e

if [ -z "${1}" ]; then
  echo "you must pass the name of an image (e.g. backend_base)"
  exit 1
fi

if [ -z "${2}" ]; then
  echo "you must pass a tag (e.g. the full git hash of source repo used to build this image)"
  exit 1
fi

# instead of imageTag="...", you can also pass imageDigest="sha256:..."
MANIFEST=$(aws ecr batch-get-image --repository-name ${1} --region us-west-2 --image-ids imageTag=${2} --query "images[].imageManifest" --output text)

if [ -z "${MANIFEST}" ]; then
  echo "no image for tag ${2}"
  exit 1
fi

aws ecr put-image --repository-name ${1} --region us-west-2 --image-tag latest --image-manifest "$MANIFEST"
