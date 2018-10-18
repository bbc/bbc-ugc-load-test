package uk.co.bbc.ugc.loadtest


import io.gatling.core.Predef._
import io.gatling.http.Predef._
import io.gatling.http.cookie.CookieJar

object Login {

  val login = exec(http("initiate_sign_in")
    .get("https://account.test.bbc.com/signin"))
    .exec(session => {
      val cookies = session("gatling.http.cookies").as[CookieJar]
      for ((k, s) <- cookies.store) {
        println(s"${k} = ${s}")
      }

      session
    }
    )
    .exec(http("perform_signin")
      .post("https://account.test.bbc.com/signin")
      .header(HttpHeaderNames.ContentType, HttpHeaderValues.ApplicationFormUrlEncoded)
      .formParam("username", "ugc-under13-testuser1")
      .formParam("password", "test4656")
      .check(status.in(400, 500)))
    .exec(http("get_session_info")
      .get("https://session.test.bbc.co.uk/session"))

}