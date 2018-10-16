package performance

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._

import io.gatling.core.structure.ChainBuilder
import java.util.concurrent.ThreadLocalRandom

class GTMOriginSimulatorAllBaseGeoIPCached(val run_time: Int = 15, val requests_per_second_per_scenario: Int = 20, val base_url: String) extends Simulation {

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

  val news404_expected_requests_per_second = requests_per_second_per_scenario / num_instances

  val news_expected_requests_per_second = requests_per_second_per_scenario / num_instances

  val sport_expected_requests_per_second = requests_per_second_per_scenario / num_instances

  val iplayer_expected_requests_per_second = requests_per_second_per_scenario / num_instances

  val weather_expected_requests_per_second = requests_per_second_per_scenario / num_instances

  val radio_expected_requests_per_second = requests_per_second_per_scenario / num_instances

  val homepage_expected_requests_per_second = requests_per_second_per_scenario / num_instances

  val total_expected_requests_per_second = news404_expected_requests_per_second 
                                            + news_expected_requests_per_second
                                            + sport_expected_requests_per_second
                                            + iplayer_expected_requests_per_second
                                            + weather_expected_requests_per_second
                                            + radio_expected_requests_per_second
                                            + homepage_expected_requests_per_second

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

  val scn_news404 = scenario("news404")
    .exec(rand_octets)
    .exec(http("news404")
    .get("/origin-simulator?page=news404&delay_min_msec=100&delay_max_msec=200&cache_control=public,max-age=30")
    .header("my_ip", "${octet_1}.${octet_2}.${octet_3}.${octet_4}"))

  val scn_news = scenario("news")
    .exec(rand_octets)
    .exec(http("news")
    .get("/origin-simulator?page=news&delay_min_msec=100&delay_max_msec=200&cache_control=public,max-age=30")
    .header("my_ip", "${octet_1}.${octet_2}.${octet_3}.${octet_4}"))

  val scn_sport = scenario("sport")
    .exec(rand_octets)
    .exec(http("sport")
    .get("/origin-simulator?page=sport&delay_min_msec=100&delay_max_msec=200&cache_control=public,max-age=30")
    .header("my_ip", "${octet_1}.${octet_2}.${octet_3}.${octet_4}"))

  val scn_iplayer = scenario("iplayer")
    .exec(rand_octets)
    .exec(http("iplayer")
    .get("/origin-simulator?page=iplayer&delay_min_msec=100&delay_max_msec=200&cache_control=public,max-age=30")
    .header("my_ip", "${octet_1}.${octet_2}.${octet_3}.${octet_4}"))

  val scn_weather = scenario("weather")
    .exec(rand_octets)
    .exec(http("weather")
    .get("/origin-simulator?page=weather&delay_min_msec=100&delay_max_msec=200&cache_control=public,max-age=30")
    .header("my_ip", "${octet_1}.${octet_2}.${octet_3}.${octet_4}"))

  val scn_radio = scenario("radio")
    .exec(rand_octets)
    .exec(http("radio")
    .get("/origin-simulator?page=radio&delay_min_msec=100&delay_max_msec=200&cache_control=public,max-age=30")
    .header("my_ip", "${octet_1}.${octet_2}.${octet_3}.${octet_4}"))

  val scn_homepage = scenario("homepage")
    .exec(rand_octets)
    .exec(http("homepage")
    .get("/origin-simulator?page=homepage&delay_min_msec=100&delay_max_msec=200&cache_control=public,max-age=30")
    .header("my_ip", "${octet_1}.${octet_2}.${octet_3}.${octet_4}"))

  setUp(
    scn_news404.inject(
      rampUsersPerSec(1) to(news404_expected_requests_per_second) during(rampUpTime minutes),
      constantUsersPerSec(news404_expected_requests_per_second) during(run_time minutes)
    ),
    scn_news.inject(
      rampUsersPerSec(1) to(news_expected_requests_per_second) during(rampUpTime minutes),
      constantUsersPerSec(news_expected_requests_per_second) during(run_time minutes)
    ),
    scn_sport.inject(
      rampUsersPerSec(1) to(sport_expected_requests_per_second) during(rampUpTime minutes),
      constantUsersPerSec(sport_expected_requests_per_second) during(run_time minutes)
    ),
    scn_iplayer.inject(
      rampUsersPerSec(1) to(iplayer_expected_requests_per_second) during(rampUpTime minutes),
      constantUsersPerSec(iplayer_expected_requests_per_second) during(run_time minutes)
    ),
    scn_weather.inject(
      rampUsersPerSec(1) to(weather_expected_requests_per_second) during(rampUpTime minutes),
      constantUsersPerSec(weather_expected_requests_per_second) during(run_time minutes)
    ),
    scn_radio.inject(
      rampUsersPerSec(1) to(radio_expected_requests_per_second) during(rampUpTime minutes),
      constantUsersPerSec(radio_expected_requests_per_second) during(run_time minutes)
    ),
    scn_homepage.inject(
      rampUsersPerSec(1) to(homepage_expected_requests_per_second) during(rampUpTime minutes),
      constantUsersPerSec(homepage_expected_requests_per_second) during(run_time minutes)
    )
  ).protocols(
    httpConf
  ).maxDuration(run_time minutes)
//     .throttle(
//      reachRps(total_expected_requests_per_second) in (rampUpTime minutes), holdFor (run_time minutes)
//     )
}
