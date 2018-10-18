package uk.co.bbc.ugc.loadtest

import io.gatling.recorder.GatlingRecorder
import io.gatling.recorder.config.RecorderPropertiesBuilder

object Recorder extends App {

	val props = new RecorderPropertiesBuilder
	//props.(IDEPathHelper.recorderOutputDirectory.toString)
	props.simulationPackage("bbc")
	props.simulationsFolder(IDEPathHelper.bodiesDirectory.toString)

	GatlingRecorder.fromMap(props.build, Some(IDEPathHelper.recorderConfigFile))
}
