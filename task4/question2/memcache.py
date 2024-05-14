import docker

# Create Docker client
client = docker.from_env()

# Specify the container image to run
image = "anakli/memcached:t1"

# Define container startup parameters
command = "/bin/sh -c './memcached -t 1 -u memcache'"
container_name = "some-memcached"
detach = True
remove = True

# Start the container
container = client.containers.run(
    image,
    command=command,
    name=container_name,
    detach=detach,
    remove=remove,
    labels={"name": "some-memcached"}
)

# Print container ID
print("Container ID:", container.id)
