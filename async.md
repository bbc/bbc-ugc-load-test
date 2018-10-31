In order to run the tests:

If you want to be notified when the tests have completed:
When running the test in asyn mode: ssm is used to store configuration
information which is used by the test to determine when the tests have completed:

Below is an example of the config:

```
aws ssm get-parameter --name "/ugcloadtest/config"
{
    "Parameter": {
        "Version": 27,
        "Type": "StringList",
        "Name": "/ugcloadtest/config",
        "Value": "state=None,startTime=None,endTime=None,instances=None"
    }
}
```
state =[start,complete,None]
start : The tests has started
startTime: The time the test started
endTime: The time the test ended
instances: The number of instances.


After each tests completes:
`aws cloudwatch put-metric-data --region eu-west-2 --namespace UGC_GATLING_SIMULATION --metric-name "RESULTS" --timestamp $cur_time --value 1`
After each instance completes it puts this information into cloudwatch.

The dashboard uses cloudwatch and ssm parameter to display the status of the tests:
[Refer to the screen shot below](dashboard.png)

