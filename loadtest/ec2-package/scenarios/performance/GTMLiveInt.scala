package performance

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._

import io.gatling.core.structure.ChainBuilder
import java.util.concurrent.ThreadLocalRandom

//class GTMLiveInt(val run_time: Int = 6) extends Simulation {
class GTMLiveInt extends Simulation {

   def rand_octets(probability: Float):ChainBuilder = {
        //if (ThreadLocalRandom.current.nextFloat() >= 0.2.toFloat)
        if (ThreadLocalRandom.current.nextFloat() >= probability)
        {
            return exec(
                _.set("octet_1", ThreadLocalRandom.current.nextInt(0, 255))
                .set("octet_2", ThreadLocalRandom.current.nextInt(0, 255))
                .set("octet_3", ThreadLocalRandom.current.nextInt(0, 255))
                .set("octet_4", ThreadLocalRandom.current.nextInt(0, 255))
            )
        }
        else
        {
            return exec(
                _.set("octet_1", 1).set("octet_2", 2).set("octet_3", 3).set("octet_4", 4)
            )
        }
    }

  val run_time = 10
  val rampUpTime = 2
  val reuseIpPct: Float = 0.2.toFloat

  val newsRps = 100
  val sportRps = 5
  val homePageRps = 5

  val num_instances = Integer.getInteger("numEC2Instances")

  val news_expected_requests_per_second = newsRps / num_instances

  val sport_expected_requests_per_second = sportRps / num_instances

  val homepage_expected_requests_per_second = homePageRps / num_instances

  val four_o_four_expected_requests_per_second = 5 / num_instances

  val three_o_two_expected_requests_per_second = 5 / num_instances

  val euWestHttpConf = http
    .baseURL("https://www.bbc.com.europe-west-1.live-int.gtm-edge.e9fb45cfcc47b85b.xhst.bbci.co.uk")
    .acceptHeader("text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
    .doNotTrackHeader("1")
    .acceptLanguageHeader("en-GB,en-US;q=0.8,en;q=0.6")
    .acceptEncodingHeader("gzip, deflate")
    .userAgentHeader("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36; SYNTHETIC")
    .header("Host", "www.bbc.com")

  val euCentralHttpConf = http
    .baseURL("https://www.bbc.com.europe-central-1.live-int.gtm-edge.e9fb45cfcc47b85b.xhst.bbci.co.uk")
    .acceptHeader("text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
    .doNotTrackHeader("1")
    .acceptLanguageHeader("en-GB,en-US;q=0.8,en;q=0.6")
    .acceptEncodingHeader("gzip, deflate")
    .userAgentHeader("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36; SYNTHETIC")
    .header("Host", "www.bbc.com")

  val scn_news = scenario("news")
    .exec(rand_octets(reuseIpPct))
    .exec(http("news")
    .get("/news")
    .header("my_ip", "${octet_1}.${octet_2}.${octet_3}.${octet_4}"))

  val scn_sport = scenario("sport")
    .exec(rand_octets(reuseIpPct))
    .exec(http("sport")
    .get("/sport")
    .header("my_ip", "${octet_1}.${octet_2}.${octet_3}.${octet_4}"))

  val scn_homepage = scenario("homepage")
    .exec(rand_octets(reuseIpPct))
    .exec(http("homepage")
    .get("/")
    .header("my_ip", "${octet_1}.${octet_2}.${octet_3}.${octet_4}"))

  val scn_four_o_four = scenario("fourofour")
    .exec(rand_octets(reuseIpPct))
    .exec(http("fourofour")
      .get("/news/bob")
      .check(status.is(404))
      .header("my_ip", "${octet_1}.${octet_2}.${octet_3}.${octet_4}"))

  val scn_three_o_two = scenario("threeotwo")
    .exec(rand_octets(reuseIpPct))
    .exec(http("threeotwo")
      .get("/dave")
      .check(status.in(302, 404))
      .header("my_ip", "${octet_1}.${octet_2}.${octet_3}.${octet_4}"))

  setUp(
    scn_news.inject(
      rampUsersPerSec(1) to(news_expected_requests_per_second) during(rampUpTime minutes),
      constantUsersPerSec(news_expected_requests_per_second) during(run_time minutes)
    ),
    scn_sport.inject(
      rampUsersPerSec(1) to(sport_expected_requests_per_second) during(rampUpTime minutes),
      constantUsersPerSec(sport_expected_requests_per_second) during(run_time minutes)
    ),
    scn_homepage.inject(
      rampUsersPerSec(1) to(homepage_expected_requests_per_second) during(rampUpTime minutes),
      constantUsersPerSec(homepage_expected_requests_per_second) during(run_time minutes)
    ),
    scn_four_o_four.inject(
      rampUsersPerSec(1) to(four_o_four_expected_requests_per_second) during(rampUpTime minutes),
      constantUsersPerSec(four_o_four_expected_requests_per_second) during(run_time minutes)
    ),
    scn_three_o_two.inject(
      rampUsersPerSec(1) to(three_o_two_expected_requests_per_second) during(rampUpTime minutes),
      constantUsersPerSec(three_o_two_expected_requests_per_second) during(run_time minutes)
    )
  ).protocols(
    euWestHttpConf
  ).maxDuration(run_time minutes)
}
