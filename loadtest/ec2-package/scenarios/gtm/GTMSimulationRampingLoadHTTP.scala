package gtm

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._

class GTMSimulationRampingLoadHTTP() extends Simulation {

  val scale_down_factor: Int = 10
  val scale_up_factor: Int = 1
  val run_time: Int = 5
  val scheme: String = "http"

  val num_instances = Integer.getInteger("numEC2Instances")

  val news_expected_requests_per_second = 150 / num_instances
  val news_expected_requests_per_second_scaled_down_tmp : Double = news_expected_requests_per_second / scale_down_factor
  val news_expected_requests_per_second_scaled_down = if (news_expected_requests_per_second_scaled_down_tmp == 1.0 || (news_expected_requests_per_second_scaled_down_tmp == 0.0))
    2.0 else news_expected_requests_per_second_scaled_down_tmp
  val news_expected_requests_per_second_scaled_up_tmp : Double = news_expected_requests_per_second * scale_up_factor
  val news_expected_requests_per_second_scaled_up = if (news_expected_requests_per_second_scaled_up_tmp == 1.0)
    2.0 else news_expected_requests_per_second_scaled_up_tmp

  val sport_expected_requests_per_second = 30 / num_instances
  val sport_expected_requests_per_second_scaled_down_tmp : Double = sport_expected_requests_per_second / scale_down_factor
  val sport_expected_requests_per_second_scaled_down = if (sport_expected_requests_per_second_scaled_down_tmp == 1.0 || (sport_expected_requests_per_second_scaled_down_tmp == 0.0))
    2.0 else sport_expected_requests_per_second_scaled_down_tmp
  val sport_expected_requests_per_second_scaled_up_tmp : Double = sport_expected_requests_per_second * scale_up_factor
  val sport_expected_requests_per_second_scaled_up = if (sport_expected_requests_per_second_scaled_up_tmp == 1.0)
    2.0 else sport_expected_requests_per_second_scaled_up_tmp

  val iplayer_expected_requests_per_second = 30 / num_instances
  val iplayer_expected_requests_per_second_scaled_down_tmp : Double = iplayer_expected_requests_per_second / scale_down_factor
  val iplayer_expected_requests_per_second_scaled_down = if (iplayer_expected_requests_per_second_scaled_down_tmp == 1.0 || (iplayer_expected_requests_per_second_scaled_down_tmp == 0.0))
    2.0 else iplayer_expected_requests_per_second_scaled_down_tmp
  val iplayer_expected_requests_per_second_scaled_up_tmp : Double = iplayer_expected_requests_per_second * scale_up_factor
  val iplayer_expected_requests_per_second_scaled_up = if (iplayer_expected_requests_per_second_scaled_up_tmp == 1.0)
    2.0 else iplayer_expected_requests_per_second_scaled_up_tmp

  val weather_expected_requests_per_second = 10 / num_instances
  val weather_expected_requests_per_second_scaled_down_tmp : Double = weather_expected_requests_per_second / scale_down_factor
  val weather_expected_requests_per_second_scaled_down = if (weather_expected_requests_per_second_scaled_down_tmp == 1.0 || (weather_expected_requests_per_second_scaled_down_tmp == 0.0))
    2.0 else weather_expected_requests_per_second_scaled_down_tmp
  val weather_expected_requests_per_second_scaled_up_tmp : Double = weather_expected_requests_per_second * scale_up_factor
  val weather_expected_requests_per_second_scaled_up = if (weather_expected_requests_per_second_scaled_up_tmp == 1.0)
    2.0 else weather_expected_requests_per_second_scaled_up_tmp

  val radio_expected_requests_per_second = 5 / num_instances
  val radio_expected_requests_per_second_scaled_down_tmp : Double = radio_expected_requests_per_second / scale_down_factor
  val radio_expected_requests_per_second_scaled_down = if (radio_expected_requests_per_second_scaled_down_tmp == 1.0 || (radio_expected_requests_per_second_scaled_down_tmp == 0.0))
    2.0 else radio_expected_requests_per_second_scaled_down_tmp
  val radio_expected_requests_per_second_scaled_up_tmp : Double = radio_expected_requests_per_second * scale_up_factor
  val radio_expected_requests_per_second_scaled_up = if (radio_expected_requests_per_second_scaled_up_tmp == 1.0)
    2.0 else radio_expected_requests_per_second_scaled_up_tmp

  val root_expected_requests_per_second = 5 / num_instances
  val root_expected_requests_per_second_scaled_down_tmp : Double = root_expected_requests_per_second / scale_down_factor
  val root_expected_requests_per_second_scaled_down = if ((root_expected_requests_per_second_scaled_down_tmp == 1.0) || (root_expected_requests_per_second_scaled_down_tmp == 0.0))
    2.0 else root_expected_requests_per_second_scaled_down_tmp
  val root_expected_requests_per_second_scaled_up_tmp : Double = root_expected_requests_per_second * scale_up_factor
  val root_expected_requests_per_second_scaled_up = if (root_expected_requests_per_second_scaled_up_tmp == 1.0)
    2.0 else root_expected_requests_per_second_scaled_up_tmp

  val total_expected_requests_per_second = news_expected_requests_per_second
  + sport_expected_requests_per_second
  + iplayer_expected_requests_per_second
  + weather_expected_requests_per_second
  + radio_expected_requests_per_second
  + root_expected_requests_per_second

  val rampUpTime = run_time / 5

  val httpConf = http
    .baseURL(scheme + "://www.bbc.co.uk")
    .acceptHeader("text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
    .doNotTrackHeader("1")
    .acceptLanguageHeader("en-GB,en-US;q=0.8,en;q=0.6")
    .acceptEncodingHeader("gzip, deflate")
    .userAgentHeader("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36")
    .disableCaching
    .header("Host", "www.bbc.co.uk")

  val scn_news = scenario("news").exec(http("news").get("/news"))

  val scn_sport = scenario("sport").exec(http("sport").get("/sport"))

  val scn_iplayer = scenario("iplayer").exec(http("iplayer").get("/iplayer"))

  val scn_weather = scenario("weather").exec(http("weather").get("/weather"))

  val scn_radio = scenario("radio").exec(http("radio").get("/radio"))

  //  val scn_root = scenario("root").exec(http("root").get("/"))

  if (scale_up_factor == 0) {
    setUp(
      scn_news.inject(
        rampUsersPerSec(1) to(news_expected_requests_per_second_scaled_down) during(run_time minutes)
      ),
      scn_sport.inject(
        rampUsersPerSec(1) to(sport_expected_requests_per_second_scaled_down) during(run_time minutes)
      ),
      scn_iplayer.inject(
        rampUsersPerSec(1) to(iplayer_expected_requests_per_second_scaled_down) during(run_time minutes)
      ),
      scn_weather.inject(
        rampUsersPerSec(1) to(weather_expected_requests_per_second_scaled_down) during(run_time minutes)
      ),
      scn_radio.inject(
        rampUsersPerSec(1) to(radio_expected_requests_per_second_scaled_down) during(run_time minutes)
      )
      //        scn_root.inject(
      //            rampUsersPerSec(1) to(root_expected_requests_per_second_scaled_down) during(rampUpTime minutes),
      //            constantUsersPerSec(root_expected_requests_per_second_scaled_down) during(run_time minutes)
      //        )
    ).protocols(httpConf)
    //     .throttle(
    //      reachRps(total_expected_requests_per_second) in (1 seconds), holdFor (run_time * 1.1 minutes)
    //     )
  } else {
    setUp(
      scn_news.inject(
        rampUsersPerSec(1) to(news_expected_requests_per_second_scaled_up) during(run_time minutes)
      ),
      scn_sport.inject(
        rampUsersPerSec(1) to(sport_expected_requests_per_second_scaled_up) during(run_time minutes)
      ),
      scn_iplayer.inject(
        rampUsersPerSec(1) to(iplayer_expected_requests_per_second_scaled_up) during(run_time minutes)
      ),
      scn_weather.inject(
        rampUsersPerSec(1) to(weather_expected_requests_per_second_scaled_up) during(run_time minutes)
      ),
      scn_radio.inject(
        rampUsersPerSec(1) to(radio_expected_requests_per_second_scaled_up) during(run_time minutes)
      )
      //        scn_root.inject(
      //            rampUsersPerSec(1) to(root_expected_requests_per_second_scaled_up) during(rampUpTime minutes),
      //            constantUsersPerSec(root_expected_requests_per_second_scaled_up) during(run_time minutes)
      //        )
    ).protocols(httpConf)
    //     .throttle(
    //      reachRps(total_expected_requests_per_second) in (1 seconds), holdFor (run_time * 1.1 minutes)
    //     )
  }



}