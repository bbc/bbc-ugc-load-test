import pprint
import json
import jsonpickle

from cosmosTroposphere import CosmosTemplate
t = CosmosTemplate(total_az=2,region="eu-west-2",description="Describe your stack there", component_name="ugc-upload-load-test-component", project_name='ugc-upload-test')


componentAutoScalingGroup = t.resources['ComponentAutoScalingGroup']

componentAutoScalingGroup.MinSize = 0
componentAutoScalingGroup.MaxSize = 2

componentAutoScalingGroup.DesiredCapacity = 0
componentAutoScalingGroup.HealthCheckGracePeriod = 0
#componentAutoScalingGroup.HealthCheckType = ""
componentAutoScalingGroup.UpdatePolicy.AutoScalingRollingUpdate.MaxBatchSize = 1
componentAutoScalingGroup.UpdatePolicy.AutoScalingRollingUpdate.MinInstancesInService = 0

del t.parameters["DesiredCapacity"]
del t.parameters["ElbHealthCheckGracePeriod"]
del t.parameters["MaxSize"]
del t.parameters["MinSize"]
del t.parameters["UpdateMaxBatchSize"]
del t.parameters["UpdateMinInService"]

ami_id = t.parameters['ImageId']
ami_id.Default = 'ami-0e8fb02fa7ec321b6'
cNameEntryParameter = t.parameters['CnameEntry']
cNameEntryParameter.Default ='ugc-loadtest.int'

domainNameBase = t.parameters['DomainNameBase']
domainNameBase.Default = 'c7dff5ab13c48206.xhst.bbci.co.uk.'

environment = t.parameters['Environment']
environment.Default = 'int'

print(t.to_json())
