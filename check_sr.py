#!/usr/bin/env python
#
# Check XenServer SR utilization
# (c) copyright Pekka Panula / Sofor oy
# Licence: GPLv2 or later
# Author: Pekka Panula, e-mail: pekka.panula@sofor.fi
# Contact if bugs, etc.
#
# Usage: ./check_sr.py <XenServer IP or FQDN> <username> <password> <sr name> <warning level %> <critical level %>
#
# - Uses https to connect to XenServer, if you have a pool, use a poolmaster IP/FQDN
# - <sr name> is a case sensitive
# - Uses (python) XenAPI, download it from Citrix, http://community.citrix.com/display/xs/Download+SDKs
# - tested on CentOS 5.8 / python 2.x, should work on any modern distro/python AFAIK
#
# example: ./check_sr.py 192.168.0.1 root password MySR 90 95
#
#
# Dated: 9.8.2013
# Version: 1.1.3
#
# Version history:
# - v1.1.3: bug fixes, changed pnp4nagios performance data format
# - v1.1.2: bug fixes, code refactoring
# - v1.1.1: modified centreon performance data format
# - v1.1: you can choose different performance data formats (pnp4nagios or centreon), some code refactoring
# - v1.0: Initial release
# 
# nagios command defination: 
#
# define command{
#        command_name    check_xenserver_sr
#        command_line    $USER1$/check_sr.py $ARG1$ "$USER15$" "$USER16$" "$ARG2$" $ARG3$ $ARG4$
# }
#
# USER16 and USER15 are username and password in resource.cfg


from __future__ import division
import sys, time, atexit
import XenAPI

# CHANGE PERFORMANCE DATA FORMAT 
performancedata_format = "pnp4nagios" # choose this if you use pnp4nagios or compatible
# performancedata_format = "centreon" # choose this if you use   centreon or compatible

def logout():
    try:
        session.xenapi.session.logout()
    except:
        pass

atexit.register(logout)

def humanize_bytes(bytes, precision=2, suffix=True, format="pnp4nagios"):

    if format == "pnp4nagios":
        abbrevs = (
            (1<<30L, 'Gb'),
            (1<<20L, 'Mb'),
            (1<<10L, 'kb'),
            (1,      'b')
        )
    else:
        abbrevs = (
            (1<<50L, 'P'),
            (1<<40L, 'T'),
            (1<<30L, 'G'),
            (1<<20L, 'M'),
            (1<<10L, 'k'),
            (1,      'b')
        )

    if bytes == 1:
        return '1 b'
    for factor, _suffix in abbrevs:
        if bytes >= factor:
            break

    if suffix:
        return '%.*f%s' % (precision, bytes / factor, _suffix)
    else:
        return '%.*f' % (precision, bytes / factor)

def performancedata(sr_name, total, alloc, warning, critical, performancedata_format="pnp4nagios"):

    if performancedata_format == "pnp4nagios":
	performance_line = "'"+sr_name + "_used_space'=" + str(alloc).replace(".",",") + ";" + str(warning).replace(".",",") + ";" + str(critical).replace(".",",") + ";0.00;" + str(total).replace(".",",") +""
    else:
	performance_line = "size=" + str(total) + "B " + "used=" + str(alloc) + "B"+ ";" + str(warning) + ";" + str(critical) + ";0;" + str(total) +""

    return(performance_line)

def main(session, sr_name, warning, critical, performancedata_format):

        gb_factor=1073741824
	mb_factor=1024*1024

	sr = session.xenapi.SR.get_by_name_label(sr_name)
	if sr:
		sr_size          = session.xenapi.SR.get_physical_size(sr[0])
		sr_phys_util     = session.xenapi.SR.get_physical_utilisation(sr[0])
		sr_virtual_alloc = session.xenapi.SR.get_virtual_allocation(sr[0])

		total_bytes_gb   = int(sr_size)      / gb_factor
		total_bytes_mb   = int(sr_size)      / mb_factor
		total_bytes_b    = int(sr_size)
		total_alloc_gb   = int(sr_phys_util) / gb_factor
		total_alloc_mb   = int(sr_phys_util) / mb_factor
		total_alloc_b    = int(sr_phys_util)
		virtual_alloc_gb = int(sr_virtual_alloc) / gb_factor
		virtual_alloc_mb = int(sr_virtual_alloc) / mb_factor
		free_space       = int(total_bytes_gb) - int(total_alloc_gb)
		free_space_b	 = int(total_bytes_b)  - int(total_alloc_b)
		used_percent     = 100*float(total_alloc_gb)/float(total_bytes_gb)
		warning_gb       = (float(total_bytes_gb)     / 100) * float(warning)
		warning_mb       = (float(total_bytes_mb)     / 100) * float(warning)
		warning_b        = int((int(total_bytes_b)    / 100) * float(warning))
		critical_gb      = (float(total_bytes_gb)     / 100) * float(critical)
		critical_mb      = (float(total_bytes_mb)     / 100) * float(critical)
		critical_b       = int((float(total_bytes_b)  / 100) * float(critical))
		if performancedata_format == "pnp4nagios":
			performance = performancedata(sr_name,
						humanize_bytes(total_bytes_b, precision=1, suffix=False, format=performancedata_format),
						humanize_bytes(total_alloc_b, precision=1,               format=performancedata_format),
						humanize_bytes(warning_b,     precision=1, suffix=False, format=performancedata_format),
						humanize_bytes(critical_b,    precision=1, suffix=False, format=performancedata_format),
						performancedata_format)
		else:
			performance = performancedata(sr_name,
						total_bytes_b,
						total_alloc_b,
						warning_b,
						critical_b,
						performancedata_format)

		info =  "utilization %s%%, size %s, used %s, free %s | %s" % (str(round(used_percent,2)), 
										str(humanize_bytes(total_bytes_b, precision=0)), 
										str(humanize_bytes(total_alloc_b, precision=0)), 
										str(humanize_bytes(free_space_b, precision=0)), 
										performance)

		if float(used_percent) >= float(critical):
			print "CRITICAL: SR", sr_name, info
			exitcode = 2
		elif float(used_percent) >= float(warning):
			print "WARNING: SR", sr_name, info
			exitcode = 1
		else:
			print "OK: SR", sr_name, info
			exitcode = 0

		print "SR Physical size:" ,        str(humanize_bytes(total_bytes_b,         precision=1))
		print "SR Virtual allocation:" ,   str(humanize_bytes(int(sr_virtual_alloc), precision=1))
		print "SR Physical Utilization:",  str(humanize_bytes(total_alloc_b,         precision=1))
		print "SR Free space:",            str(humanize_bytes(free_space_b,          precision=1))
		print "SR Space used:",            str(round(used_percent,2)), "%"
		print "SR Warning  level:",        str(humanize_bytes(warning_b,             precision=1))
		print "SR Critical level:",        str(humanize_bytes(critical_b,            precision=1))

		sys.exit(exitcode)		

	else:
		print "CRITICAL: Cant get SR, check SR name! SR =", sr_name
		sys.exit(2)



if __name__ == "__main__":
	if len(sys.argv) <> 7:
		print "Usage:"
		print sys.argv[0], " <XenServer poolmaster ip or fqdn> <username> <password> <sr name> <warning %> <critical %>"
		sys.exit(1)
	url = sys.argv[1]
	username = sys.argv[2]
	password = sys.argv[3]
	sr_name  = sys.argv[4]
	warning  = sys.argv[5]
	critical = sys.argv[6]

	# First acquire a valid session by logging in:
	try:
		session = XenAPI.Session("https://"+url)
	except Exception, e:
		print "CRITICAL: Cant get XenServer session, error: ", str(e)
		sys.exit(2)
	try:
		session.xenapi.login_with_password(username, password)
	except Exception, e:
		print "CRITICAL: Cant login to XenServer, error: ", str(e)
		sys.exit(2)

	main(session, sr_name, warning, critical, performancedata_format)
