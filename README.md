# Running load tests
### Prerequisites
 * Use your Mac, not the sandbox.
 * Update to python version >= 3.4.5 You can check you current version with
   `python -V` and either install/upgrade with `brew install python` or `brew
   upgrade python`
 * Create virtual environment
   ```
    sudo yum install python34-devel libcurl-devel
    sudo pip3.4 install virtualenv
    python3.4 -m virtualenv ~/loadtest
    source ~/loadtest/bin/activate
    ```
 * Change into the `loadtest/` directory: `cd loadtest/`.
 * You may (probably do) want to create a virtual environment and install pips requirements there
    * Ensure python `pip` is installed on your machine and install the
   requirements: `sudo pip install -r requirements.txt`.
    * Note: If having problems installing pycurl: Remove from `requirements.txt` and do the following:
        remove existing pycurl installation
	```
	pip uninstall pycurl
	export PYCURL_SSL_LIBRARY=openssl
	pip install pycurl
	```
    * Note: [If still not working try this](https://stackoverflow.com/questions/47888757/importerror-pycurl-libcurl-link-time-ssl-backend-openssl-is-different-from-c)

   [Also follow this link to install troposhere](https://confluence.dev.bbc.co.uk/display/RMServices/Gap+Analysis+-+CosmosTroposhere)
   
 * Create a `ltctl.local.conf` from coping file with the following config, changing the
   paths to your pem_cert, pem_key and ssh_format as needed: [Follow instructions in here to create the keys](openssl.md):

 * There are two modes in running the test: Async and non async.
 
	*  Non Async: The output of the tests are piped to your terminal..if you exit the terminal it will terminate the tests.
	*  Async: The tests run in the background refer to [Dashboard Monitoring](async.md) for information about how to determine when the tests have completed.

```dosini
	  
[ltctl]
pem_cert=/Users/baahk01/workspace/ugc-load-test/bbc_cert.crt.pem
pem_key=/Users/baahk01/workspace/ugc-load-test/bbc_cert.key.pem


#
# Override this based on how you would SSH into instances. E.g. without r,
# ssh_format={ip},{region}
#
ssh_format={ip},{region}

region=eu-west-2
stack_name=int-ugc-loadtest-app
results_bucket=ugcupload-load-test
cosmos=https://api.live.bbc.co.uk/cosmos/env/int/component/ugc-loadtest
cosmosbaseurl=https://api.live.bbc.co.uk/cosmos
awsaccount=546933502184
cosmoscomponent=ugc-loadtest
testdata=s3://ugc-test-data/gatling
certlocation=/Users/baahk01/workspace/bbc_cert.p12
gatlingtestsrc=/Users/baahk01/workspace/isite-testing-tools/gatling/ugc/src
systemundertest=212.58.228.27:443

[jars]
1=http://central.maven.org/maven2/io/suzaku/boopickle-shapeless_2.12/1.3.0/boopickle-shapeless_2.12-1.3.0.jar
2=http://central.maven.org/maven2/io/netty/netty-tcnative/2.0.19.Final/netty-tcnative-2.0.19.Final.jar

```
 * Generate AWS access keys
```shell
# Worm hole credentials. e.g fetch-aws-creds.py 546933502184
fetch-aws-creds.py <aws_account_id>
# In the file ~/.aws/credentials make sure the region is set correctly. e.g eu-west-2

```

### Environment Preparation
```shell

# Create stack
./ltctl.py createstack

# Delete stack
./ltctl.py deletestack

# Copy cert to instance
./ltctl.py cert

# deploy to int
./ltctl.py release

# Describe the stack
./ltclt.py describestack

# Get simulation files
./ltclt.py prepare

# Used to tell the dashboard test has completed
./ltctl.py completemonitoring

# Used to tell the dashboard not to display test information
./ltctl.py turnoffmonitoring

# Create restricted bandwidth:
# maxbandwidth: The maximum bandwidth
# bandwidthclass: The bandwidth which will be used by the test
# bandwidthdefaultcalss: The rest of t
#
# To cause test to use 500kbs bandwidth on port 91
./ltctl.py bandwidth 3000kbps 500kbps 2500kbps 91
./ltclt.py bandwidth <maxbandwidth> <bandwidthclass> <bandwidthdefaultclass> <port>

```

### Running a load test
```shell
# Provision infrastructure
./ltctl.py spinup -n 2 -t m4.large

# Start jvm monitoring of system undertest
./ltctl.py jvmmonitoring

# Fetch jvm monitoring 
./ltctl.py jvmmonitoringlogs

# View infrastructure status
./ltctl.py status

# Async: Run the load test described in ./ec2-package/scenarios/ugc/UGCBasicSimulation.scala 
./ltctl.py run ugc.UGCBasicSimulation -t async  -b 1

# Async: Get logs
./ltctl.py fetchasynclogs

# Non Async: Run the load test described in ./ec2-package/scenarios/ugc/UGCBasicSimulation.scala 
./ltctl.py run ugc.UGCBasicSimulation -t foreground  -b 1

# After running the loadtest run report generation manually 
# (You will be prompted after running the loadtest)
./ltctl.py genreport

# Upload generated report to S3 bucket 
./ltctl.py uploadreport

# Tear down infrastructure
./ltctl.py spindown

```
### Monitoring async test via dashboard

```
# To update ssm parameter to indicate tests have started
./ltctl.py startmonitoring 

# To update ssm parameter to indicate tests have concluded
./ltctl.py completemonitoring

#  To update ssm parameter to indicate are no longer running
./ltctl.py turnoffmonitoring
```

### JVM monitoring
```
# To start jvm monitoring of the ugc instances
./ltctl.py jvmmonitoring

# To fetch the logs
./ltctl.py jvmmonitoringlogs

# To make the logs more readable
./ltctl.py modifyjstat

```
### Lambda Notifications

# Disable the lambda notification on the bucket
./ltctl.py disablenotifications [-v]

# Enable the lambda notification on the bucket
./ltctl.py enablenotifications [-v]

# Tips and tricks

### Debug logging
Screwed something up in a scenario and want more detailed error information?

Crack open `loadtest/ec2-package/conf/logback.xml` and change
`<root level="WARN">` to `<root level="DEBUG">`.


# Other things in this repo
### What is the RPM for?
The RPM (crudely) packages gatling under `/opt/gatling` and also installs
utilities such as lsof/iptraf.
p
### Infrastructure
The main
[int-ugc-loadtest-infrastructure](https://admin.live.bbc.co.uk/cosmos/env/int/component/ugc-loadtest/stacks)
stack contains an AutoScaling group that is only used during a load test. At
all other times there should be no instances in service.

