from airflow.models import *


def email_alert(self, exception, is_retry=False):
    task = self.task
    hostname = self.hostname
    email_state = "FAIL" if self.try_number >= self.max_tries else "WARN"
    email_env = self.__get_email_env()

    fw_rpt_standard_location_dict = {'PRD': 'NYC', 'STG': 'NYC', 'DEV': 'PEK', 'UNKNOWN': 'UNKNOWN'}
    if fw_rpt_standard_location_dict.__contains__(self.email_env):
        email_location = fw_rpt_standard_location_dict[self.email_env]
    else:
        email_location = "DEV"

    title = __format_subject()
    exception = str(exception).replace('\n', '<br>')
    # For reporting purposes, we report based on 1-indexed,
    # not 0-indexed lists (i.e. Try 1 instead of
    # Try 0 for the first attempt).
    body = (
        "Try {try_number} out of {max_tries}<br>"
        "Exception:<br>{exception}<br>"
        "Log: <a href='{self.log_url}'>Link</a><br>"
        "Host: {self.hostname}<br>"
        "Log file: {self.log_filepath}<br>"
        "Mark success: <a href='{self.mark_success_url}'>Link</a><br>"
    ).format(try_number=self.try_number + 1, max_tries=self.max_tries + 1, **locals())
    send_email(task.email, title, body)


def __format_subject():
    return "[{self.email_state}][{self.email_env}][ANALYTICS][{self.hostname}][{self.email_location}] Airflow " \
           "alert:{self.task}".format(**locals())


TaskInstance.email_alert = email_alert
