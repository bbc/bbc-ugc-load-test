import pprint
import json
import jsonpickle
from troposphere import Parameter, Ref
from cosmosTroposphere import CosmosTemplate


t = CosmosTemplate(total_az=2,region="eu-west-2",description="UgcUpload loadtest", component_name="ugc-upload-load-test-component", project_name='ugc-upload-test')

del t.parameters["ElbHealthCheckGracePeriod"]
del t.parameters["UpdatePauseTime"]

updateMaxBatchSize = t.parameters["UpdateMaxBatchSize"]
updateMaxBatchSize.Default = "0"

updateMinInService = t.parameters["UpdateMinInService"]
updateMinInService.Default = "0"

ami_id = t.parameters['ImageId']
ami_id.Default = 'ami-0e8fb02fa7ec321b6'

cNameEntryParameter = t.parameters['CnameEntry']
cNameEntryParameter.Default ='ugc-loadtest.int'

domainNameBase = t.parameters['DomainNameBase']
domainNameBase.Default = 'c7dff5ab13c48206.xhst.bbci.co.uk.'

environment = t.parameters['Environment']
environment.Default = 'int'

maxSize = t.parameters["MaxSize"]
maxSize.Default = "2"

minSize = t.parameters["MinSize"]
minSize.Default = "0"

componentAutoScalingGroup = t.resources['ComponentAutoScalingGroup']
componentAutoScalingGroup.UpdatePolicy.AutoScalingRollingUpdate.PauseTime = "PT0S"
componentAutoScalingGroup.HealthCheckGracePeriod = 0
#componentAutoScalingGroup.HealthCheckType = ""


print(t.to_json())
