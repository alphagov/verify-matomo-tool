# How to replay missing Matomo requests to Matomo

>**GOV.UK Verify has closed**
>
>This repository is out of date and has been archived

You need to install [gds-cli](https://github.com/alphagov/gds-cli) on your computer before following these steps to get missing Matomo requests from AWS CloudWatch and replay them to Matomo.

1. Run the following command to obtain a session token from the AWS Security Token Service in Tools AWS account using gds-cli.
    ```
    eval "$(gds auth aws_verify_tools)"
    ```
2. Run the following command to build a docker image.
    ```
    docker build -t my-python-app .
    ```
3. Run the following command to get the file containing missing Matomo requests. You need to specify START_DATE and NUM_OF_DAYS before you run the command.
    ```
    docker run -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN -e AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION -e START_DATE=2019-04-02T00:00:00+00:00 -e NUM_OF_DAYS=1 -v $(pwd):/app -it --rm --name my-running-app my-python-app
    ```
4. If the newly generated file is not empty, run the following command to clone `matomo-log-analytics` GitHub repository.
    ```
    git clone git@github.com:adityapahuja/matomo-log-analytics.git
    ```
5. Go to `matomo-log-analytics` directory.
    ```
    cd matomo-log-analytics
    ```
6. Run the following command to replay missing Matomo requests to Matomo. API Authentication Token can be found under Personal Settings section in Matomo Administration page.
    ```
    python2.7 ./import_logs.py --token-auth='<api-authentication-token>' --url=<matamo url> --enable-http-errors --enable-http-redirects --enable-static --enable-bots --replay-tracking ../20190402_20190402_matomo_requests.json
    ```
    Its ouput will display like this.
    ```
    Logs import summary
    -------------------
    
        1 requests imported successfully
        0 requests were downloads
        0 requests ignored:
            0 HTTP errors
            0 HTTP redirects
            0 invalid log lines
            0 filtered log lines
            0 requests did not match any known site
            0 requests did not match any --hostname
            0 requests done by bots, search engines...
            0 requests to static resources (css, js, images, ico, ttf...)
            0 requests to file downloads did not match any --download-extensions
    
    Website import summary
    ----------------------
    
        1 requests imported to 1 sites
            1 sites already existed
            0 sites were created:
    
        0 distinct hostnames did not match any existing site:
    
    
    
    Performance summary
    -------------------
    
        Total time: 0 seconds
        Requests imported per second: 6.62 requests per second
    
    Processing your log data
    ------------------------
    
        In order for your logs to be processed by Matomo, you may need to run the following command:
         ./console core:archive --force-all-websites --force-all-periods=315576000 --force-date-last-n=1000 --url='<matamo-url>'
     ```
