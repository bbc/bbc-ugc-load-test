NAME=ugc-loadtest
GATLING='https://repo1.maven.org/maven2/io/gatling/highcharts/gatling-charts-highcharts-bundle/3.0.0-RC4/gatling-charts-highcharts-bundle-3.0.0-RC4-bundle.zip'

.PHONY: all
all: RPMS

.PHONY: prepare
prepare: SOURCES

.PHONY: clean
clean:
	rm -rf SOURCES RPMS SRPMS

SOURCES: $(shell find src/ -type f)
	@ # Create a tarball to be used as a source in the RPM spec.
	rm -rf SOURCES && mkdir SOURCES
	tar --exclude=".git" --exclude="*.sw?" -czf SOURCES/${NAME}.tar.gz src/
	curl ${GATLING} -o SOURCES/gatling.zip

RPMS: SOURCES $(shell find SPECS/ -type f)
	@ rm -rf RPMS && mkdir RPMS
        mock-build --os 7
       cosmos-release service ugc-loadtest RPMS/*.rpm

