Summary: Condor: High Throughput Computing
Name: condor
Version: 7.2.4
Release: 1%{?dist}
License: ASL 2.0
Group: Applications/System
URL: http://www.cs.wisc.edu/condor/
# The upstream Condor source tarball contains some source that cannot
# be shipped as well as extraneous copies of packages the source
# depends on. Additionally, the upstream Condor source requires a
# click-through license. Once you have downloaded the source from:
#   http://parrot.cs.wisc.edu/v7.0.license.html
# you should process it with generate-tarball.sh:
#   ./generate-tarball.sh 7.0.4
# MD5Sum of upstream source:
#   06eec3ae274b66d233ad050a047f3c91  condor_src-7.0.0-all-all.tar.gz
#   b08743cfa2e87adbcda042896e8ef537  condor_src-7.0.2-all-all.tar.gz
#   5f326ad522b63eacf34c6c563cf46910  condor_src-7.0.4-all-all.tar.gz
#   73323100c5b2259f3b9c042fa05451e0  condor_src-7.0.5-all-all.tar.gz
#   a2dd96ea537b2c6d105b6c8dad563ddc  condor_src-7.2.0-all-all.tar.gz
#   edbac8267130ac0a0e016d0f113b4616  condor_src-7.2.1-all-all.tar.gz
#   6d9b0ef74d575623af11e396fa274174  condor_src-7.2.4-all-all.tar.gz
# Note: The md5sum of each generated tarball may be different
Source0: condor-7.2.4-159529-RH.tar.gz
Source1: generate-tarball.sh
Source2: NOTICE.txt
Patch0: condor_config.generic.patch
Patch1: stdsoap2.h.patch.patch
Patch3: chkconfig_off.patch
Patch4: no_rpmdb_query.patch
Patch5: no_basename.patch
Patch6: log_lock_run.patch

BuildRoot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildRequires: imake
BuildRequires: flex
BuildRequires: byacc
BuildRequires: pcre-devel
BuildRequires: postgresql-devel
BuildRequires: openssl-devel
BuildRequires: krb5-devel
BuildRequires: gsoap-devel >= 2.7.12-1
BuildRequires: bind-utils
BuildRequires: m4
BuildRequires: autoconf
BuildRequires: classads-devel
BuildRequires: libX11-devel

Requires: gsoap >= 2.7.12-1
Requires: mailx
Requires: python >= 2.2

Requires(pre): shadow-utils

Requires(post):/sbin/chkconfig
Requires(preun):/sbin/chkconfig
Requires(preun):/sbin/service
Requires(postun):/sbin/service

#Provides: user(condor) = 43
#Provides: group(condor) = 43

Obsoletes: condor-static < 7.2.0


%description
Condor is a specialized workload management system for
compute-intensive jobs. Like other full-featured batch systems, Condor
provides a job queueing mechanism, scheduling policy, priority scheme,
resource monitoring, and resource management. Users submit their
serial or parallel jobs to Condor, Condor places them into a queue,
chooses when and where to run the jobs based upon a policy, carefully
monitors their progress, and ultimately informs the user upon
completion.


#%package static
#Summary: Headers and libraries for interacting with Condor
#Group: Development/System
#Requires: %name = %version-%release
#
#
#%description static
#Headers and libraries for interacting with Condor and its components.


%package kbdd
Summary: Condor Keyboard Daemon
Group: Applications/System
Requires: %name = %version-%release
Requires: libX11

%description kbdd
The condor_kbdd monitors logged in X users for activity. It is only
useful on systems where no device (e.g. /dev/*) can be used to
determine console idle time.


%pre
getent group condor >/dev/null || groupadd -r condor
getent passwd condor >/dev/null || \
  useradd -r -g condor -d %_var/lib/condor -s /sbin/nologin \
    -c "Owner of Condor Daemons" condor
exit 0


%prep
%setup -q -n %{name}-%{version}

cp %{SOURCE2} .

%patch0 -p1
%patch1 -p1
%patch3 -p1
%patch4 -p1
%patch5 -p1
%patch6 -p1

# fix errant execute permissions
find src -perm /a+x -type f -name "*.[Cch]" -exec chmod a-x {} \;


%build
# set USE_OLD_IMAKE to anything so condor_imake will use the system
# installed imake instead of building its own
USE_OLD_IMAKE=YES
export USE_OLD_IMAKE

# Condor does not like to be built with -O2 to begin with, and it
# appears to trigger a bug in GCC 4.3.0, so for the time being -O2 is
# banished from C*FLAGS
%define optflags %(rpm --eval '%%optflags' | sed 's|-O2||g')

cd src
./build_init
%configure --with-buildid=Fedora-%{version}-%{release} \
   --enable-proper \
   --disable-full-port \
   --disable-gcc-version-check \
   --disable-glibc-version-check \
   --disable-static \
   --disable-rpm \
   --enable-kbdd \
   --disable-hibernation \
   --disable-lease-manager \
   --without-zlib \
   --with-openssl \
   --with-krb5 \
   --with-postgresql \
   --with-gsoap \
   --with-classads \
   --with-man=$PWD/../externals/bundles/man/current

# SMP_NUM_JOBS must be set properly to pass -j to make
#SMP_NUM_JOBS=$(echo %{?_smp_mflags} | sed -e 's/-j\(.*\)/\1/')
#export SMP_NUM_JOBS

# build a releasable tarball
make public


%install
# installation happens into a temporary location, this function is
# useful in moving files into their final locations
function populate {
  _dest="$1"; shift; _src="$*"
  mkdir -p "%{buildroot}/$_dest"
  mv $_src "%{buildroot}/$_dest"
}

rm -rf %{buildroot}

# make public creates release tarballs which we will install
oldpwd=$PWD
cd public/v7.2
gzip -cd condor-%{version}-*-dynamic-unstripped.tar.gz | tar x
cd condor-%{version}

PREFIX=%{buildroot}/install

populate install *

cp $PREFIX/etc/examples/condor_config.generic $PREFIX/etc/condor_config

# the default condor_config file is not architecture aware and thus
# sets the LIB directory to always be /usr/lib, we want to do better
# than that. this is, so far, the best place to do this
# specialization. we strip the "lib" or "lib64" part from _libdir and
# stick it in the LIB variable in the config.
LIB=$(echo %{?_libdir} | sed -e 's:/usr/\(.*\):\1:')
if [ "$LIB" = "%_libdir" ]; then
  echo "_libdir does not contain /usr, sed expression needs attention"
  exit 1
fi
sed -e "s:^LIB\s*=.*:LIB = \$(RELEASE_DIR)/$LIB/condor:" \
  $PREFIX/etc/examples/condor_config.generic \
  > $PREFIX/etc/condor_config


mkdir $PREFIX/local_dir
mkdir -m1777 $PREFIX/local_dir/execute
mkdir -m0755 $PREFIX/local_dir/log
mkdir -m0755 $PREFIX/local_dir/spool

cat >> $PREFIX/local_dir/condor_config.local << EOF
CONDOR_DEVELOPERS = NONE
CONDOR_HOST = \$(FULL_HOSTNAME)
COLLECTOR_NAME = Personal Condor
START = TRUE
SUSPEND = FALSE
PREEMPT = FALSE
KILL = FALSE
DAEMON_LIST = COLLECTOR, MASTER, NEGOTIATOR, SCHEDD, STARTD
NEGOTIATOR_INTERVAL = 20
EOF

# this gets around a bug whose fix is not yet merged
echo "TRUST_UID_DOMAIN = TRUE" >> $PREFIX/local_dir/condor_config.local

# used by BLAHP, which is not packaged
rm -rf $PREFIX/libexec/glite
# used by old MPI universe, not packaged (it's rsh, it should die)
rm -rf $PREFIX/libexec/rsh
# this is distributed as chirp_client.c/h and chirp_protocol.h in %_usrsrc
rm $PREFIX/lib/libchirp_client.a
rm $PREFIX/include/chirp_client.h
# checkpoint, reschedule and vacate live in bin/, don't duplicate
rm $PREFIX/sbin/condor_checkpoint
rm $PREFIX/sbin/condor_reschedule
rm $PREFIX/sbin/condor_vacate
# the libcondorapi.so is not properly created, instead of providing it
# we will provide the .a version in a static package
rm $PREFIX/lib/libcondorapi.so
# sbin/condor is a pointless hard links
rm $PREFIX/sbin/condor

# not packaging the condor_startd_factory right now
rm $PREFIX/sbin/condor_startd_factory
rm $PREFIX/lib/webservice/condorStartdFactory.wsdl
rm $PREFIX/libexec/bgp_available_partitions
rm $PREFIX/libexec/bgp_back_partition
rm $PREFIX/libexec/bgp_boot_partition
rm $PREFIX/libexec/bgp_destroy_partition
rm $PREFIX/libexec/bgp_generate_partition
rm $PREFIX/libexec/bgp_query_work_loads
rm $PREFIX/libexec/bgp_shutdown_partition

# not packaging uninteresting WSDL files, except for the master
rm $PREFIX/lib/webservice/condorCgahp.wsdl
rm $PREFIX/lib/webservice/condorDagman.wsdl
rm $PREFIX/lib/webservice/condorDbmsd.wsdl
rm $PREFIX/lib/webservice/condorDcskel.wsdl
rm $PREFIX/lib/webservice/condorEventd.wsdl
rm $PREFIX/lib/webservice/condorGridmanager.wsdl
rm $PREFIX/lib/webservice/condorHad.wsdl
rm $PREFIX/lib/webservice/condorJobRouter.wsdl
rm $PREFIX/lib/webservice/condorKbdd.wsdl
rm $PREFIX/lib/webservice/condorNegotiator.wsdl
rm $PREFIX/lib/webservice/condorShadow.wsdl
rm $PREFIX/lib/webservice/condorStartd.wsdl
rm $PREFIX/lib/webservice/condorStarter.wsdl
rm $PREFIX/lib/webservice/condorTransferd.wsdl
rm $PREFIX/lib/webservice/condorTt.wsdl
rm $PREFIX/lib/webservice/condorVMgahp.wsdl


# not packaging glexec support right now
rm $PREFIX/libexec/condor_glexec_cleanup
rm $PREFIX/libexec/condor_glexec_job_wrapper
rm $PREFIX/libexec/condor_glexec_kill
rm $PREFIX/libexec/condor_glexec_run
rm $PREFIX/libexec/condor_glexec_setup
# not shipping gt42 gahp right now
rm $PREFIX/sbin/gt42_gahp

# not going to package the sc2005 negotiator
#rm $PREFIX/sbin/condor_lease_manager

# not going to package these until we know what they are
rm $PREFIX/bin/condor_power
rm $PREFIX/sbin/condor_set_shutdown

# not packaging glidein support, depends on globus
rm $PREFIX/man/man1/condor_glidein.1
rm $PREFIX/bin/condor_glidein

# not packaging deployment tools
# sbin/uniq_pid_command is a link for uniq_pid_midwife/undertaker
rm $PREFIX/sbin/uniq_pid_command
rm $PREFIX/sbin/uniq_pid_midwife
rm $PREFIX/sbin/uniq_pid_undertaker
rm $PREFIX/sbin/cleanup_release
rm $PREFIX/sbin/condor_local_stop
rm $PREFIX/sbin/condor_cleanup_local
rm $PREFIX/sbin/condor_cold_start
rm $PREFIX/sbin/condor_cold_stop
rm $PREFIX/sbin/condor_config_bind
rm $PREFIX/sbin/filelock_midwife
rm $PREFIX/sbin/filelock_undertaker
rm $PREFIX/sbin/condor_install_local
rm $PREFIX/sbin/condor_local_start
rm $PREFIX/sbin/install_release
rm $PREFIX/lib/Execute.pm
rm $PREFIX/lib/FileLock.pm
rm $PREFIX/man/man1/condor_config_bind.1
rm $PREFIX/man/man1/condor_cold_start.1
rm $PREFIX/man/man1/condor_cold_stop.1

# not packaging the ckpt server
rm $PREFIX/sbin/condor_ckpt_server

# not packaging standard universe
rm $PREFIX/bin/condor_checkpoint
rm $PREFIX/sbin/condor_shadow.std
rm $PREFIX/sbin/condor_starter.std
rm $PREFIX/bin/condor_compile
rm $PREFIX/man/man1/condor_compile.1
rm $PREFIX/man/man1/condor_checkpoint.1
rm $PREFIX/libexec/condor_ckpt_probe

# not packaging configure/install scripts
rm $PREFIX/man/man1/condor_configure.1
rm $PREFIX/sbin/condor_configure
rm $PREFIX/sbin/condor_install

# not packaging legacy cruft
rm $PREFIX/man/man1/condor_master_off.1
rm $PREFIX/sbin/condor_master_off
rm $PREFIX/man/man1/condor_reconfig_schedd.1
rm $PREFIX/sbin/condor_reconfig_schedd
rm $PREFIX/man/man1/condor_convert_history.1
rm $PREFIX/sbin/condor_convert_history

# not packaging anything globus related
rm $PREFIX/sbin/condor_gridshell
rm $PREFIX/sbin/grid_monitor.sh
rm $PREFIX/sbin/gt4_gahp

# not packaging unsupported gahps
rm $PREFIX/sbin/unicore_gahp

# not packaging libcondorapi.a
rm $PREFIX/lib/libcondorapi.a


# some scripts are examples but have exec bits set anyway
chmod a-x $PREFIX/etc/examples/condor.boot
chmod a-x $PREFIX/etc/examples/lamscript
chmod a-x $PREFIX/etc/examples/mp1script

# here is the actual installation
populate %_mandir/man1 $PREFIX/man/man1/*
populate %_bindir $PREFIX/bin/*
populate %_sbindir $PREFIX/sbin/*
populate %_sysconfdir/condor $PREFIX/etc/condor_config
# no -static package
#populate %_usrsrc $PREFIX/src/chirp
#populate %_includedir/condor $PREFIX/include/*
#populate %_libdir $PREFIX/lib/libcondorapi.a
populate %_datadir/condor $PREFIX/lib/*
populate %_datadir/condor/sql $PREFIX/sql/*
populate %_libexecdir/condor $PREFIX/libexec/*
populate %_var/lib/condor $PREFIX/local_dir/*
mkdir -p -m0755 "%{buildroot}"/%_var/run/condor
mkdir -p -m0755 "%{buildroot}"/%_var/log/condor
mkdir -p -m0755 "%{buildroot}"/%_var/lock/condor

# install the lsb init script
install -Dp -m0755 $PREFIX/etc/examples/condor.init %buildroot/%_initrddir/condor

# we must place the config examples in builddir so %doc can find them
mv $PREFIX/etc/examples %_builddir/%name-%version

# delete our temporary workspace
rm -rf $PREFIX


%clean
rm -rf %{buildroot}


%check
# This currently takes hours and can kill your machine...
#cd condor_tests
#make check-seralized


%files
%defattr(-,root,root,-)
%doc LICENSE-2.0.txt examples
%_initrddir/condor
%dir %_sysconfdir/condor/
%config(noreplace) %_sysconfdir/condor/condor_config
%dir %_datadir/condor/
%_datadir/condor/Chirp.jar
%_datadir/condor/CondorJavaInfo.class
%_datadir/condor/CondorJavaWrapper.class
%_datadir/condor/Condor.pm
%_datadir/condor/scimark2lib.jar
%dir %_datadir/condor/webservice/
%_datadir/condor/webservice/condorCollector.wsdl
%_datadir/condor/webservice/condorMaster.wsdl
%_datadir/condor/webservice/condorSchedd.wsdl
%dir %_datadir/condor/sql/
%_datadir/condor/sql/common_createddl.sql
%_datadir/condor/sql/oracle_createddl.sql
%_datadir/condor/sql/oracle_dropddl.sql
%_datadir/condor/sql/pgsql_createddl.sql
%_datadir/condor/sql/pgsql_dropddl.sql
%dir %_libexecdir/condor/
%_libexecdir/condor/condor_chirp
%_libexecdir/condor/condor_ssh
%_libexecdir/condor/sshd.sh
%_libexecdir/condor/condor_job_router
%_libexecdir/condor/gridftp_wrapper.sh
%_mandir/man1/condor_advertise.1.gz
%_mandir/man1/condor_check_userlogs.1.gz
%_mandir/man1/condor_chirp.1.gz
%_mandir/man1/condor_cod.1.gz
%_mandir/man1/condor_config_val.1.gz
%_mandir/man1/condor_dagman.1.gz
%_mandir/man1/condor_fetchlog.1.gz
%_mandir/man1/condor_findhost.1.gz
%_mandir/man1/condor_history.1.gz
%_mandir/man1/condor_hold.1.gz
%_mandir/man1/condor_load_history.1.gz
%_mandir/man1/condor_master.1.gz
%_mandir/man1/condor_off.1.gz
%_mandir/man1/condor_on.1.gz
%_mandir/man1/condor_preen.1.gz
%_mandir/man1/condor_prio.1.gz
%_mandir/man1/condor_q.1.gz
%_mandir/man1/condor_qedit.1.gz
%_mandir/man1/condor_reconfig.1.gz
%_mandir/man1/condor_release.1.gz
%_mandir/man1/condor_reschedule.1.gz
%_mandir/man1/condor_restart.1.gz
%_mandir/man1/condor_rm.1.gz
%_mandir/man1/condor_run.1.gz
%_mandir/man1/condor_stats.1.gz
%_mandir/man1/condor_status.1.gz
%_mandir/man1/condor_store_cred.1.gz
%_mandir/man1/condor_submit.1.gz
%_mandir/man1/condor_submit_dag.1.gz
%_mandir/man1/condor_transfer_data.1.gz
%_mandir/man1/condor_updates_stats.1.gz
%_mandir/man1/condor_userlog.1.gz
%_mandir/man1/condor_userprio.1.gz
%_mandir/man1/condor_vacate.1.gz
%_mandir/man1/condor_vacate_job.1.gz
%_mandir/man1/condor_version.1.gz
%_mandir/man1/condor_wait.1.gz
# bin/condor is a link for checkpoint, reschedule, vacate
%_bindir/condor
%_bindir/condor_load_history
%_bindir/condor_submit_dag
%_bindir/condor_prio
%_bindir/condor_transfer_data
%_bindir/condor_check_userlogs
%_bindir/condor_q
%_sbindir/condor_transferer
%_bindir/condor_cod
%_bindir/condor_qedit
%_bindir/condor_userlog
%_bindir/condor_release
%_bindir/condor_userlog_job_counter
%_bindir/condor_config_val
%_bindir/condor_reschedule
%_bindir/condor_userprio
%_bindir/condor_dagman
%_bindir/condor_rm
%_bindir/condor_vacate
%_bindir/condor_dump_history
%_bindir/condor_run
%_bindir/condor_router_history
%_bindir/condor_router_q
%_bindir/condor_router_rm
%_bindir/condor_vacate_job
%_bindir/condor_findhost
%_bindir/condor_stats
%_bindir/condor_version
%_bindir/condor_history
%_bindir/condor_status
%_bindir/condor_wait
%_bindir/condor_hold
%_bindir/condor_submit
# sbin/condor is a link for master_off, off, on, reconfig,
# reconfig_schedd, restart
%_sbindir/condor_advertise
%_sbindir/condor_c-gahp
%_sbindir/condor_c-gahp_worker_thread
%_sbindir/condor_collector
%_sbindir/condor_dbmsd
%_sbindir/condor_fetchlog
%_sbindir/condor_had
%_sbindir/condor_init
%_sbindir/condor_master
%_sbindir/condor_negotiator
%_sbindir/condor_off
%_sbindir/condor_on
%_sbindir/condor_preen
%_sbindir/condor_procd
%_sbindir/condor_quill
%_sbindir/condor_reconfig
%_sbindir/condor_replication
%_sbindir/condor_restart
%_sbindir/condor_root_switchboard
%_sbindir/condor_schedd
%_sbindir/condor_shadow
%_sbindir/condor_startd
%_sbindir/condor_starter
%_sbindir/condor_store_cred
%_sbindir/condor_transferd
%_sbindir/condor_updates_stats
%_sbindir/condor_vm-gahp
%_sbindir/amazon_gahp
%_sbindir/condor_vm_vmware.pl
%_sbindir/condor_vm_xen.sh
%_sbindir/condor_gridmanager
%config(noreplace) %_var/lib/condor/condor_config.local
%defattr(-,condor,condor,-)
%dir %_var/lib/condor/
%dir %_var/lib/condor/execute/
%dir %_var/log/condor/
%dir %_var/lib/condor/spool/
%dir %_var/lock/condor/
%dir %_var/run/condor/


#%files static
#%defattr(-,root,root,-)
#%doc LICENSE-2.0.txt
#%_libdir/libcondorapi.a
#%dir %_includedir/condor/
#%_includedir/condor/condor_constants.h
#%_includedir/condor/condor_event.h
#%_includedir/condor/condor_holdcodes.h
#%_includedir/condor/file_lock.h
#%_includedir/condor/user_log.c++.h
#%doc %_includedir/condor/user_log.README
#%dir %_usrsrc/chirp/
#%_usrsrc/chirp/chirp_client.c
#%_usrsrc/chirp/chirp_client.h
#%_usrsrc/chirp/chirp_protocol.h


%files kbdd
%defattr(-,root,root,-)
%doc LICENSE-2.0.txt NOTICE.txt
%_sbindir/condor_kbdd


%post -n condor
/sbin/chkconfig --add condor
/sbin/ldconfig
test -x /usr/sbin/selinuxenabled && /usr/sbin/selinuxenabled
if [ $? = 0 ]; then
   semanage fcontext -a -t unconfined_execmem_exec_t %_sbindir/condor_startd 2>&1| grep -v "already defined"
   restorecon  %_sbindir/condor_startd
fi


%preun -n condor
if [ $1 = 0 ]; then
  /sbin/service condor stop >/dev/null 2>&1 || :
  /sbin/chkconfig --del condor
fi


%postun -n condor
if [ "$1" -ge "1" ]; then
  /sbin/service condor condrestart >/dev/null 2>&1 || :
fi
/sbin/ldconfig


%changelog
* Fri Aug 28 2009  <matt@redhat> - 7.2.4-1
- Upgrade to 7.2.4 release
- Removed gcc44_const.patch, accepted upstream
- New log, lock, run locations (BZ502175)
- Filtered innocuous semanage message

* Fri Aug 21 2009 Tomas Mraz <tmraz@redhat.com> - 7.2.1-3
- rebuilt with new openssl

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 7.2.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Mon Feb 25 2009  <matt@redhat> - 7.2.1-1
- Upgraded to 7.2.1 release
- Pruned changes accepted upstream from condor_config.generic.patch
- Removed Requires in favor of automatic dependencies on SONAMEs
- Added no_rmpdb_query.patch to avoid rpm -q during a build

* Tue Feb 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 7.2.0-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Thu Jan 15 2009 Tomas Mraz <tmraz@redhat.com> - 7.2.0-4
- rebuild with new openssl

* Mon Jan 14 2009  <matt@redhat> - 7.2.0-3
- Fixed regression: initscript was on by default, now off again

* Thu Jan  8 2009  <matt@redhat> - 7.2.0-2
- (Re)added CONDOR_DEVELOPERS=NONE to the default condor_config.local
- Added missing Obsoletes for condor-static (thanks Michael Schwendt)

* Wed Jan  7 2009  <matt@redhat> - 7.2.0-1
- Upgraded to 7.2.0 release
- Removed -static package
- Added Fedora specific buildid
- Enabled KBDD, daemon to monitor X usage on systems with only USB devs
- Updated install process

* Wed Oct  8 2008  <matt@redhat> - 7.0.5-1
- Rebased on 7.0.5, security update

* Wed Aug  6 2008  <mfarrellee@redhat> - 7.0.4-1
- Updated to 7.0.4 source
- Stopped using condor_configure in install step

* Tue Jun 10 2008  <mfarrellee@redhat> - 7.0.2-1
- Updated to 7.0.2 source
- Updated config, specifically HOSTALLOW_WRITE, for Personal Condor setup
- Added condor_config.generic

* Mon Apr  7 2008  <mfarrellee@redhat> - 7.0.0-8
- Modified init script to be off by default, resolves bz441279

* Fri Apr  4 2008  <mfarrellee@redhat> - 7.0.0-7
- Updated to handle changes in gsoap dependency

* Mon Feb 11 2008  <mfarrellee@redhat> - 7.0.0-6
- Added note about how to download the source
- Added generate-tarball.sh script

* Sun Feb 10 2008  <mfarrellee@redhat> - 7.0.0-5
- The gsoap package is compiled with --disable-namespaces, which means
  soap_set_namespaces is required after each soap_init. The
  gsoap_nonamespaces.patch handles this.

* Fri Feb  8 2008  <mfarrellee@redhat> - 7.0.0-4
- Added patch to detect GCC 4.3.0 on F9
- Added patch to detect GLIBC 2.7.90 on F9
- Added BuildRequires: autoconf to allow for regeneration of configure
  script after GCC 4.3.0 detection and GLIBC 2.7.90 patches are
  applied
- Condor + GCC 4.3.0 + -O2 results in an internal compiler error
  (BZ 432090), so -O2 is removed from optflags for the time
  being. Thanks to Mike Bonnet for the suggestion on how to filter
  -O2.

* Tue Jan 22 2008  <mfarrellee@redhat> - 7.0.0-3
- Update to UW's really-final source for Condor 7.0.0 stable series
  release. It is based on the 72173 build with minor changes to the
  configure.ac related to the SRB external version.
- In addition to removing externals from the UW tarball, the NTconfig
  directory was removed because it had not gone through IP audit.

* Tue Jan 22 2008  <mfarrellee@redhat> - 7.0.0-2
- Update to UW's final source for Condor 7.0.0 stable series release

* Thu Jan 10 2008  <mfarrellee@redhat> - 7.0.0-1
- Initial package of Condor's stable series under ASL 2.0
- is_clipped.patch replaced with --without-full-port option to configure
- zlib_is_soft.patch removed, outdated by configure.ac changes
- removed autoconf dependency needed for zlib_is_soft.patch

* Tue Dec  4 2007  <mfarrellee@redhat> - 6.9.5-2
- SELinux was stopping useradd in pre because files specified root as
  the group owner for /var/lib/condor, fixed, much thanks to Phil Knirsch

* Fri Nov 30 2007  <mfarrellee@redhat> - 6.9.5-1
- Fixed release tag
- Added gSOAP support and packaged WSDL files

* Thu Nov 29 2007  <mfarrellee@redhat> - 6.9.5-0.2
- Packaged LSB init script
- Changed pre to not create the condor user's home directory, it is
  now a directory owned by the package

* Thu Nov 29 2007  <mfarrellee@redhat> - 6.9.5-0.1
- Condor 6.9.5 release, the 7.0.0 stable series candidate
- Removed x86_64_no_multilib-200711091700cvs.patch, merged upstream
- Added patch to make zlib a soft requirement, which it should be
- Disabled use of smp_mflags because of make dependency issues
- Explicitly not packaging WSDL files until the SOAP APIs are available

* Tue Nov 20 2007  <mfarrellee@redhat> - 6.9.5-0.3.200711091700cvs
- Rebuild for repo inheritance update: dependencies are now pulled
  from RHEL 5 U1 before RH Application Stack

* Thu Nov 15 2007 <mfarrellee@redhat> - 6.9.5-0.2.200711091700cvs
- Added support for building on x86_64 without multilib packages
- Made the install section more flexible, reduced need for
  make_final_tarballs to be updated

* Fri Nov 9 2007 <mfarrellee@redhat> - 6.9.5-0.1.200711091700cvs
- Working source with new ASL 2.0 license

* Fri Nov 9 2007 <mfarrellee@redhat> - 6.9.5-0.1.200711091330cvs
- Source is now stamped ASL 2.0, as of Nov 9 2007 1:30PM Central
- Changed license to ASL 2.0
- Fixed find in prep to work if no files have bad permissions
- Changed the name of the LICENSE file to match was is now release in
  the source tarball

* Tue Nov 6 2007  <mfarrellee@redhat> - 6.9.5-0.1.rc
- Added m4 dependency not in RHEL 5.1's base
- Changed chmod a-x script to use find as more files appear to have
  improper execute bits set
- Added ?dist to Release:
- condor_privsep became condor_root_switchboard

* Tue Sep 11 2007  <mfarrellee@redhat> - 6.9.5-0.3.20070907cvs
- Instead of releasing libcondorapi.so, which is improperly created
  and poorly versioned, we release libcondorapi.a, which is apparently
  more widely used, in a -static package
- Instead of installing the stripped tarball, the unstripped is now
  installed, which gives a nice debuginfo package
- Found and fixed permissions problems on a number of src files,
  issue raised by rpmlint on the debuginfo package

* Mon Sep 10 2007  <mfarrellee@redhat> - 6.9.5-0.2.20070907cvs
- Updated pre section to create condor's home directory with adduser, and
  removed _var/lib/condor from files section
- Added doc LICENSE.TXT to all files sections
- Shortened lines longer than 80 characters in this spec (except the sed line)
- Changed install section so untar'ing a release can handle fedora7 or fedora8
- Simplified the site.def and config file updates (sed + mv over mv + sed + rm)
- Added a patch (fedora_rawhide_7.91-20070907cvs.patch) to support building on
  a fedora 7.91 (current Rawhide) release
- Moved the examples from /usr/share/doc/condor... into builddir and just
  marked them as documentation
- Added a number of dir directives to force all files to be listed, no implicit
  inclusion

* Fri Sep  7 2007  <mfarrellee@redhat> - 6.9.5-0.1.20070907cvs
- Initial release
