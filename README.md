# Running load tests
### Prerequisites
 * Use your Mac, not the sandbox.
 * Update to python version >= 3.4.5 You can check you current version with
   `python -V` and either install/upgrade with `brew install python` or `brew
   upgrade python`
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
 * Generate AWS access keys for your IAM user in *otg-md-dev* account, then
 place the credentials in `~/.aws/credentials`, in the format:
```dosini
[default]
aws_access_key_id = <YOUR_KEY>
aws_secret_access_key = <YOUR_SECRET>
```


### Running a load test
```shell
# Provision infrastructure
./ltctl.py spinup -n 2 -t m4.large

# View infrastructure status
./ltctl.py status

# Run the load test described in ./ec2-package/scenarios/gtm/milestone1/GTMAvailabilityAll.scala
./ltctl.py run ugc.UGCBasicSimulation

# After running the GTMAvailabilityAll loadtest run report generation manually 
# (You will be prompted after running the loadtest)
./ltctl.py genreport "CCYY-MM-DD.HH-mm-ss.GTMAvailabiliyAll"

# Up generated report to S3 bucket 
./ltctl.py uploadreport "CCYY-MM-DD.HH-mm-ss.GTMAvailabiliyAll"

# Tear down infrastructure
./ltctl.py spindown

# GTM specific (wraps ltctl run command)
make <test type>

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
[int-md-loadtest-infrastructure](https://admin.live.bbc.co.uk/cosmos/env/int/component/ugc-loadtest/stacks)
stack contains an AutoScaling group that is only used during a load test. At
all other times there should be no instances in service.

Note that you will need the [Cosmos
Troposhere](https://github.com/bbc/cosmos-troposphere/) library to build the
templates within `infrastructure/`

### Gatling Carbon Server 
To change the host where the Carbon server is located
Crack open `loadtest/ec2-package/conf/gatling.conf` and change
```
 graphite {
      --snip--
      host = "gtm-graphite-internal.test.api.bbci.co.uk"
      --snip--
    }
```
And then crack open `loadtest/ec2-package/tools/configure` and change
```
LoadPlugin write_graphite
<Plugin write_graphite>
    <Node "gatling">
        Host "gtm-graphite-internal.test.api.bbci.co.uk"
        --snip--
    </Node>
</Plugin>
```


