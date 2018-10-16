package performance

class GTMBbcDotComAllLiveGeoIP() extends GTMBbcDotComAllBaseGeoIP (
    run_time=15,
    requests_per_second_per_scenario=25,
    base_url="https://www.bbc.com"
    )
{}
