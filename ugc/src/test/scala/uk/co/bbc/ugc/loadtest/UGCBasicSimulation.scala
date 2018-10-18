package uk.co.bbc.ugc.loadtest

import io.gatling.core.Predef._
import io.gatling.http.Predef._

class UGCBasicSimulation extends Simulation {

  val httpProtocol = http
    .baseUrl("https://www.int.bbc.co.uk")
    .proxy(Proxy("www-cache.reith.bbc.co.uk",80).httpsPort(80))


  val scn = scenario("BasicSimulation") // 7
    .exec(Login.login, Upload.upload)

  setUp( // 11
    scn.inject(atOnceUsers(1)) // 12
  ).protocols(httpProtocol)

}
