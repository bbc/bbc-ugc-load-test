package uk.co.bbc.ugc.loadtest

import io.gatling.core.Predef._
import io.gatling.http.Predef._

object Upload {

  val upload = exec(http("upload")
      .post("/ugc/send/c12577411")
      .bodyPart(RawFileBodyPart("data", "data/Clocktower_Panorama_20080622_1mb.jpg")))

}
