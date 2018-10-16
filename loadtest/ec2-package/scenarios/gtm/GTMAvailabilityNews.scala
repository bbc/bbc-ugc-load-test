package gtm

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._

class GTMAvailabilityNews() extends Simulation {

  val run_time = 240

  val num_instances = Integer.getInteger("numEC2Instances")

  val news_expected_requests_per_second = 1

  val total_expected_requests_per_second = news_expected_requests_per_second

  val httpConf = http
    .baseURL("https://www.bbc.europe-west-1.live-int.gtm-edge.e9fb45cfcc47b85b.xhst.bbci.co.uk")
    .acceptHeader("text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
    .doNotTrackHeader("1")
    .acceptLanguageHeader("en-GB,en-US;q=0.8,en;q=0.6")
    .acceptEncodingHeader("gzip, deflate")
    .userAgentHeader("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36; SYNTHETIC")
    .header("Host", "www.bbc.co.uk")

  val scn_news = scenario("news").exec(http("news").get("/news"))

setUp(
    scn_news.inject(
        constantUsersPerSec(news_expected_requests_per_second) during(run_time minutes)
    )
).protocols(httpConf)

}
