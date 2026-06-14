package simulations

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._

class DelayLlamaSimulationScaleCep1to100UsersCached extends Simulation {

  val httpProtocol = http
    .baseUrl("http://app:8080")
    .acceptHeader("application/json")
    .userAgentHeader("Gatling")
    
  // The scenario should be a SINGLE request. 
  // Gatling handles the "1 request per second" pacing by injecting new users automatically.
  val scn = scenario("CEP Constant Fire Generator")
    .exec(
      http("get-cep")
        .get("/v1/cached/cep/01430000")
        .check(status.is(200))
        .requestTimeout(6000)
    )

  setUp(
    scn.inject(
      constantUsersPerSec(10).during(10.seconds),
      constantUsersPerSec(20).during(10.seconds),
      constantUsersPerSec(100).during(10.seconds),
      constantUsersPerSec(20).during(10.seconds),
      constantUsersPerSec(10).during(10.seconds),
    )
  ).protocols(httpProtocol)
}