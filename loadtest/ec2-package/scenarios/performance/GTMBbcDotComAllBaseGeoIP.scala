package performance

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._

import io.gatling.core.structure.ChainBuilder
import java.util.concurrent.ThreadLocalRandom

class GTMBbcDotComAllBaseGeoIP(val run_time: Int = 15, val requests_per_second_per_scenario: Int = 20, val base_url: String) extends Simulation {

   def rand_octets():ChainBuilder = {
        return exec(
            _.set("octet_1", ThreadLocalRandom.current.nextInt(0, 255))
            .set("octet_2", ThreadLocalRandom.current.nextInt(0, 255))
            .set("octet_3", ThreadLocalRandom.current.nextInt(0, 255))
            .set("octet_4", ThreadLocalRandom.current.nextInt(0, 255))
        )
    }

  val num_instances = Integer.getInteger("numEC2Instances")

  val news_expected_requests_per_second = requests_per_second_per_scenario / num_instances

  val sport_expected_requests_per_second = requests_per_second_per_scenario / num_instances

  val world_expected_requests_per_second = requests_per_second_per_scenario / num_instances

  val earth_expected_requests_per_second = requests_per_second_per_scenario / num_instances

  val total_expected_requests_per_second = news_expected_requests_per_second
                                         + sport_expected_requests_per_second
                                         + world_expected_requests_per_second
                                         + earth_expected_requests_per_second

  val rampUpTime = 1

  val httpConf = http
    .baseURL(base_url)
    .acceptHeader("text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
    .doNotTrackHeader("1")
    .acceptLanguageHeader("en-GB,en-US;q=0.8,en;q=0.6")
    .acceptEncodingHeader("gzip, deflate")
    .userAgentHeader("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36; SYNTHETIC")

  val scn_news = scenario("news")
    .exec(rand_octets)
    .exec(http("news")
    .get("/news")
    .header("my_ip", "${octet_1}.${octet_2}.${octet_3}.${octet_4}"))

  val scn_sport = scenario("sport")
    .exec(rand_octets)
    .exec(http("sport")
    .get("/sport")
    .header("my_ip", "${octet_1}.${octet_2}.${octet_3}.${octet_4}"))

  val scn_world = scenario("world")
    .exec(rand_octets)
    .exec(http("world")
    .get("/news/world-us-canada-44434558")
    .header("my_ip", "${octet_1}.${octet_2}.${octet_3}.${octet_4}"))

  val scn_earth = scenario("earth")
    .exec(rand_octets)
    .exec(http("earth")
    .get("/earth/uk")
    .header("my_ip", "${octet_1}.${octet_2}.${octet_3}.${octet_4}"))

  setUp(
    scn_news.inject(
      //rampUsersPerSec(1) to(news_expected_requests_per_second) during(rampUpTime minutes),
      constantUsersPerSec(news_expected_requests_per_second) during(run_time minutes)
    ),
    scn_sport.inject(
      //rampUsersPerSec(1) to(sport_expected_requests_per_second) during(rampUpTime minutes),
      constantUsersPerSec(sport_expected_requests_per_second) during(run_time minutes)
    ),
    scn_world.inject(
      //rampUsersPerSec(1) to(world_expected_requests_per_second) during(rampUpTime minutes),
      constantUsersPerSec(world_expected_requests_per_second) during(run_time minutes)
    ),
    scn_earth.inject(
      //rampUsersPerSec(1) to(world_expected_requests_per_second) during(rampUpTime minutes),
      constantUsersPerSec(world_expected_requests_per_second) during(run_time minutes)
    )
  ).protocols(
    httpConf
  ).maxDuration(run_time minutes)
//     .throttle(
//      reachRps(total_expected_requests_per_second) in (rampUpTime minutes), holdFor (run_time minutes)
//     )
}
