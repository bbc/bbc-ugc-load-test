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
 * Create a `ltctl.local.conf` file with the following config, changing the
   paths to your pem_cert, pem_key and ssh_format as needed:
```dosini
[ltctl]
pem_cert=/Users/woolda01/BBC/Certificates/alistair-wooldrige-dev-cert-expires-14-09-2016.crt.pem
pem_key=/Users/woolda01/BBC/Certificates/alistair-wooldrige-dev-cert-expires-14-09-2016.key.pem

#
# Override this based on how you would SSH into instances.
# ssh_format={ip},{region}
#
ssh_format={ip},{region}

region=eu-west-1
stack_name=int-gtm-loadtest-main
results_bucket=gtm-load-tests
cosmos=https://api.live.bbc.co.uk/cosmos/env/int/component/gtm-loadtest

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

# Create restricted bandwidth:
# maxbandwidth: The maximum bandwidth
# bandwidthclass: The bandwidth which will be used by the test
# bandwidthdefaultcalss: The rest of t
#
# To cause test to use 1500kb bandwidth on port 91
./ltctl.py bandwidth 3000 1500 2500 91
./ltclt.py bandwidth <maxbandwidth> <bandwidthclass> <bandwidthdefaultclass> <port>

```

### Running a load test
```shell
# Provision infrastructure
./ltctl.py spinup -n 2 -t m4.large

# View infrastructure status
./ltctl.py status

# Run the load test described in ./ec2-package/scenarios/ugc/UGCBasicSimulation.scala
./ltctl.py run ugc.UGCBasicSimulation

# After running the loadtest run report generation manually 
# (You will be prompted after running the loadtest)
./ltctl.py genreport

# Up generated report to S3 bucket 
./ltctl.py uploadreport

# Tear down infrastructure
./ltctl.py spindown


```

# Tips and tricks

### Debug logging
Screwed something up in a scenario and want more detailed error information?

Crack open `loadtest/ec2-package/conf/logback.xml` and change
`<root level="WARN">` to `<root level="DEBUG">`.


# Other things in this repo
### What is the RPM for?
The RPM (crudely) packages gatling under `/opt/gatling` and also installs
utilities such as lsof/iptraf.

### Infrastructure
The main
[int-ugc-loadtest-infrastructure](https://admin.live.bbc.co.uk/cosmos/env/int/component/ugc-loadtest/stacks)
stack contains an AutoScaling group that is only used during a load test. At
all other times there should be no instances in service.

