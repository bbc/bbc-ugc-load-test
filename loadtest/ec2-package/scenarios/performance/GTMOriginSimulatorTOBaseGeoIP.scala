package performance

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._

import io.gatling.core.structure.ChainBuilder
import java.util.concurrent.ThreadLocalRandom

class GTMOriginSimulatorTOBaseGeoIP(val run_time: Int = 15, val requests_per_second_per_scenario: Int = 20, val base_url: String) extends Simulation {

   def rand_octets():ChainBuilder = {
        return exec(
            _.set("octet_1", ThreadLocalRandom.current.nextInt(0, 255))
            .set("octet_2", ThreadLocalRandom.current.nextInt(0, 255))
            .set("octet_3", ThreadLocalRandom.current.nextInt(0, 255))
            .set("octet_4", ThreadLocalRandom.current.nextInt(0, 255))
        )
    }

    // val gtmUrl = csv("lbh/live_logs.txt").random

  val num_instances = Integer.getInteger("numEC2Instances")

  val to1024_expected_requests_per_second = requests_per_second_per_scenario / num_instances

  val total_expected_requests_per_second = to1024_expected_requests_per_second 

  val rampUpTime = 2

  val httpConf = http
    .baseURL(base_url)
    .acceptHeader("text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
    .doNotTrackHeader("1")
    .acceptLanguageHeader("en-GB,en-US;q=0.8,en;q=0.6")
    .acceptEncodingHeader("gzip, deflate")
    .userAgentHeader("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36; SYNTHETIC")
    .header("Host", "origin-simulator.example.org")

    //.check(header("x-bbc-edge-country").not("**"))

  val scn_to1024 = scenario("TO-1024")
    .exec(rand_octets)
    .exec(http("to1024")
    .get("/gtm-test-objects/1024.bin")
    .header("my_ip", "${octet_1}.${octet_2}.${octet_3}.${octet_4}"))


  setUp(
    scn_to1024.inject(
      rampUsersPerSec(1) to(to1024_expected_requests_per_second) during(rampUpTime minutes),
      constantUsersPerSec(to1024_expected_requests_per_second) during(run_time minutes)
    )
  ).protocols(
    httpConf
  ).maxDuration(run_time minutes)
//     .throttle(
//      reachRps(total_expected_requests_per_second) in (rampUpTime minutes), holdFor (run_time minutes)
//     )
}
