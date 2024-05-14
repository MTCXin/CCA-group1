import docker
import time
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
cpu_quota = 50000

# Start the container
container = client.containers.run(
    image,
    command,
    cpuset_cpus=cpuset_cpus,
    name=container_name,
    detach=detach,
    remove=remove,
    cpu_quota=cpu_quota
)

# Print container ID
print("Container ID:", container.id)
while True:
    # Get the container
    container = client.containers.get(container.id)

    # Check the status
    if container.status == "exited":
        print("completed")
        break
    else:
        print("pending")
        time.sleep(30)
