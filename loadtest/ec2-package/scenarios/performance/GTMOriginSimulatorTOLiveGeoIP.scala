package performance

class GTMOriginSimulatorTOLiveGeoIP() extends GTMOriginSimulatorTOBaseGeoIP (
    run_time=5,
    requests_per_second_per_scenario=6000,
    base_url="http://gtm-osim.europe-west-1.live-int.gtm-edge.e9fb45cfcc47b85b.xhst.bbci.co.uk"
    )
{}
