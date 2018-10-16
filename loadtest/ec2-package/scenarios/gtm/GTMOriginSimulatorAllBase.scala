package gtm

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._

class GTMOriginSimulatorAllBase(val run_time: Int = 15, val requests_per_second_per_scenario: Int = 20, val base_url: String) extends Simulation {

  val num_instances = Integer.getInteger("numEC2Instances")

  val news404_expected_requests_per_second = requests_per_second_per_scenario / num_instances

  val news_expected_requests_per_second = requests_per_second_per_scenario / num_instances

  val sport_expected_requests_per_second = requests_per_second_per_scenario / num_instances

  val iplayer_expected_requests_per_second = requests_per_second_per_scenario / num_instances

  val weather_expected_requests_per_second = requests_per_second_per_scenario / num_instances

  val radio_expected_requests_per_second = requests_per_second_per_scenario / num_instances

  val homepage_expected_requests_per_second = requests_per_second_per_scenario / num_instances

  val httpConf = http
    .baseURL(base_url)
    .acceptHeader("text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
    .doNotTrackHeader("1")
    .acceptLanguageHeader("en-GB,en-US;q=0.8,en;q=0.6")
    .acceptEncodingHeader("gzip, deflate")
    .userAgentHeader("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36; SYNTHETIC")
    .header("Host", "origin-simulator.example.org")

  val scn_news404 = scenario("news404").exec(http("news404").get("/origin-simulator?page=news404&delay_min_msec=100&delay_max_msec=200"))

  val scn_news = scenario("news").exec(http("news").get("/origin-simulator?page=news&delay_min_msec=100&delay_max_msec=200"))

  val scn_sport = scenario("sport").exec(http("sport").get("/origin-simulator?page=sport&delay_min_msec=100&delay_max_msec=200"))

  val scn_iplayer = scenario("iplayer").exec(http("iplayer").get("/origin-simulator?page=iplayer&delay_min_msec=100&delay_max_msec=200"))

  val scn_weather = scenario("weather").exec(http("weather").get("/origin-simulator?page=weather&delay_min_msec=100&delay_max_msec=200"))

  val scn_radio = scenario("radio").exec(http("radio").get("/origin-simulator?page=radio&delay_min_msec=100&delay_max_msec=200"))

  val scn_homepage = scenario("homepage").exec(http("homepage").get("/origin-simulator?page=homepage&delay_min_msec=100&delay_max_msec=200"))

  setUp(
    scn_news404.inject(
      constantUsersPerSec(news404_expected_requests_per_second) during(run_time minutes)
    ),
    scn_news.inject(
      constantUsersPerSec(news_expected_requests_per_second) during(run_time minutes)
    ),
    scn_sport.inject(
      constantUsersPerSec(sport_expected_requests_per_second) during(run_time minutes)
    ),
    scn_iplayer.inject(
      constantUsersPerSec(iplayer_expected_requests_per_second) during(run_time minutes)
    ),
    scn_weather.inject(
      constantUsersPerSec(weather_expected_requests_per_second) during(run_time minutes)
    ),
    scn_radio.inject(
      constantUsersPerSec(radio_expected_requests_per_second) during(run_time minutes)
    ),
    scn_homepage.inject(
      constantUsersPerSec(homepage_expected_requests_per_second) during(run_time minutes)
    )
  ).protocols(httpConf)

}
