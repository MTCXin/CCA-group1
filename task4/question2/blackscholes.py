import docker

# 创建Docker客户端
client = docker.from_env()

# 指定要运行的容器镜像
image = "anakli/cca:parsec_blackscholes"

# 定义容器启动参数
command = "./run -a run -S parsec -p blackscholes -i native -n 2"
cpuset_cpus = "0"
container_name = "parsec"
detach = True
remove = True

# 启动容器
container = client.containers.run(
    image,
    command,
    cpuset_cpus=cpuset_cpus,
    name=container_name,
    detach=detach,
    remove=remove
)

# 打印容器ID
print("Container ID:", container.id)
