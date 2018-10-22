from cosmosTroposphere import CosmosTemplate


class TemplateBuilder:

    @staticmethod
    def buildtemplate(t):
        del t.parameters["ElbHealthCheckGracePeriod"]
        del t.parameters["UpdatePauseTime"]

        updatemaxbatchsize = t.parameters["UpdateMaxBatchSize"]
        updatemaxbatchsize.Default = "0"

        updatemininservice = t.parameters["UpdateMinInService"]
        updatemininservice.Default = "0"

        ami_id = t.parameters['ImageId']
        ami_id.Default = 'ami-0e8fb02fa7ec321b6'

        cNameentryparameter = t.parameters['CnameEntry']
        cNameentryparameter.Default = 'ugc-loadtest.int'

        domainnamebase = t.parameters['DomainNameBase']
        domainnamebase.Default = 'c7dff5ab13c48206.xhst.bbci.co.uk.'

        environment = t.parameters['Environment']
        environment.Default = 'int'

        maxsize = t.parameters["MaxSize"]
        maxsize.Default = "2"

        minsize = t.parameters["MinSize"]
        minsize.Default = "0"

        componentautoscalinggroup = t.resources['ComponentAutoScalingGroup']
        componentautoscalinggroup.UpdatePolicy.AutoScalingRollingUpdate.PauseTime = "PT0S"
        componentautoscalinggroup.HealthCheckGracePeriod = 0
        # componentAutoScalingGroup.HealthCheckType = ""


if __name__ == '__main__':
    t = CosmosTemplate(total_az=2, region="eu-west-2", description="UgcUpload loadtest",
                       component_name="ugc-upload-load-test-component", project_name='ugc-upload-test')
    templateBuilder = TemplateBuilder()
    templateBuilder.buildTemplate(t)
    print(t.to_json())
