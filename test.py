import subprocess
import json
import os
import time
import logging
import datetime

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('/var/log/cassandra/repair_check.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
current_time = int(time.time())
REPAIR_STATUS_FILE = '/var/tmp/repair_status.json'
REPAIR_NODE_BOOTSTRAP_DATE_FILE = '/var/tmp/repair_node_bootstrap_date'
TIME_DIFF = 10800 # 3 hours
SEVEN_DAYS_IN_SECONDS = 604800
EIGHT_DAYS_IN_SECONDS = 691200
NINE_DAYS_IN_SECONDS = 777600
SENSU_ALERT_JOB_NOT_RUNNING = 'Repair-job-not-running'
SENSU_ALERT_REPAIR_PROCESS = 'Cassandra Repair Process'
REPAIR_STEPS = '<%= @repair_steps %>'
REPAIR_WORKERS = '<%= @repair_workers %>'
REPAIR_WINDOW = '<%= @repair_window %>'


def run_command(cmd):

    logger.debug('Executing cmd : {0}'.format(' '.join(cmd)))
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, err = p.communicate()
    if p.returncode != 0:
        message = 'Command {0} exited with code {1}. STDERR: "{2}"'.format(' '.join(cmd), p.returncode, err)
        logger.debug(message)
        raise Exception(message)
    return p.returncode, out, err


def run_command_check(cmd):
    logger.debug('new run command')
    pid= map(int,subprocess.check_output(['pidof','range_repair']).split())
    if len(pid) > 1:
        message = 'issue'
        logger.debug(message)
        raise Exception(message)
    return 0, len(pid), None

def raise_sensu_alert(check_name, error_name):
    """
    Raise alerts in Pagerduty on failure via Sensu
    :param check_name
    :param error_name:
    :return:
    """
    if error_name:
        cmd = ["<%= scope.lookupvar('sensu::client::monit_trigger_script') %>", check_name, "{0}".format(error_name)]
        try:
            run_command(cmd)
        except Exception:
            logger.info('Exception in raising sensu alert')


def resolve_sensu_alert(check_name):
    """
    Raise alerts in Pagerduty on failure via Sensu.
    :param check_name:
    :return:
    """
    if check_name:
        logger.info("Resolving sensu alert with name - {}".format(check_name))
        cmd = ["<%= scope.lookupvar('sensu::client::monit_resolve_script') %>", check_name]
        try:
            run_command(cmd)
        except Exception:
            logger.info('exception in resolving sensu alert')


class CheckRepairs(object):
    """
    Check Repairs.
    """

    @classmethod
    def repair_status_alert(cls, check_name,repair_status):
        """
        Check for the cassandra repairs.
        :return:
        """

        logger.debug("Raising sensu alert")
        raise_sensu_alert(check_name,"{}".format(repair_status))

    @classmethod
    def can_trigger_repair_now(cls):
        """
        Check if we are in repair window right now, so that repair can be triggered or not.
        :return:
        """
        ranges = REPAIR_WINDOW.split('-')
        start_hour = int(ranges[0])
        end_hour = int(ranges[1])

        if start_hour < 0 or start_hour > 23 or end_hour < 0 or end_hour > 23:
            logger.error("Repair window is invalid, so will trigger repair anyways now.")
            return True

        if start_hour == end_hour: # repairs are always allowed.
            return True

        hour = datetime.datetime.utcnow().hour
        if start_hour > end_hour and (hour >= start_hour or hour < end_hour):
            return True
        elif start_hour < end_hour and hour >= start_hour and hour < end_hour:
            return True
        return False


    @classmethod
    def is_repair_running(cls):
        """
        Check if repair is running on the host or not.
        :return:
        """
        is_repairs_running_status = False
        try:
            return_code, out, error = run_command(['pgrep -f range_repair | wc -l'])
            if return_code == 0 and error == '':
                if int(out) > 1: # when executed from python pgrep command counts itslef as well
                    logger.info("Repairs are in progress on the node")
                    is_repairs_running_status = True
            else :
                logger.error("Command Failed with return code: {}, error: {}".format(return_code,  error))
        except Exception as e:
            logger.error("Exception occured while trying to check if repairs are already running: {}".format(e))


        return is_repairs_running_status

    @classmethod
    def kill_repair(cls):
        """
        Kill the current running repairs.
        :return:
        """
        run_command(['pkill -f repair'])

    @classmethod
    def fix_hung_repair(cls):
        """
        Fix the hung repair here only and not send alert to Sensu.
        :return:
        """
        if cls.is_repair_running():
            cls.kill_repair()
        if cls.can_trigger_repair_now():
            resume_command = ['/opt/cassandra_range_repair/start_range_repair.sh']
            resume_command.append('-d')
            resume_command.extend(['-s', REPAIR_STEPS])
            resume_command.extend(['-w', REPAIR_WORKERS])
            resume_command.append('--resume')
            resume_command.extend(['--output-status', REPAIR_STATUS_FILE])
            run_command(resume_command)
        else:
            logger.info("Cannot trigger repairs now as we are out of the window. Will wait for window to trigger repairs.")

    @classmethod
    def fix_failed_repair(cls):
        """
        Fix the failed ranges here only and not send alert to Sensu.
        :return:
        """
        if cls.is_repair_running():
            logger.info("Current repair is still running, so not fixing the failed ranges now.")
        elif cls.can_trigger_repair_now():
            logger.info("No repair is running now, will try to fix the failed ranges.")
            failed_command = ['/opt/cassandra_range_repair/start_failed_repair.sh']
            failed_command.append(REPAIR_STATUS_FILE)
            run_command(failed_command)
        else:
            logger.info("Cannot trigger repairs now as we are out of the window. Will wait for window to trigger repairs.")

    @classmethod
    def run(cls):
        """
        Run the cassandra repairs checks.
        :return:
        """
        raise_alert = True
        if os.path.isfile(REPAIR_STATUS_FILE):
            resolve_sensu_alert(SENSU_ALERT_JOB_NOT_RUNNING)
            with open(REPAIR_STATUS_FILE) as file:
               json_data = json.loads(file.read())
            repair_status = ''
            lastupdate = datetime.datetime.strptime(json_data["updated"], "%Y-%m-%dT%H:%M:%S.%f")
            lastupdate_timediff = datetime.datetime.utcnow() - lastupdate
            num_failed =len(json_data["failed_repairs"])
            if lastupdate_timediff.total_seconds() > TIME_DIFF and json_data["finished"] is None:
                cls.fix_hung_repair()
                raise_alert = False
            elif num_failed > 0:
                cls.fix_failed_repair()
                raise_alert = False
            else:
                if json_data["finished"]:
                    lastfinish = datetime.datetime.strptime(json_data["finished"], "%Y-%m-%dT%H:%M:%S.%f")
                    lastfinisd_timediff = datetime.datetime.utcnow() - lastfinish
                    if (lastfinisd_timediff.total_seconds() > EIGHT_DAYS_IN_SECONDS and lastfinisd_timediff.total_seconds() < NINE_DAYS_IN_SECONDS):
                        repair_status = 'Repair process not triggered from last 8 days '
                    elif lastfinisd_timediff.total_seconds() >= NINE_DAYS_IN_SECONDS :
                        repair_status = 'Repair process not triggered from last 9 days - HIGH PRIORITY ALERT !!!'
                    else:
                        raise_alert = False
                else:
                    raise_alert = False
            if raise_alert:
                cls.repair_status_alert(SENSU_ALERT_REPAIR_PROCESS, repair_status)
            else:
                resolve_sensu_alert(SENSU_ALERT_REPAIR_PROCESS)
        else:
            if os.path.isfile(REPAIR_NODE_BOOTSTRAP_DATE_FILE):
                with open(REPAIR_NODE_BOOTSTRAP_DATE_FILE, 'r') as f:
                    bootstrap_date = f.read()
                    if current_time > int(bootstrap_date) + SEVEN_DAYS_IN_SECONDS:
                        logger.error("Repair status file does not exist")
                        raise_sensu_alert(SENSU_ALERT_JOB_NOT_RUNNING, "Repair status file does not exist")
                    else:
                        logger.info("node was created less than 7 days ago, not triggering repair status file does not exist alert")
            else:
                logger.error("Repair status file does not exist")
                raise_sensu_alert(SENSU_ALERT_JOB_NOT_RUNNING, "Repair status file does not exist")


if __name__ == '__main__':
    CheckRepairs.run()

