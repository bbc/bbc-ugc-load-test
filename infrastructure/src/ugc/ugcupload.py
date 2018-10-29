from cosmosTroposphere import CosmosTemplate
from troposphere import Base64, Join
from troposphere.policies import UpdatePolicy, AutoScalingReplacingUpdate

from awacs.aws import Allow, Statement
from awacs.s3 import ListBucket, GetObject, GetObjectVersion, ListBucketVersions

class TemplateBuilder:

    @staticmethod
    def buildtemplate(t):
        del t.parameters["UpdatePauseTime"]

        #
        # updatemaxbatchsize = t.parameters["UpdateMaxBatchSize"]
        # updatemaxbatchsize.Default = "0"
        #
        # updatemininservice = t.parameters["UpdateMinInService"]
        # updatemininservice.Default = "0"

        ami_id = t.parameters['ImageId']
        ami_id.Default = 'ami-09fd46debba20791d'

        cNameentryparameter = t.parameters['CnameEntry']
        cNameentryparameter.Default = 'ugc-loadtest.int'

        domainnamebase = t.parameters['DomainNameBase']
        domainnamebase.Default = 'c7dff5ab13c48206.xhst.bbci.co.uk.'

        environment = t.parameters['Environment']
        environment.Default = 'int'

        maxsize = t.parameters["MaxSize"]
        maxsize.Default = "0"

        minsize = t.parameters["MinSize"]
        minsize.Default = "0"

        componentautoscalinggroup = t.resources['ComponentAutoScalingGroup']
        #componentautoscalinggroup.UpdatePolicy.AutoScalingRollingUpdate.PauseTime = "PT0S"
        componentautoscalinggroup.UpdatePolicy = UpdatePolicy(
            AutoScalingReplacingUpdate=AutoScalingReplacingUpdate(
                WillReplace=True,
            ))
        # componentautoscalinggroup.HealthCheckGracePeriod = 0
        # componentAutoScalingGroup.HealthCheckType = ""

        componentLaunchConfiguration = t.resources['ComponentLaunchConfiguration']

        #NOTE: This appears not to be working
        componentLaunchConfiguration.UserData=Base64(Join('', [
            "# Installing awcsli \n",
            "sudo yum --enablerepo=extras install epel-release -y \n",
            "sudo yum update -y \n",
            "sudo yum install -y python-pip \n",
            "sudo pip install awscli --upgrade \n",
        ]))


        policyDocument =  t.resources["ComponentPolicy"].PolicyDocument
        policyDocument.Statement.append(
            Statement(
                Effect=Allow,
                Action=[ListBucket, ListBucketVersions],
                Resource=["*"]))

        policyDocument.Statement.append(
            Statement(
                Effect=Allow,
                Action=[GetObject, GetObjectVersion],
                Resource=["*"]))






if __name__ == '__main__':
    t = CosmosTemplate(total_az=2, region="eu-west-2", description="UgcUpload loadtest",
                       component_name="ugc-upload-load-test-component", project_name='ugc-upload-test')

    TemplateBuilder().buildtemplate(t)
    print(t.to_json())
