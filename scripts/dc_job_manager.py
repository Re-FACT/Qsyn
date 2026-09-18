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
DC_EXEC = "dc_shell"
DC_EXEC_TOPO = "dc_shell -topo"
DC_LOG_FILE = "dc_run.log"
SPACE_LIMIT = 80  # Maximum space tuned for the screen width


# Class of a DC job run manager
class DcJobManager:
    def __init__(self):
        # Internal data
        self.__new_thread_wait_time_ = 1  # [sec.] Give a wait time before starting the next thread. Avoid any conflicts in switching directories
        self.__dc_rundir_prefix_ = "_snps_dc"
        self.__job_names_ = []
        self.__job_names_mode_map = {}
        self.__tcl_scripts_ = []
        self.__rundirs_ = (
            []
        )  # Directory when DC is actually called. All the intermediate files will be kept there
        self.__error_counts_ = []  # Flag it DC run is successfully or not

    # Set default runtime directory name
    def set_runtime_dir_prefix(self, val):
        self.__dc_rundir_prefix_ = val

    # Create a new job
    def create_job(self, job_name, mode):
        if job_name in self.__job_names_:
            raise Exception(
                "Duplicated job names: another job has already been created under the same name!"
            )
        self.__job_names_.append(job_name)
        self.__job_names_mode_map[job_name] = mode
        # Give a default empty script
        self.__tcl_scripts_.append("")
        # Set a default value
        self.__rundirs_.append(self.__dc_rundir_prefix_ + "_" + job_name)
        # Clear error count
        self.__error_counts_.append(0)

    # Get the runtime directory for a given job
    def dc_rundir(self, job_name):
        if job_name not in self.__job_names_:
            raise Exception("Intend to access/mutate a job which has not been created!")
        job_idx = self.__job_names_.index(job_name)
        return self.__rundirs_[job_idx]

    # Set the tcl script to run the DC job
    def set_tcl_script(self, job_name, val):
        if job_name not in self.__job_names_:
            raise Exception("Intend to access/mutate a job which has not been created!")
        job_idx = self.__job_names_.index(job_name)
        self.__tcl_scripts_[job_idx] = val

    # Set the runtime directory to execute DC job
    def set_runtime_dir(self, job_name, val):
        if job_name not in self.__job_names_:
            raise Exception("Intend to access/mutate a job which has not been created!")
        job_idx = self.__job_names_.index(job_name)
        self.__rundirs_[job_idx] = val

    # Run a DC job with a given job name
    def __thread_run_dc(
        self, thread_sema, job_name, check_log, job_status, job_time, curr_dir, mode
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
            if not os.path.isfile(self.__tcl_scripts_[job_idx]):
                raise Exception(f"Tcl script '{self.__tcl_scripts_[job_idx]}' is not a valid file")
            # Change to the runtime directory
            os.chdir(os.path.join(curr_dir, self.__rundirs_[job_idx]))
            logging.debug(f"Changed to directory: {self.__rundirs_[job_idx]}")
            # Run DC
            if mode == "topo":
                run_cmd = (
                    DC_EXEC_TOPO
                    + " -f "
                    + os.path.abspath(self.__tcl_scripts_[job_idx])
                    + " > "
                    + DC_LOG_FILE
                )
            else:
                run_cmd = (
                    DC_EXEC
                    + " -f "
                    + os.path.abspath(self.__tcl_scripts_[job_idx])
                    + " > "
                    + DC_LOG_FILE
                )
            # Current, we have to disable checks because PrimeTime has issues when loading library compilers
            subprocess.run(run_cmd, shell=True, check=False)
            # Restore
            os.chdir(curr_dir)

            end_time = time.time()
            job_time[job_name] = timedelta(seconds=(end_time - start_time))

            time_str = "Running DC job '" + job_name + "' took " + str(job_time[job_name])
            end_time_str = datetime.fromtimestamp(end_time).isoformat()
            logging.info(job_name + " ends  at" + time_logging_space + end_time_str)

            # check log
            if check_log:
                job_status[job_name] += self.parse_dc_log(job_name)

            return job_status

    # Check a DC log, count the number errors found
    def parse_dc_log(self, job_name):
        num_errors = 0
        if job_name not in self.__job_names_:
            raise Exception("Intend to access/mutate a job which has not been created!")
        job_idx = self.__job_names_.index(job_name)
        # Log runtime
        start_time = time.time()
        log_path = os.path.join(self.__rundirs_[job_idx], DC_LOG_FILE)
        log_abspath = os.path.abspath(log_path)
        # Check if the tcl script is valid
        if not os.path.isfile(log_abspath):
            raise Exception(f"Expect DC run log file at '{log_abspath}' but not found!")
        logging.info(f"Checking DC log file '{log_abspath}'...")

        with open(log_abspath, "r") as logf:
            log_lines = logf.readlines()
            for line_num, curr_line in enumerate(log_lines):
                is_err = False
                if re.search("Error", curr_line):
                    # Add an exception which does not impact the ptpx run failures; just some env setup issue
                    if (
                        curr_line
                        != "Error: Library Compiler executable path is not set. (PT-063)\n"
                    ):
                        is_err = True
                elif re.search("error", curr_line):
                    is_err = True
                if is_err:
                    # logging("DC run error [LINE" + str(line_num) + "]: ")
                    print(curr_line)
                    num_errors += 1

        end_time = time.time()
        time_diff = timedelta(seconds=(end_time - start_time))

        time_str = "Checking DC log file took " + str(time_diff)
        logging.info(time_str)

        return num_errors

    # Run all DC jobs with a given maximum number of jobs in parrallel
    def run_dc_all(self, max_num_jobs, check_log):
        # Create thread pool
        thread_sema = threading.BoundedSemaphore(value=max_num_jobs)
        thread_list = []

        # Job status dashboard
        job_status = {}
        job_time = {}

        curr_dir = os.getcwd()
        for key in self.__job_names_:
            mode = self.__job_names_mode_map[key]
            curr_thread = threading.Thread(
                target=self.__thread_run_dc,
                args=(thread_sema, key, check_log, job_status, job_time, curr_dir, mode),
            )
            curr_thread.start()
            thread_list.append(curr_thread)
            time.sleep(self.__new_thread_wait_time_)

        for curr_thread in thread_list:
            curr_thread.join()

        num_passed_jobs = 0
        total_num_jobs = 0
        for key in self.__job_names_:
            job_idx = self.__job_names_.index(key)
            curr_job_status = job_status[key]
            # Create a space when logging
            logging_space = " " + "." * (SPACE_LIMIT - len(key) - 2) + " "
            self.__error_counts_[job_idx] += curr_job_status
            if curr_job_status == 0:
                logging.info(key + logging_space + "[Pass]")
                num_passed_jobs += 1
            else:
                logging.info(key + logging_space + "[Fail]")
            # Show runtime
            time_diff = job_time[key]
            time_str = "took " + str(time_diff)
            time_logging_space = "." * (SPACE_LIMIT - len(key) - len(time_str) - 2) + " "
            logging.info(key + time_logging_space + time_str)
            total_num_jobs += 1
        # Show a final summary on pass rate
        logging.info("Finished " + str(total_num_jobs) + " synthesis jobs")
        logging.info("\tPassed " + str(num_passed_jobs))
        logging.info("\tFailed " + str(total_num_jobs - num_passed_jobs))

    # Check if run is successful
    def num_errors(self):
        return sum(self.__error_counts_)

    # Clear all the data
    def clear(self):
        self.__init__()
