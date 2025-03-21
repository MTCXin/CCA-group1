import psutil
import scheduler_logger as slogger
import subprocess
import sys
import docker
import time

# POLICY
# We have 2 list of jobs: small and large ones
# if the load memcached is low:
#       - run memcached on cores 0
#       - run a large job on cores 1,2,3 
#       - pause small jobs 
#       - if all large jobs finished, we run a small job instead
#       
# if the load on memcaches is high:
#       - run memcacched on cores 0,1
#       - run a small job on cores 2,3
#       - pause large jobs
#
# whether the load on memcached is low or high is determined by monitoring the CPU utilization of the memcached cores.


SLEEP_TIME = 0.2 # TODO: find suitable value or remove sleep

THRESHOLD_HIGH = 25
THRESHOLD_LOW = 15
# TOLERANCE = 10

class BatchJob(object):
    name = ""
    num_threads = 4 # default, can be overriden
    image = ""
    command = ""
    container = None # will be set once the container has been created
    cores = [] # will be set when the job is started and is updated dynamically
    has_finished_ = False # will be set once the container finished and was removed
    start_time = None
    runtime = 0.0

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
        self.start_time = time.time()
        # print(f"Start {self}")
        self.container = container

    def pause_job(self, logger):
        if self.container is None:
            return False
        self.container.reload()
        if not self.is_running():
            # print(f"WARN: Cannot pause {self.name} because job is not running.")
            return False
        try:
            self.container.pause()
            logger.job_pause(self.name)
            self.runtime = self.runtime + (time.time() - self.start_time)
            # print(f"Pause {self}")
            return True
        except:
            print(f"ERROR: Could not pause job {self.name}")
            return False

    def unpause_job(self, logger):
        if self.container is None:
            return False
        self.container.reload()
        if not self.is_paused():
            # print(f"WARN: Cannot unpause {self.name} because job is not paused.")
            return False
        try:
            self.container.unpause()
            logger.job_unpause(self.name)
            self.start_time = time.time()
            # print(f"Unpause {self}")
            return True
        except:
            print(f"ERROR: Could not unpause job {self.name}")
            return False 
        
    def finish_job(self, logger: slogger.SchedulerLogger):
        if not self.container is None:
            self.container.reload()
        if not self.has_finished():
            # print(f"WARN: Cannot finish {self.name} because job is not done yet.")
            return False
        elif self.container is None: # job has been removed already
            return True
        else:
            try:
                self.container.reload()
                result = self.container.wait()
                exit_code = result["StatusCode"]
                logger.custom_event(self.name, f"exit code {exit_code}")
                # print("Try to remove")
                self.container.remove()
                if exit_code != 0:
                    print(f"ERROR: The following container exited with code {exit_code}\n{self}\nContainer stats: {result}")
                    exit(-1)
                logger.job_end(self.name)
                logger.custom_event(self.name, f"runtime (s) {self.runtime}")
                self.runtime = self.runtime + (time.time() - self.start_time)
                self.container = None
                self.has_finished_ = True
                return True
            except:
                print(f"ERROR: Could not finish job {self.name}")
                return False

    def update_cores(self, cpu_set, logger):
        if self.container is None:
            return False
        self.container.reload()
        if self.container is None or self.has_finished():
            # print(f"WARN: Cannot update {self.name} because job is not running.")
            return False

        self.container.update(cpuset_cpus=",".join([str(c) for c in cpu_set]))
        logger.update_cores(self.name, [str(c) for c in cpu_set])
        self.cores = cpu_set
        # print(f"Update cores {self}")
        return True
    
    def remove_container(self, force=False):
        if not self.container is None:
            self.container.remove(force=force)
            self.container = None
        

class CannealJob(BatchJob):
    name = slogger.Job.CANNEAL
    num_threads = 4 # TODO
    image = "anakli/cca:parsec_canneal"
    command = f"./run -a run -S parsec -p canneal -i native -n {num_threads}"

class BlackscholesJob(BatchJob):
    name = slogger.Job.BLACKSCHOLES
    num_threads = 2 # TODO
    image = "anakli/cca:parsec_blackscholes"
    command = f"./run -a run -S parsec -p blackscholes -i native -n {num_threads}"

class FerretJob(BatchJob):
    name = slogger.Job.FERRET
    num_threads = 4 # TODO
    image = "anakli/cca:parsec_ferret"
    command = f"./run -a run -S parsec -p ferret -i native -n {num_threads}"

class FreqmineJob(BatchJob):
    name = slogger.Job.FREQMINE
    num_threads = 4 # TODO
    image = "anakli/cca:parsec_freqmine"
    command = f"./run -a run -S parsec -p freqmine -i native -n {num_threads}"

class DedupJob(BatchJob):
    name = slogger.Job.DEDUP
    num_threads = 4 # TODO
    image = "anakli/cca:parsec_dedup"
    command = f"./run -a run -S parsec -p dedup -i native {num_threads}"

class RadixJob(BatchJob):
    name = slogger.Job.RADIX
    num_threads = 2 # TODO
    image = "anakli/cca:splash2x_radix"
    command = f"./run -a run -S splash2x -p radix -i native -n {num_threads}"

class VipsJob(BatchJob):
    name = slogger.Job.VIPS
    num_threads = 2 # TODO
    image = "anakli/cca:parsec_vips"
    command = f"./run -a run -S parsec -p vips -i native -n {num_threads}"


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
        if cores == self.cores:
            return
        if len(self.pid) == 0:
            print(f"ERROR: Could not update memcached cores because pid is None")
            return False
        # print(f'Update memcache (pid: {self.pid}) CPUs to {cores}')
        for pid in self.pid:
            command = f'sudo taskset -a -cp {",".join([str(c) for c in cores])} {pid}'
            subprocess.run(command.split(" "), stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        if enable_log:
            logger.update_cores(slogger.Job.MEMCACHED, [str(c) for c in cores])
        self.cores = cores
        return True
    
    def __str__(self):
        return f"memcached: pid = {self.pid}, cores = {self.cores}"


class Scheduler(object):

    def __init__(self, memcached: MemcachedProcess, small_jobs: list[BatchJob], large_jobs: list[BatchJob]):
        self.docker_client = docker.from_env()
        self.logger = None
        self.memcached = memcached
        self.small_jobs = small_jobs
        self.large_jobs = large_jobs
        self.memcached.get_pid()
        self.start_time = 0.0

    def get_all_jobs(self) -> list[BatchJob]:
        return self.small_jobs + self.large_jobs
    
    #CPU usage for memcache process
    def get_pid_cpu(self):
        pid = self.memcached.pid[0]
        process = psutil.Process(pid)
        cpu_usage = process.cpu_percent(interval=None)
        return cpu_usage

    # CPU usage per core
    def get_cpu_usage(self):
        return psutil.cpu_percent(interval=None, percpu=True)
    
    def check_all_jobs_finished(self):
        return all(j.has_finished() for j in self.get_all_jobs())

    def remove_finished_jobs(self):
        for job in self.get_all_jobs():
            if job.is_newly_finished():
                job.finish_job(self.logger)

    def print_job_status(self):
        for job in self.get_all_jobs():
            print(f"{job.name} - {job.get_status()}")

    def update_cores_all_jobs(self, cpu_set):
        if cpu_set == self.job_cores:
            return
        self.job_cores = cpu_set
        for job in self.get_all_jobs():
            job.update_cores(cpu_set, self.logger)
    
    def remove_all_jobs(self, force=False):
        for job in self.get_all_jobs():
            job.remove_container(force=force)


    def start_run(self):
        # start with 2 memcached cores in case there is high load in the beginning
        self.memcached.update_memcached_cores(self.logger, [0,1], enable_log=False)
        self.get_pid_cpu()
        self.get_cpu_usage()
        time.sleep(2)
        print("Start scheduler")
        self.logger = slogger.SchedulerLogger()
        self.logger.job_start(slogger.Job.MEMCACHED, ["0","1"], 2)
        self.job_cores = [2,3]
        self.start_or_unpause_job(self.small_jobs)
        self.start_time = time.time()

    def end_run(self):
        runtime = time.time() - self.start_time
        self.remove_finished_jobs()
        self.logger.custom_event(slogger.Job.SCHEDULER, f"runtime (s) {runtime}")
        self.logger.end()
        print("All jobs have finished. Force removing all containers in 10s...")
        time.sleep(10)
        self.remove_all_jobs(force=True)

    def reload_all_jobs(self):
        for j in self.get_all_jobs():
            j.reload_stats()

    def can_run_one_job(self, jobs: list[BatchJob]) -> bool:
        return len([j for j in jobs if j.is_running() or j.is_new() or j.is_paused()]) > 0

    def ensure_one_job_runs(self, jobs: list[BatchJob]):
        running_jobs = [j for j in jobs if j.is_running()]
        if len(running_jobs) == 0:
            return self.start_or_unpause_job(jobs)
        return True

    def start_or_unpause_job(self, job: list[BatchJob]):
        paused_jobs = [j for j in job if j.is_paused()]
        if len(paused_jobs) > 0:
            paused_jobs[0].unpause_job(self.logger)
            return True
        else:
            new_jobs = [j for j in job if j.is_new()]
            if len(new_jobs) > 0:
                new_jobs[0].start_job(self.docker_client, self.job_cores, self.logger)
                return True
        return False
    
    def pause_all_jobs(self, jobs: list[BatchJob]):
        running_jobs = [j for j in jobs if j.is_running()]
        for j in running_jobs:
            j.pause_job(self.logger)
        return len(running_jobs)
        

    # main method!
    def run(self):
        self.start_run()

        keep_on_high = 3 # avoid switching too quickly

        while True:
            self.reload_all_jobs()
            if self.check_all_jobs_finished():
                break

            self.remove_finished_jobs()
            keep_on_high = keep_on_high - 1

            cpu_usage = self.get_cpu_usage()
            cpu_usage_memcached = sum([cpu_usage[i] for i in memcached.cores])
            print(f"CPU utilization = {cpu_usage}")
            print(f"memcached CPU utilization = {cpu_usage_memcached}")
            print(self.memcached)

            job_string = "\n".join([str(j) for j in self.get_all_jobs()])
            print(job_string)

            if cpu_usage_memcached > THRESHOLD_HIGH:
                if len(self.memcached.cores) < 2:
                    self.memcached.update_memcached_cores(self.logger, [0,1])
                    self.update_cores_all_jobs([2,3])
                    keep_on_high = 5
            elif cpu_usage_memcached < THRESHOLD_LOW:
                if keep_on_high < 0 and len(self.memcached.cores) > 1:
                    self.memcached.update_memcached_cores(self.logger, [0])
                    self.update_cores_all_jobs([1,2,3])

            if len(self.memcached.cores) == 1:
                # run a large job if possible, otherwise run a small job
                if self.can_run_one_job(self.large_jobs):
                    self.pause_all_jobs(self.small_jobs)
                    time.sleep(0.1)
                    self.ensure_one_job_runs(self.large_jobs) 
                else:
                    self.ensure_one_job_runs(self.small_jobs)
                    
            elif len(self.memcached.cores) == 2:
                # only run a small job
                self.pause_all_jobs(self.large_jobs)
                time.sleep(0.1)
                self.ensure_one_job_runs(self.small_jobs)
                
            self.reload_all_jobs()
            if self.check_all_jobs_finished():
                break
            self.get_cpu_usage()
            time.sleep(SLEEP_TIME)

        self.end_run()


memcached = MemcachedProcess([])
pids = memcached.get_pid()
if len(pids) != 1:
    print(f"\nUnexpected number of memcached processes. Expected 1, found {len(pids)} ({pids}). Abort!")
    exit(-1)

scheduler = Scheduler(memcached, 
                      small_jobs=[BlackscholesJob(), RadixJob(), VipsJob(), CannealJob(), FreqmineJob()],
                      large_jobs=[FerretJob(), DedupJob()])
                    #   small_jobs=[BlackscholesJob(), RadixJob(), CannealJob(), VipsJob(), DedupJob()],
                    #   large_jobs=[FerretJob(), FreqmineJob()])
try:
    scheduler.run()
except Exception as e:
    print(e)
    print(f"\nUnexpected error. Remove all containers and abort.")
    scheduler.remove_all_jobs(force=True)
    exit(-1)

print(f"\nScheduler terminated successfully!")
    
        
    
        
    

