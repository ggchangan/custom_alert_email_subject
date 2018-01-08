#!/usr/bin/env bash

# python alert_email_subject.py
python ~/airflow/dags/alert_email_subject.py
airflow backfill alert_email_subject -s 2017-12-01 -e 2018-01-01
