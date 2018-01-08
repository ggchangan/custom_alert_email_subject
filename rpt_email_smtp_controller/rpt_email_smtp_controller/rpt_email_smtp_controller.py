import re
from abc import abstractmethod

from airflow.utils.email import send_email_smtp
from airflow import configuration
#from airflow.utils.log.logging_mixin import LoggingMixin
from airflow.utils.logging import LoggingMixin


def send_email_smtp_controller(to, subject, html_content, files=None, dryrun=False, cc=None, bcc=None,
                               mime_subtype='mixed'):
    log = LoggingMixin().logger

    custom_alerts = get_custom_alerters()
    email_context = EmailContext(subject, html_content)
    for custom_alert in custom_alerts:
        if custom_alert.sure_called_by_me(email_context):
            log.info("Sent an alert email by custom %s", custom_alert.__class__)
            custom_alert.send_email(to, subject, html_content, files, dryrun, cc, bcc, mime_subtype)
            return

    log.info("Sent an alert email by default %s", "send_email_smtp")
    send_email_smtp(to, subject, html_content, files, dryrun, cc, bcc, mime_subtype)


"""
the factory method for all alerters
"""


def get_custom_alerters():
    custom_alerters = [RPTCustomEmailAlerter()]
    return custom_alerters


"""
the context of alert emails
"""


class EmailContext:
    def __init__(self, subject, html_content):
        self.subject = subject
        self.html_content = html_content

    def set_subject(self, subject):
        self.subject = subject

    def get_subject(self):
        return self.subject

    def set_html_content(self, html_content):
        self.html_content = html_content

    def get_html_content(self):
        return self.html_content


"""
Base class for all Alerters
"""


class CustomEmailAlerter:
    def __init__(self):
        pass

    @abstractmethod
    def sure_called_by_me(self, email_context): pass

    @abstractmethod
    def send_email(self, to, subject, html_content, files=None, dryrun=False, cc=None, bcc=None,
                   mime_subtype='mixed'): pass


class RPTCustomEmailAlerter(CustomEmailAlerter):
    def __init__(self):
        self.email_state = ""
        self.email_env = ""
        self.email_location = ""
        self.hostname = ""
        self.task = ""

    def sure_called_by_me(self, email_context):
        subject = email_context.get_subject()
        context = email_context.get_html_content()
        alert_found = subject.find("alert") != -1
        try_found = context.find("Try") != -1
        exception_found = context.find("Exception") != -1
        log_found = context.find("Log") != -1
        host_found = context.find("Host") != -1
        log_file_found = context.find("Log file") != -1
        mark_success_found = context.find("Mark success") != -1
        return alert_found & try_found & exception_found & \
               log_found & host_found & log_file_found & mark_success_found

    def send_email(self, to, subject, html_content, files=None, dryrun=False, cc=None, bcc=None, mime_subtype='mixed'):
        log = LoggingMixin().logger
        try:
            subject = self.get_subject(subject, html_content)
            send_email_smtp(to, subject, html_content, files, dryrun, cc, bcc, mime_subtype)
        except Exception, e:
            log.info("Custom alert email subject except", e.message, ", use original subject.")

    def get_subject(self, subject, html_content):
        lines = html_content.split("<br>")
        if len(lines) != 8:
            raise Exception("Invalid alert body!")

        try_line = lines[0]
        try_number_strs = re.findall(r"\d+\.?\d*", try_line)
        if len(try_number_strs) != 2:
            raise Exception("The first line of alert email body is invalid!")

        try_number = int(try_number_strs[0])
        max_tries = int(try_number_strs[1])

        self.task = subject[subject.find(':') + 1:]
        hostname_line = lines[4]
        self.hostname = hostname_line[hostname_line.find(':') + 2:]
        self.email_state = "FAIL" if try_number >= max_tries else "WARN"

        self.email_env = self.__get_email_env()

        fw_rpt_standard_location_dict = {'PRD': 'NYC', 'STG': 'NYC', 'DEV': 'PEK', 'UNKNOWN': 'UNKNOWN'}
        if fw_rpt_standard_location_dict.__contains__(self.email_env):
            self.email_location = fw_rpt_standard_location_dict[self.email_env]
        else:
            self.email_location = "DEV"

        return self.__format_subject()

    def __get_email_env(self):
        return configuration.get('email', 'EMAIL_ENV').upper()

    def __format_subject(self):
        return "[{self.email_state}][{self.email_env}][ANALYTICS][{self.hostname}][{self.email_location}] Airflow " \
               "alert:{self.task}".format(**locals())
