from datetime import datetime, timedelta, timezone
import os
import boto3
import time
from _decimal import Decimal

NUM_OF_DAYS = 'NUM_OF_DAYS'
START_DATE = 'START_DATE'


def print_unset_env_variable_error_and_exit(environment_variable):
    print(environment_variable, " environment variable is not set.")
    exit(1)


def validate_environment_variables():
    if os.getenv(START_DATE) is None:
        print_unset_env_variable_error_and_exit(START_DATE)
    if os.getenv(NUM_OF_DAYS) is None:
        print_unset_env_variable_error_and_exit(NUM_OF_DAYS)


def get_start_date():
    try:
        return datetime.strptime(os.getenv(START_DATE), '%Y-%m-%dT%H:%M:%S%z')
    except ValueError:
        print("START_DATE has an invalid date and time format. It should be in %Y-%m-%dT%H:%M:%S%z")
        exit(1)


def get_number_of_days():
    try:
        return int(os.getenv(NUM_OF_DAYS))
    except ValueError:
        print("NUM_OF_DAYS has an invalid format. It should be in integers only")
        exit(1)


def wait_for_the_query_to_complete(response):
    queryId = response['queryId']
    status = 'Running'
    while status != 'Complete':
        response = client.get_query_results(queryId=queryId)
        status = response['status']
        time.sleep(1)
    return response


def run_query(start_timestamp, end_timestamp):
    return client.start_query(
        logGroupName='matomo',
        startTime=int(start_timestamp.timestamp() * 1000),
        endTime=int(end_timestamp.timestamp() * 1000),
        queryString=
        """fields @message
        | sort @timestamp asc
        | filter @logStream like /matomo-nginx/
        | filter status!='200'
        | filter status!='204'
        | filter user_agent!='ELB-HealthChecker/2.0'
        | filter path like /idsite=1/
        | filter path like /rec=1/""",
        limit=10000
    )


def write_requests_to_a_file(response, start_date, end_date, output_filename):
    with open(output_filename, 'a+') as f:
        for messages in response['results']:
            for message in messages:
                if message['field'] == '@message':
                    f.write(message['value'] + '\n')
                    break


if __name__ == '__main__':
    validate_environment_variables()

    client = boto3.client('logs')

    start_date = get_start_date()
    num_of_days = get_number_of_days()
    end_date = start_date + timedelta(days=num_of_days) + timedelta(microseconds=-1)

    OUTPUT_FILENAME = start_date.strftime('%Y%m%d') + '_' + end_date.strftime('%Y%m%d') + '_matomo_requests.json'
    if os.path.exists(OUTPUT_FILENAME):
        os.remove(OUTPUT_FILENAME)

    for days in range(0, get_number_of_days()):
        current_date = start_date + timedelta(days=(days))
        end_date = current_date + timedelta(days=1, microseconds=-1)

        start_timestamp = current_date.replace(tzinfo=timezone.utc).timestamp()
        end_timestamp = end_date.replace(tzinfo=timezone.utc).timestamp()

        duration = (end_date - current_date).total_seconds()
        offset = 60 * 5
        num_of_iterations = int(duration / offset)

        for i in range(num_of_iterations):
            response = run_query(datetime.utcfromtimestamp(start_timestamp),
                                 (datetime.utcfromtimestamp((start_timestamp + offset)) + timedelta(microseconds=-1)))
            response = wait_for_the_query_to_complete(response)
            write_requests_to_a_file(response, start_date, end_date, OUTPUT_FILENAME)
            start_timestamp = start_timestamp + offset
        if Decimal(duration) / Decimal(offset) % Decimal(1) != Decimal(0):
            response = run_query(datetime.utcfromtimestamp(start_timestamp),
                                 (datetime.utcfromtimestamp((start_timestamp + offset)) + timedelta(microseconds=-1)))
            response = wait_for_the_query_to_complete(response)
            write_requests_to_a_file(response, start_date, end_date, OUTPUT_FILENAME)
