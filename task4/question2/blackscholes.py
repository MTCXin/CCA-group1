import docker

# Create Docker client
client = docker.from_env()

# Specify the container image to run
image = "anakli/cca:parsec_blackscholes"

# Define container startup parameters
command = "./run -a run -S parsec -p blackscholes -i native -n 2"
cpuset_cpus = "0"
container_name = "parsec"
detach = True
remove = True

# Start the container
container = client.containers.run(
    image,
    command,
    cpuset_cpus=cpuset_cpus,
    name=container_name,
    detach=detach,
    remove=remove
)

# Print container ID
print("Container ID:", container.id)
