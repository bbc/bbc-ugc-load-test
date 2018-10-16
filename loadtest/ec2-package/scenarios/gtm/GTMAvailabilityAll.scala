package gtm

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._

class GTMAvailabilityAll() extends Simulation {

  val run_time = 240

  val num_instances = Integer.getInteger("numEC2Instances")

  val news_expected_requests_per_second = 1

  val sport_expected_requests_per_second = 1

  val iplayer_expected_requests_per_second = 1

  val weather_expected_requests_per_second = 1

  val radio_expected_requests_per_second = 1

  val root_expected_requests_per_second = 1

  val total_expected_requests_per_second = news_expected_requests_per_second
                                            + sport_expected_requests_per_second
                                            + iplayer_expected_requests_per_second
                                            + weather_expected_requests_per_second
                                            + radio_expected_requests_per_second
                                            + root_expected_requests_per_second

  val httpConf = http
    .baseURL("https://www.bbc.europe-west-1.live-int.gtm-edge.e9fb45cfcc47b85b.xhst.bbci.co.uk")
    .acceptHeader("text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
    .doNotTrackHeader("1")
    .acceptLanguageHeader("en-GB,en-US;q=0.8,en;q=0.6")
    .acceptEncodingHeader("gzip, deflate")
    .userAgentHeader("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36; SYNTHETIC")
    .header("Host", "www.bbc.co.uk")

  val scn_news = scenario("news").exec(http("news").get("/news"))

  val scn_sport = scenario("sport").exec(http("sport").get("/sport"))

  val scn_iplayer = scenario("iplayer").exec(http("iplayer").get("/iplayer"))

  val scn_weather = scenario("weather").exec(http("weather").get("/weather/"))

  val scn_radio = scenario("radio").exec(http("radio").get("/radio"))

  val scn_root = scenario("root").exec(http("root").get("/"))

setUp(
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
    scn_root.inject(
        constantUsersPerSec(root_expected_requests_per_second) during(run_time minutes)
    )
).protocols(httpConf)

}
