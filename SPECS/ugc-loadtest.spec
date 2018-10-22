Name: ugc-loadtest
Version: 0.4.6
Release: 1%{?dist}
Group: Development/Tools
License: Internal BBC use only
Summary: Useful base tools for Gatling load tests, usually against croupier
Source: ugc-loadtest.tar.gz
Source1: gatling.zip
BuildRoot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildArch: noarch
BuildRequires: unzip

# Gatling deps:
Requires: cosmos-ca-chains
Requires: java-1.8.0-openjdk-headless

# Handy deps:
# Requires: htop # Not in base :(
Requires: bind-utils
Requires: collectd
Requires: iptraf-ng
Requires: lsof
Requires: mtr
Requires: sysstat
Requires: strace
Requires: stunnel
Requires: tcpdump
Requires: tmux
Requires: unzip
Requires: vim-enhanced

%description
Useful base tools for Gatling load tests, usually against croupier


###############################################################################
#                              BUILD TIME SCRIPTS                             #
###############################################################################
%prep
%setup -q -n src
cd %{_sourcedir}
rm -rf gatling
unzip %SOURCE1
mv gatling-charts-highcharts-bundle-* %{_builddir}/src/gatling


%install
rm -rf %{buildroot}

# As long as we're careful about what we put in src/ there should be no problem
# with doing this
mkdir -p $RPM_BUILD_ROOT
cp -R ./etc ./usr $RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT/opt
cp -R ./gatling $RPM_BUILD_ROOT/opt/

%pre
getent group stunnel >/dev/null || groupadd -r stunnel
getent passwd stunnel >/dev/null || useradd -r -g stunnel -G stunnel -d / -s /sbin/nologin -c "stunnel" stunnel

%clean
rm -rf $RPM_BUILD_ROOT


###############################################################################
#                PACKAGE FILE/DIRECTORY LISTING AND ATTRIBUTES                #
###############################################################################
%files
%attr(0640,root,root) /usr/lib/systemd/system/stunnel.service
# %defattr(644, root, root, 755)
%dir /opt/gatling
/opt/gatling/LICENSE
/opt/gatling/conf
/opt/gatling/lib
/opt/gatling/results
/opt/gatling/user-files

/etc/sudoers.d/no_tty

%defattr(755, root, root, 755)
/opt/gatling/bin


###############################################################################
#                                  CHANGELOG                                  #
###############################################################################
%changelog
* Thu Aug  9 2018 Mark Cranny <mark.cranny.ext@bbc.co.uk> 0.4.5-1
- Add collectd dependency

* Wed Aug  8 2018 Mark Cranny <mark.cranny.ext@bbc.co.uk> 0.4.4-1
- Add stunnel dependency and associated configuration

* Mon Nov 28 2016 Henry Rodrick <henry.rodrick@bbc.co.uk> 0.4.1-1
- Bump gatling to 2.2.3

* Thu Apr 07 2016 Alistair Wooldrige <alistair.wooldrige@bbc.co.uk> 0.4.0-1
- Add /etc/sudoers.d/no_tty to stop sudo requiring a tty
- Remove phony script

* Thu Apr 07 2016 Alistair Wooldrige <alistair.wooldrige@bbc.co.uk> 0.3.0-1
- MD-724: Add bind-utils

* Fri Apr 01 2016 Alistair Wooldrige <alistair.wooldrige@bbc.co.uk> 0.2.0-1
- MD-724: Add Gatling into the RPM

* Wed Mar 30 2016 Alistair Wooldrige <alistair.wooldrige@bbc.co.uk> 0.1.0-1
- MD-724: Initial package
