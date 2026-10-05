import time
import logging
import yaml
import os
import re
import subprocess
from datetime import timedelta
from datetime import datetime
import threading

# Constants
EZREG_RUNLOG_FNAME = "_ezreg_run.log"
EZREG_NUM_CHAR_PER_LINE = 80  # Maximum space tuned for the screen width

# Class of a regression test job run manager
class EzRegJobManager:
    def __init__(self):
        # Internal data
        self.__new_thread_wait_time_ = 1  # [sec.] Give a wait time before starting the next thread. Avoid any conflicts in switching directories
        self.__job_names_ = []
        self.__job_commands_ = []
        self.__job_deps_ = []
        self.__job_status_data_ = []
        self.__job_rundirs_ = []
        self.__job_logs_ = []
        self.__job_expect_failures_ = []
        self.__error_counts_ = []  # Flag it DC run is successfully or not
        # Constants
        self.__TASK_STATUS_INIT__ = "fresh"
        self.__TASK_STATUS_PASS__ = "pass"
        self.__TASK_STATUS_FAIL__ = "fail"

    # Create a new job
    def create_job(self, job_name, job_cmd, exp_f):
        if job_name in self.__job_names_:
            raise Exception(
                "Duplicated job names: another job has already been created under the same name!"
            )
        self.__job_names_.append(job_name)
        self.__job_commands_.append(job_cmd)
        self.__job_deps_.append([])
        job_log_fpath = job_name + EZREG_RUNLOG_FNAME
        self.__job_logs_.append(job_log_fpath)
        self.__job_rundirs_.append("")
        self.__job_status_data_.append([job_name, self.__TASK_STATUS_FAIL__, job_log_fpath])
        self.__job_expect_failures_.append(exp_f)
        # Clear error count
        self.__error_counts_.append(0)

    # Get the runtime directory for a given job
    def rundir(self, job_name):
        if job_name not in self.__job_names_:
            raise Exception("Intend to access/mutate a job which has not been created!")
        job_idx = self.__job_names_.index(job_name)
        return self.__rundirs_[job_idx]

    # Set the tcl script to run the DC job
    def set_rundir(self, job_name, val):
        if job_name not in self.__job_names_:
            raise Exception("Intend to access/mutate a job which has not been created!")
        job_idx = self.__job_names_.index(job_name)
        self.__rundirs_[job_idx] = val

    # Set the tcl script to run the DC job
    def set_job_deps(self, job_name, val):
        if job_name not in self.__job_names_:
            raise Exception("Intend to access/mutate a job which has not been created!")
        job_idx = self.__job_names_.index(job_name)
        self.__job_deps_[job_idx] = val

    # Get result data for give job
    def job_status_data(self, job_name):
        if job_name not in self.__job_names_:
            raise Exception("Intend to access/mutate a job which has not been created!")
        job_idx = self.__job_names_.index(job_name)
        return self.__job_status_data_[job_idx]

    def jobs(self):
        return self.__job_names_

    # Run a DC job with a given job name
    def __thread_run_job(
        self, thread_sema, job_name, dryrun, check_log, job_status, job_time, curr_dir
    ):
        if job_name not in self.__job_names_:
            raise Exception("Intend to access/mutate a job which has not been created!")
        job_idx = self.__job_names_.index(job_name)

        with thread_sema:
            thread_name = threading.currentThread().getName()

            # Log runtime
            start_time = time.time()

            start_time_str = datetime.fromtimestamp(start_time).isoformat()
            time_logging_space = (
                "." * (SPACE_LIMIT - len(job_name) - len(" start at") - len(start_time_str) - 2)
                + " "
            )
            logging.info(job_name + " start at" + time_logging_space + start_time_str)

            job_status[job_name] = 0

            # Check if the tcl script is valid
            if not os.path.isfile(self.__task_scripts_[job_idx]):
                raise Exception(
                    f"Task script '{self.__task_scripts_[job_idx]}' is not a valid file"
                )
            # Change to the runtime directory
            runtime_dir = os.path.abspath(self.__job_rundirs_[job_idx])
            os.makedirs(runtime_dir, exist_ok=True)
            os.chdir(runtime_dir)
            logging.debug(f"Changed to directory: {runtime_dir}")
            # Run DC
            run_cmd = self.__job_commands_[job_idx] 
            logging.debug("Run job with the following command:\n\t" + run_cmd)
            log_fname = self.__job_logs_[job_idx]
            # Current, we have to disable checks because PrimeTime has issues when loading library compilers
            if dryrun:
                logging.info(
                    f"User choose to perform dryrun\n User may run with \n\t{run_cmd}"
                )
            else:
                with open(log_fname, "w") as log_f:
                    make_process = subprocess.Popen(run_cmd, shell=True, stdout=log_f, stderr=log_f)
                    if (make_process.wait()) != 0:
                        job_status[job_name] += 1

            # Restore
            os.chdir(curr_dir)

            end_time = time.time()
            job_time[job_name] = timedelta(seconds=(end_time - start_time))

            time_str = "Running job '" + job_name + "' took " + str(job_time[job_name])
            end_time_str = datetime.fromtimestamp(end_time).isoformat()
            logging.info(job_name + " ends  at" + time_logging_space + end_time_str)

            # check log
            if not dryrun and check_log:
                job_status[job_name] += self.parse_job_log(job_name)

            return job_status

    # Check a job log, count the number errors found
    def parse_job_log(self, job_name):
        num_errors = 0
        if job_name not in self.__job_names_:
            raise Exception("Intend to access/mutate a job which has not been created!")
        job_idx = self.__job_names_.index(job_name)
        # Log runtime
        start_time = time.time()
        runtime_dir = os.path.abspath(self.__job_rundirs_[job_idx])
        log_path = os.path.join(runtime_dir, self.__task_logs_[job_idx])
        log_abspath = os.path.abspath(log_path)
        # Check if the tcl script is valid
        if not os.path.isfile(log_abspath):
            raise Exception(f"Expect run log file at '{log_abspath}' but not found!")
        logging.info(f"Checking log file '{log_abspath}'...")

        with open(log_abspath, "r") as logf:
            log_lines = logf.readlines()
            end_flag = 0
            for line_num, curr_line in enumerate(log_lines):
                status = 0
                if re.search("ERROR", curr_line):
                    status += 1
                if re.search("Failed", curr_line) and not re.search("Failed 0", curr_line):
                    status += 1
                if re.search("Error", curr_line):
                    status += 1
                if re.search("Segmentation fault", curr_line):
                    status += 1
                if re.search("Assertion", curr_line) and re.search("failed", curr_line):
                    status += 1
                if status:
                    if not self.__job_expect_failures_[job_idx]:
                        logging.info("Job run error [LINE" + str(line_num) + "]: ")
                        logging.info(curr_line)
                    num_errors += status

        end_time = time.time()
        time_diff = timedelta(seconds=(end_time - start_time))

        time_str = "Checking log file took " + str(time_diff)
        logging.info(time_str)

        return num_errors

    # Run all jobs with a given maximum number of jobs in parrallel
    def run_all(self, max_num_jobs, dryrun, check_log):
        # Create thread pool
        thread_sema = threading.BoundedSemaphore(value=max_num_jobs)

        # Job status dashboard
        job_status = {}
        job_time = {}

        curr_dir = os.getcwd()

        num_passed_jobs = 0
        total_num_jobs = 0

        # Initalize
        task_status = {}
        for task_name in self.__job_names_:
            task_status[task_name] = self.__TASK_STATUS_INIT__
        task_all_done = False
        task_never_start = {}

        while not task_all_done:
            thread_list = []
            tasks_started = []
            # Run all the tasks without dependencies or dependencies are finished
            for job_name in self.__job_names_:
                if task_status[job_name] == self.__TASK_STATUS_PASS__:
                    continue
                if task_status[job_name] == self.__TASK_STATUS_FAIL__:
                    continue

                # Check dependencies
                task_to_start = True
                job_idx = self.__job_names_.index(job_name)
                for dep_name in self.__job_deps_[job_idx]:
                    if task_status[dep_name] == self.__TASK_STATUS_INIT__:
                        task_to_start = False
                        break
                    if task_status[dep_name] == self.__TASK_STATUS_FAIL__:
                        task_to_start = False
                        # Dependency failed, this task should fail
                        task_status[job_name] = self.__TASK_STATUS_FAIL__
                        task_never_start[job_name] = True
                        logging.info(
                            f"Job '{job_name}' will not start as its dependency job '{dep_name}' is already failed"
                        )
                        break
                # Any dependency found, not to start now. wait for next round
                if not task_to_start:
                    continue

                curr_thread = threading.Thread(
                    target=self.__thread_run_job,
                    args=(thread_sema, job_name, dryrun, check_log, job_status, job_time, curr_dir),
                )
                curr_thread.start()
                thread_list.append(curr_thread)
                tasks_started.append(job_name)
                time.sleep(self.__new_thread_wait_time_)

            # Wait all the threads to finish
            for curr_thread in thread_list:
                curr_thread.join()

            # Check and Update status
            for task_name in tasks_started:
                job_idx = self.__job_names_.index(task_name)
                curr_job_status = job_status[task_name]
                # Create a space when logging
                logging_space = " " + "." * (SPACE_LIMIT - len(task_name) - 2) + " "
                if dryrun:
                    if curr_job_status == 0:
                        self.__error_counts_[job_idx] += curr_job_status
                        logging.info(task_name + logging_space + "[Pass]")
                        task_status[task_name] = self.__TASK_STATUS_PASS__
                        self.__job_status_data_[job_idx][1] = self.__TASK_STATUS_PASS__
                        num_passed_jobs += 1
                    else:
                        self.__error_counts_[job_idx] += curr_job_status
                        logging.info(task_name + logging_space + "[Fail]")
                        task_status[task_name] = self.__TASK_STATUS_FAIL__
                else:
                    if curr_job_status == 0:
                        if self.__job_expect_failures_[job_idx]:
                            self.__error_counts_[job_idx] += curr_job_status
                            logging.info(task_name + logging_space + "[Fail*]")
                            task_status[task_name] = self.__TASK_STATUS_FAIL__
                        else:
                            self.__error_counts_[job_idx] += curr_job_status
                            logging.info(task_name + logging_space + "[Pass]")
                            task_status[task_name] = self.__TASK_STATUS_PASS__
                            self.__job_status_data_[job_idx][1] = self.__TASK_STATUS_PASS__
                            num_passed_jobs += 1
                    else:
                        if self.__job_expect_failures_[job_idx]:
                            logging.info(task_name + logging_space + "[Pass*]")
                            task_status[task_name] = self.__TASK_STATUS_PASS__
                            self.__job_status_data_[job_idx][1] = self.__TASK_STATUS_PASS__
                            num_passed_jobs += 1
                        else:
                            self.__error_counts_[job_idx] += curr_job_status
                            logging.info(task_name + logging_space + "[Fail]")
                            task_status[task_name] = self.__TASK_STATUS_FAIL__
                # Show runtime
                if task_name in task_never_start:
                    logging.info(f"due to a dependency failure")
                else:
                    time_diff = job_time[task_name]
                    time_str = "took " + str(time_diff)
                    time_logging_space = (
                        "." * (SPACE_LIMIT - len(task_name) - len(time_str) - 2) + " "
                    )
                    logging.info(task_name + time_logging_space + time_str)
                total_num_jobs += 1

            task_all_done = True
            for job_name in self.__job_names_:
                if task_status[job_name] == self.__TASK_STATUS_INIT__:
                    task_all_done = False
                    break

        # Show a final summary on pass rate
        logging.info("Finished " + str(total_num_jobs) + " jobs")
        logging.info("\tPassed " + str(num_passed_jobs))
        logging.info("\tFailed " + str(total_num_jobs - num_passed_jobs))

        logging.info("\n\t[Fail*] Expect fail but it passed in the run")
        logging.info("\n\t[Pass*] Expect fail but it failed in the run")

    # Check if run is successful
    def num_errors(self):
        return sum(self.__error_counts_)

    # Clear all the data
    def clear(self):
        self.__init__()
