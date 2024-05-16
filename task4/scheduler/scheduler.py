import psutil
import scheduler_logger as slogger
import subprocess
import sys
import docker
from time import sleep

# TODO find suitable values for these variables
MAX_LOAD_LOW = 2 # the max weight of jobs when memcached uses 2 cores
MAX_LOAD_HIGH = 4 # the max weight of jobs when memcached uses 1 core
CPU_THRESHOLD_1_CORE = 60 # CPU utilization threshold for switching from 1 to 2 cores
CPU_THRESHOLD_2_CORES = 100 # CPU utilization threshold for switching from 2 to 1 core
SLEEP_TIME = 0.5 # sleep time between two iterations of the main loop


class BatchJob(object):
    name = ""
    num_threads = 4 # default, can be overriden
    image = ""
    command = ""
    weight = 0 # how cpu intensive the job is
    container = None # will be set once the container has been created
    cores = [] # will be set when the job is started and is updated dynamically
    has_finished_ = False # will be set once the container finished and was removed

    def is_running(self):
        if self.container is None:
            return False
        self.container.reload()
        return self.container.status in ["created", "running", "restarting"]

    def has_finished(self):
        if self.container is None:
            return self.has_finished_
        self.container.reload()
        return self.container.status in ["exited"] 
    
    def is_newly_finished(self):
        return (not self.container is None) and self.container.status in ["exited"] 

    def is_paused(self):
        if self.container is None:
            return False
        self.container.reload()
        return self.container.status in ["paused"] 
    
    def is_new(self):
        return self.container is None and not self.has_finished_
    
    def reload_stats(self):
        if self.container is not None:
            self.container.reload()
    
    def get_status(self):
        if self.has_finished_:
            return "exited"
        if self.container is None:
            return "not started"
        self.container.reload()
        return self.container.status

    def __str__(self):
        return f"{self.name} ({self.image}): \n\tcores = {self.cores}\n\tcommand = {self.command}\n\tstatus = {self.get_status()}" 

    def start_job(self, docker_client, cpu_set, logger):
        self.cores = cpu_set
        container = docker_client.containers.run(cpuset_cpus=",".join([str(c) for c in cpu_set]),
                                               name=self.name,
                                               detach=True,
                                               auto_remove=False,
                                               image=self.image,
                                               command=self.command)
        logger.job_start(self.name, [str(c) for c in cpu_set], self.num_threads)
        print(f"Start {self}")
        self.container = container

    def pause_job(self, logger):
        if self.container is None:
            return False
        self.container.reload()
        if not self.is_running():
            print(f"WARN: Cannot pause {self.name} because job is not running.")
            return False
        try:
            self.container.pause()
            logger.job_pause(self.name)
            print(f"Pause {self}")
            return True
        except:
            print(f"ERROR: Could not pause job {self.name}")
            return False

    def unpause_job(self, logger):
        if self.container is None:
            return False
        self.container.reload()
        if not self.is_paused():
            print(f"WARN: Cannot unpause {self.name} because job is not paused.")
            return False
        try:
            self.container.unpause()
            logger.job_unpause(self.name)
            print(f"Unpause {self}")
            return True
        except:
            print(f"ERROR: Could not unpause job {self.name}")
            return False 
        
    def finish_job(self, logger):
        if not self.container is None:
            self.container.reload()
        if not self.has_finished():
            print(f"WARN: Cannot finish {self.name} because job is not done yet.")
            return False
        elif self.container is None: # job has been removed already
            return True
        else:
            try:
                self.container.reload()
                self.container.remove()
                logger.job_end(self.name)
                self.container = None
                self.has_finished_ = True
                print(f"Finished {self}")
                return True
            except:
                print(f"ERROR: Could not finish job {self.name}")
                return False

    def update_cores(self, cpu_set, logger):
        if self.container is None:
            return False
        self.container.reload()
        if self.container is None or self.has_finished():
            print(f"WARN: Cannot update {self.name} because job is not running.")
            return False

        self.container.update(cpuset_cpus=",".join([str(c) for c in cpu_set]))
        logger.update_cores(self.name, [str(c) for c in cpu_set])
        self.cores = cpu_set
        print(f"Update cores {self}")
        return True
    
    def remove_container(self, force=False):
        if not self.container is None:
            self.container.remove(force=force)
            self.container = None
        

class CannealJob(BatchJob):
    name = slogger.Job.CANNEAL
    num_threads = 2
    image = "anakli/cca:parsec_canneal"
    command = f"./run -a run -S parsec -p canneal -i native -n {num_threads}"
    weight = 4 # TODO

class BlackscholesJob(BatchJob):
    name = slogger.Job.BLACKSCHOLES
    num_threads = 2
    image = "anakli/cca:parsec_blackscholes"
    command = f"./run -a run -S parsec -p blackscholes -i native -n {num_threads}"
    weight = 1 # TODO

class FerretJob(BatchJob):
    name = slogger.Job.FERRET
    num_threads = 4
    image = "anakli/cca:parsec_ferret"
    command = f"./run -a run -S parsec -p ferret -i native -n {num_threads}"
    weight = 4 # TODO

class FreqmineJob(BatchJob):
    name = slogger.Job.FREQMINE
    num_threads = 4
    image = "anakli/cca:parsec_freqmine"
    command = f"./run -a run -S parsec -p freqmine -i native -n {num_threads}"
    weight = 2 # TODO

class DedupJob(BatchJob):
    name = slogger.Job.DEDUP
    num_threads = 2
    image = "anakli/cca:parsec_dedup"
    command = f"./run -a run -S parsec -p dedup -i native {num_threads}"
    weight = 4 # TODO

class RadixJob(BatchJob):
    name = slogger.Job.RADIX
    num_threads = 4
    image = "anakli/cca:splash2x_radix"
    command = f"./run -a run -S splash2x -p radix -i native -n {num_threads}"
    weight = 1 # TODO

class VipsJob(BatchJob):
    name = slogger.Job.VIPS
    num_threads = 4
    image = "anakli/cca:parsec_vips"
    command = f"./run -a run -S parsec -p vips -i native -n {num_threads}"
    weight = 2 # TODO


class MemcachedProcess(object):
    pid = []
    cores = 0
    process_name = "memcache"

    def __init__(self, cores):
        self.get_pid()
        self.cores = cores

    def get_pid(self):
        if len(self.pid) == 0:
            for proc in psutil.process_iter():
                if self.process_name in proc.name():
                    self.pid.append(proc.pid)
        return self.pid

    def update_memcached_cores(self, logger, cores, enable_log=True):
        if len(self.pid) == 0:
            print(f"ERROR: Could not update memcached cores because pid is None")
            return False
        print(f'Update memcache (pid: {self.pid}) CPUs to {cores}')
        for pid in self.pid:
            command = f'sudo taskset -a -cp {",".join([str(c) for c in cores])} {pid}'
            subprocess.run(command.split(" "), stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        if enable_log:
            logger.update_cores(slogger.Job.MEMCACHED, [str(c) for c in cores])
        self.cores = cores
        return True


class Scheduler(object):

    def __init__(self, memcached: MemcachedProcess, small_jobs: list[BatchJob], medium_jobs: list[BatchJob], large_jobs: list[BatchJob]):
        self.docker_client = docker.from_env()
        self.logger = None
        self.memcached = memcached
        self.small_jobs = small_jobs
        self.medium_jobs = medium_jobs
        self.large_jobs = large_jobs
        self.job_cores = []
        self.memcached.get_pid()
        self.curr_max_load = 0

    def get_all_jobs(self) -> list[BatchJob]:
        return self.small_jobs + self.medium_jobs + self.large_jobs

    def get_cpu_usage(self):
        return psutil.cpu_percent(interval=None, percpu=True)
    
    def check_all_jobs_finished(self):
        return all(j.has_finished() for j in self.get_all_jobs())

    def remove_finished_jobs(self) -> int:
        weight = 0
        for job in self.get_all_jobs():
            if job.is_newly_finished():
                weight = weight + job.weight
                job.finish_job()
        return weight

    def print_job_status(self):
        print("\n== JOB STATUS ==")
        for job in self.get_all_jobs():
            print(f"{job.name} - {job.get_status()}")

    def update_cores_all_jobs(self, cpu_set):
        self.job_cores = cpu_set
        for job in self.get_all_jobs():
            job.update_cores(cpu_set, self.logger)
    
    def remove_all_jobs(self, force=False):
        for job in self.get_all_jobs():
            job.remove_container(force=force)

    def get_current_load(self):
        load = 0
        for job in self.get_all_jobs():
            if job.is_running():
                load = load + job.weight
        return load

    def start_run(self):
        # start with 2 memcached cores in case there is high load in the beginning
        self.memcached.update_memcached_cores(self.logger, [0,1], enable_log=False)
        sleep(2)
        print("Start scheduler")
        self.logger = slogger.SchedulerLogger()
        self.logger.job_start(slogger.Job.MEMCACHED, ["0","1"], 2)
        self.curr_max_load = MAX_LOAD_LOW
        self.job_cores = [2,3]

    def end_run(self):
        self.remove_finished_jobs()
        self.logger.end()
        print("All jobs have finished. Force removing all containers in 10s...")
        sleep(10)
        self.remove_all_jobs(force=True)

    def reload_all_jobs(self):
        for j in self.get_all_jobs():
            j.reload_stats()

    # start new job(s) with upper bound on weights
    def start_next_job(self, weight) -> int:
        # TODO find better strategy
        jobs_to_consider = []
        new_jobs = []
        if weight >= 4:
            jobs_to_consider = self.large_jobs
        elif weight >= 2: 
            jobs_to_consider = self.medium_jobs
        elif weight == 1:
            jobs_to_consider = self.small_jobs
        else:
            return 0

        new_jobs = [j for j in jobs_to_consider if j.is_new()]
    
        if len(new_jobs) > 0:
            t = new_jobs[0].start_job(self.docker_client, self.job_cores, self.logger)
            if t:
                return new_jobs[0].weight
        
        return self.start_next_job(weight/2) + self.start_next_job(weight/2)

    # unpause job(s) with upper bound on weights
    def unpause_job(self, weight) -> int:
        # TODO find better strategy
        jobs_to_consider = []
        paused_jobs = []
        if weight >= 4:
            jobs_to_consider = self.large_jobs
        elif weight >= 2: 
            jobs_to_consider = self.medium_jobs
        elif weight == 1:
            jobs_to_consider = self.small_jobs
        else:
            return 0

        paused_jobs = [j for j in jobs_to_consider if j.is_paused()]
    
        if len(paused_jobs) > 0:
            t = paused_jobs[0].unpause_job(self.logger)
            if t:
                return paused_jobs[0].weight
        return self.unpause_job(weight/2) + self.unpause_job(weight/2)
    
    # pause job(s) with bound on weights
    def pause_job(self, weight) -> int:
        # TODO find better strategy
        if weight <= 0:
            return 0
        jobs_to_consider = []
        running_jobs = []
        if weight >= 4:
            jobs_to_consider = self.large_jobs
        elif weight >= 2: 
            jobs_to_consider = self.medium_jobs
        elif weight == 1:
            jobs_to_consider = self.small_jobs
        else:
            return 0

        running_jobs = [j for j in jobs_to_consider if j.is_running()]
    
        if len(running_jobs) > 0:
            t = running_jobs[0].pause_job(self.logger)
            if t:
                return running_jobs[0].weight
        return self.pause_job(weight/2) + self.pause_job(weight/2)
    
    # starts/unpauses/pauses jobs depending on curr and max load
    def start_pause_unpause_jobs(self):
        # TODO find better strategy
        curr_load = self.get_current_load()
        print(f"curr_load: {curr_load}, max load: {self.curr_max_load}")
        if curr_load > self.curr_max_load:
            self.pause_job(curr_load-self.curr_max_load)
        elif curr_load < self.curr_max_load:
            add_weight = self.unpause_job(self.curr_max_load-curr_load)
            if add_weight + curr_load < self.curr_max_load:
                self.start_next_job(self.curr_max_load-add_weight-curr_load)
        

    # main method!
    def run(self):
        self.start_run()

        # TODO optimize this strategy, implement other strategies and compare ...
        while True:
            self.reload_all_jobs()
            if self.check_all_jobs_finished():
                break

            # get cpu usage per core
            cpu_usage = self.get_cpu_usage() # TODO maybe we could measure the CPU usage multiple times and average
            cpu_usage_memcached = sum([cpu_usage[i] for i in memcached.cores])
            print(f"CPU utilization = {cpu_usage}")
            print(f"memcached CPU utilization = {cpu_usage_memcached}")

            job_string = "\n".join([str(j) for j in self.get_all_jobs()])
            print(job_string)

            # memcached is always run on dedicated cores such that we can measure the CPU utilization 
            # depending on the load memcached gets 1 or 2 cores
            if len(memcached.cores) == 1 and cpu_usage_memcached > CPU_THRESHOLD_1_CORE:
                print("Memache 2 core, jobs 2 cores")
                memcached.update_memcached_cores(self.logger, [0,1])
                self.update_cores_all_jobs([2,3])
                self.curr_max_load = MAX_LOAD_LOW
            elif len(memcached.cores) == 2 and cpu_usage_memcached < CPU_THRESHOLD_2_CORES:
                print("Memache 1 core, jobs 3 cores")
                memcached.update_memcached_cores(self.logger, [0])
                self.update_cores_all_jobs([1,2,3])
                self.curr_max_load = MAX_LOAD_HIGH

            # update running jobs such that curr max load is satisfied
            self.reload_all_jobs()
            self.start_pause_unpause_jobs()

            self.reload_all_jobs()
            if self.check_all_jobs_finished():
                break
            print("Sleep")
            sleep(SLEEP_TIME)

        self.end_run()


memcached = MemcachedProcess([])
pids = memcached.get_pid()
if len(pids) != 2:
    print(f"\nUnexpected number of memcached processes. Expected 2, found {len(pids)} ({pids}). Abort!")
    exit(-1)

# TODO find optimal assignements, add/remove queues if necessary
scheduler = Scheduler(memcached, 
                      small_jobs=[RadixJob(), BlackscholesJob()],
                      medium_jobs=[FreqmineJob(), VipsJob()], 
                      large_jobs=[CannealJob(), DedupJob(), FerretJob()])
scheduler.remove_all_jobs(force=True) # remove containers if they already exist
try:
    scheduler.run()
except Exception as e:
    print(e)
    print(f"\nUnexpected error. Remove all containers and abort.")
    scheduler.remove_all_jobs(force=True)
    exit(-1)

print(f"\nScheduler terminated successfully!")
    
        
    
        
    

