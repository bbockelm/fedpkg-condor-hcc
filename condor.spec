Summary: Condor: High Throughput Computing
Name: condor
Version: 7.5.5
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
#   ee72b65fad02d21af0dc8f1aa5872110  condor_src-7.4.0-all-all.tar.gz
#   d4deeabbbce65980c085d8bea4c1018a  condor_src-7.4.1-all-all.tar.gz
#   4714086f58942b78cf03fef9ccb1117c  condor_src-7.4.2-all-all.tar.gz
#   2b7e7687cba85d0cf0774f9126b51779  condor_src-7.4.3-all-all.tar.gz
#   108a4b91cd10deca1554ca1088be6c8c  condor_src-7.4.4-all-all.tar.gz
#   b482c4bfa350164427a1952113d53d03  condor_src-7.5.5-all-all.tar.gz
# Note: The md5sum of each generated tarball may be different
Source0: condor-7.5.5-308936-RH.tar.gz
Source1: generate-tarball.sh
Patch0: condor_config.generic.patch
Patch3: chkconfig_off.patch
Patch6: log_lock_run.patch

BuildRoot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildRequires: cmake
BuildRequires: flex
BuildRequires: byacc
BuildRequires: pcre-devel
BuildRequires: postgresql-devel
BuildRequires: openssl-devel
BuildRequires: krb5-devel
BuildRequires: gsoap-devel >= 2.7.12-1
BuildRequires: libvirt-devel
BuildRequires: bind-utils
BuildRequires: m4
BuildRequires: autoconf
BuildRequires: libX11-devel

Requires: gsoap >= 2.7.12
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


%package vm-gahp
Summary: Condor's VM Gahp
Group: Applications/System
Requires: %name = %version-%release

%description vm-gahp
The condor_vm-gahp enables the Virtual Machine Universe feature of
Condor. The VM Universe uses libvirt to start and control VMs under
Condor's Startd.


%pre
getent group condor >/dev/null || groupadd -r condor
getent passwd condor >/dev/null || \
  useradd -r -g condor -d %_var/lib/condor -s /sbin/nologin \
    -c "Owner of Condor Daemons" condor
exit 0


%prep
%setup -q -n %{name}-%{version}

%patch0 -p1
%patch3 -p1
%patch6 -p1

# fix errant execute permissions
find src -perm /a+x -type f -name "*.[Cch]" -exec chmod a-x {} \;


%build
%cmake
make %{?_smp_mflags}


%install
# installation happens into a temporary location, this function is
# useful in moving files into their final locations
function populate {
  _dest="$1"; shift; _src="$*"
  mkdir -p "%{buildroot}/$_dest"
  mv $_src "%{buildroot}/$_dest"
}

rm -rf %{buildroot}
make install DESTDIR=%{buildroot}

# The install target puts etc/ under usr/, let's fix that.
mv %{buildroot}/usr/etc %{buildroot}/%{_sysconfdir}

# It is proper to put Condor specific libexec binaries under libexec/condor/
populate %_libexecdir/condor %{buildroot}/usr/libexec/*

# man pages go under %{_mandir}
mkdir -p %{buildroot}/%{_mandir}
mv %{buildroot}/usr/man/man1 %{buildroot}/%{_mandir}

# Things in /usr/lib really belong in /usr/share/condor
mv %{buildroot}/usr/lib %{buildroot}/%{_datarootdir}/condor

mkdir -p %{buildroot}/%{_sysconfdir}/condor
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
  %{buildroot}/etc/examples/condor_config.generic \
  > %{buildroot}/%{_sysconfdir}/condor/condor_config

mkdir -p -m0755 %{buildroot}/%{_var}/run/condor
mkdir -p -m0755 %{buildroot}/%{_var}/log/condor
mkdir -p -m0755 %{buildroot}/%{_var}/lock/condor
mkdir -p -m0755 %{buildroot}/%{_sharedstatedir}/condor/spool
mkdir -p -m1777 %{buildroot}/%{_sharedstatedir}/condor/execute

cat >> %{buildroot}/%{_sharedstatedir}/condor/condor_config.local << EOF
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
echo "TRUST_UID_DOMAIN = TRUE" >> %{buildroot}/%{_sharedstatedir}/condor/condor_config.local

# used by BLAHP, which is not packaged
rm -r %{buildroot}/%{_libexecdir}/condor/glite
rm -r %{buildroot}/%{_datarootdir}/condor/glite
# used by old MPI universe, not packaged (it's rsh, it should die)
rm %{buildroot}/%{_libexecdir}/condor/rsh
# this is distributed as chirp_client.c/h and chirp_protocol.h in %_usrsrc
rm %{buildroot}/%{_datarootdir}/condor/libchirp_client.a
# which we're not distributing atm either
rm -r %{buildroot}/%{_usrsrc}/chirp

# not packaging the condor_startd_factory right now
rm %{buildroot}/%{_sbindir}/condor_startd_factory
rm -r %{buildroot}/%{_usrsrc}/startd_factory
rm %{buildroot}/%{_libexecdir}/condor/bgp_available_partitions
rm %{buildroot}/%{_libexecdir}/condor/bgp_back_partition
rm %{buildroot}/%{_libexecdir}/condor/bgp_boot_partition
rm %{buildroot}/%{_libexecdir}/condor/bgp_destroy_partition
rm %{buildroot}/%{_libexecdir}/condor/bgp_generate_partition
rm %{buildroot}/%{_libexecdir}/condor/bgp_query_work_loads
rm %{buildroot}/%{_libexecdir}/condor/bgp_shutdown_partition

# not packaging glexec support right now
rm %{buildroot}/%{_libexecdir}/condor/condor_glexec_cleanup
rm %{buildroot}/%{_libexecdir}/condor/condor_glexec_job_wrapper
rm %{buildroot}/%{_libexecdir}/condor/condor_glexec_kill
rm %{buildroot}/%{_libexecdir}/condor/condor_glexec_run
rm %{buildroot}/%{_libexecdir}/condor/condor_glexec_setup

# not going to package the sc2005 negotiator
rm %{buildroot}/%{_sbindir}/condor_lease_manager

# no master shutdown program for now
rm %{buildroot}/%{_sbindir}/condor_set_shutdown
rm %{buildroot}/%{_mandir}/man1/condor_set_shutdown.1.gz

# not packaging glidein support, depends on globus
rm %{buildroot}/%{_mandir}/man1/condor_glidein.1.gz
rm %{buildroot}/%{_bindir}/condor_glidein

# not packaging deployment tools
# sbin/uniq_pid_command is a link for uniq_pid_midwife/undertaker
rm %{buildroot}/%{_sbindir}/uniq_pid_command
rm %{buildroot}/%{_sbindir}/uniq_pid_midwife
rm %{buildroot}/%{_sbindir}/uniq_pid_undertaker
rm %{buildroot}/%{_sbindir}/cleanup_release
rm %{buildroot}/%{_sbindir}/condor_local_stop
rm %{buildroot}/%{_sbindir}/condor_cleanup_local
rm %{buildroot}/%{_sbindir}/condor_cold_start
rm %{buildroot}/%{_sbindir}/condor_cold_stop
rm %{buildroot}/%{_sbindir}/condor_config_bind
rm %{buildroot}/%{_sbindir}/filelock_midwife
rm %{buildroot}/%{_sbindir}/filelock_undertaker
rm %{buildroot}/%{_sbindir}/condor_install_local
rm %{buildroot}/%{_sbindir}/condor_local_start
rm %{buildroot}/%{_sbindir}/install_release
rm %{buildroot}/%{_datarootdir}/condor/Execute.pm
rm %{buildroot}/%{_datarootdir}/condor/FileLock.pm
rm %{buildroot}/%{_mandir}/man1/condor_config_bind.1.gz
rm %{buildroot}/%{_mandir}/man1/condor_cold_start.1.gz
rm %{buildroot}/%{_mandir}/man1/condor_cold_stop.1.gz
rm %{buildroot}/%{_mandir}/man1/uniq_pid_midwife.1.gz
rm %{buildroot}/%{_mandir}/man1/uniq_pid_undertaker.1.gz
rm %{buildroot}/%{_mandir}/man1/filelock_midwife.1.gz
rm %{buildroot}/%{_mandir}/man1/filelock_undertaker.1.gz
rm %{buildroot}/%{_mandir}/man1/install_release.1.gz
rm %{buildroot}/%{_mandir}/man1/cleanup_release.1.gz

# not packaging standard universe
rm %{buildroot}/%{_mandir}/man1/condor_compile.1.gz
rm %{buildroot}/%{_mandir}/man1/condor_checkpoint.1.gz
rm -r %{buildroot}/usr/examples

# not packaging configure/install scripts
rm %{buildroot}/%{_mandir}/man1/condor_configure.1.gz
rm %{buildroot}/%{_sbindir}/condor_configure
rm %{buildroot}/%{_sbindir}/condor_install

# not packaging legacy cruft
rm %{buildroot}/%{_mandir}/man1/condor_master_off.1.gz
rm %{buildroot}/%{_sbindir}/condor_master_off
rm %{buildroot}/%{_mandir}/man1/condor_reconfig_schedd.1.gz
rm %{buildroot}/%{_sbindir}/condor_reconfig_schedd
rm %{buildroot}/%{_mandir}/man1/condor_convert_history.1.gz

# not packaging anything globus related
rm %{buildroot}/%{_sbindir}/condor_gridshell
rm %{buildroot}/%{_sbindir}/grid_monitor.sh
rm %{buildroot}/%{_sbindir}/gt4_gahp
rm %{buildroot}/%{_sbindir}/gt42_gahp

# not packaging unsupported gahps
rm %{buildroot}/%{_sbindir}/unicore_gahp

# not packaging libcondorapi.a
rm %{buildroot}/%{_datarootdir}/condor/libcondorapi.a

# not packaging quill bits
rm %{buildroot}/%{_mandir}/man1/condor_load_history.1.gz

# Remove junk
rm -r %{buildroot}/%{_sysconfdir}/sysconfig
rm -r %{buildroot}/%{_sysconfdir}/init.d
rm %{buildroot}/usr/DOC
rm %{buildroot}/usr/INSTALL
rm %{buildroot}/usr/LICENSE-2.0.txt
rm %{buildroot}/usr/README
# No libs, no headers!
rm -r %{buildroot}/usr/include

# install the lsb init script
install -Dp -m0755 %{buildroot}/etc/examples/condor.init %buildroot/%_initrddir/condor

# we must place the config examples in builddir so %doc can find them
mv %{buildroot}/etc/examples %_builddir/%name-%version


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
%_datadir/condor/condor_ssh_to_job_sshd_config_template
%dir %_datadir/condor/webservice/
%_datadir/condor/webservice/condorCollector.wsdl
%_datadir/condor/webservice/condorSchedd.wsdl
%dir %_libexecdir/condor/
%_libexecdir/condor/condor_chirp
%_libexecdir/condor/condor_ssh
%_libexecdir/condor/sshd.sh
%_libexecdir/condor/condor_job_router
%_libexecdir/condor/gridftp_wrapper.sh
%_libexecdir/condor/condor_glexec_update_proxy
%_libexecdir/condor/condor_limits_wrapper.sh
%_libexecdir/condor/condor_rooster
%_libexecdir/condor/condor_ssh_to_job_shell_setup
%_libexecdir/condor/condor_ssh_to_job_sshd_setup
%_libexecdir/condor/power_state
%_libexecdir/condor/condor_shared_port
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
%_mandir/man1/condor_router_history.1.gz
%_mandir/man1/condor_router_q.1.gz
%_mandir/man1/condor_ssh_to_job.1.gz
%_mandir/man1/condor_power.1.gz
# bin/condor is a link for checkpoint, reschedule, vacate
%_bindir/condor
%_bindir/condor_submit_dag
%_bindir/condor_prio
%_bindir/condor_transfer_data
%_bindir/condor_check_userlogs
%_bindir/condor_q
%_libexecdir/condor/condor_transferer
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
%_bindir/condor_ssh_to_job
%_bindir/condor_power
# sbin/condor is a link for master_off, off, on, reconfig,
# reconfig_schedd, restart
%_sbindir/condor_advertise
%_sbindir/condor_c-gahp
%_sbindir/condor_c-gahp_worker_thread
%_sbindir/condor_collector
%_sbindir/condor_fetchlog
%_sbindir/condor_had
%_sbindir/condor_init
%_sbindir/condor_master
%_sbindir/condor_negotiator
%_sbindir/condor_off
%_sbindir/condor_on
%_sbindir/condor_preen
%_sbindir/condor_procd
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
%_sbindir/amazon_gahp
%_sbindir/condor_gridmanager
%_sbindir/condor_credd
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


%files vm-gahp
%defattr(-,root,root,-)
%doc LICENSE-2.0.txt NOTICE.txt
%_sbindir/condor_vm-gahp
%_sbindir/condor_vm_vmware.pl
%_sbindir/condor_vm_xen.sh
%_libexecdir/condor/libvirt_simple_script.awk


%post -n condor
/sbin/chkconfig --add condor
/sbin/ldconfig
test -x /usr/sbin/selinuxenabled && /usr/sbin/selinuxenabled
if [ $? = 0 ]; then
   semanage fcontext -a -t unconfined_execmem_exec_t %_sbindir/condor_startd
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
* Thu Jan 27 2011 <matt@redhat> - 7.5.5-1
- Rebase to 7.5.5 release
-  configure+imake -> cmake
-  Removed patches:
-   only_dynamic_unstripped.patch
-   gsoap-2.7.16-wsseapi.patch
-   gsoap-2.7.16-dom.patch
-  man pages are now built with source
-  quill is no longer present
-  condor_shared_port added
-  condor_power added
-  condor_credd added
-  classads now built from source

* Thu Jan 13 2011 <matt@redhat> - 7.4.4-1
- Upgrade to 7.4.4 release
- Upstreamed: stdsoap2.h.patch.patch

* Mon Aug 23 2010  <matt@redhat> - 7.4.3-1
- Upgrade to 7.4.3 release
- Upstreamed: dso_link_change

* Fri Jun 11 2010  <matt@redhat> - 7.4.2-2
- Rebuild for classads DSO version change (1:0:0)
- Updated stdsoap2.h.patch.patch for gsoap 2.7.16
- Added gsoap-2.7.16-wsseapi/dom.patch for gsoap 2.7.16

* Wed Apr 21 2010  <matt@redhat> - 7.4.2-1
- Upgrade to 7.4.2 release

* Tue Jan  5 2010  <matt@redhat> - 7.4.1-1
- Upgrade to 7.4.1 release
- Upstreamed: guess_version_from_release_dir, fix_platform_check
- Security update (BZ549577)

* Fri Dec  4 2009  <matt@redhat> - 7.4.0-1
- Upgrade to 7.4.0 release
- Fixed POSTIN error (BZ540439)
- Removed NOTICE.txt source, now provided by upstream
- Removed no_rpmdb_query.patch, applied upstream
- Removed no_basename.patch, applied upstream
- Added only_dynamic_unstripped.patch to reduce build time
- Added guess_version_from_release_dir.patch, for previous
- Added fix_platform_check.patch
- Use new --with-platform, to avoid modification of make_final_tarballs
- Introduced vm-gahp package to hold libvirt deps

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
