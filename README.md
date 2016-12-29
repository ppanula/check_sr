# check_sr
check_sr.py is a Nagios check plugin for Citrix XenServer, it checks storage SR utilization %. It uses XenAPI. 

Usage: ./check_sr.py XenServer_IP username password sr_name warning_level critical_level

- Uses https to connect to XenServer, if you have a pool, use a poolmaster IP/FQDN
- is a case sensitive
- Uses (python) XenAPI, download it from Citrix, http://community.citrix.com/display/xs/Download+SDKs
- tested on CentOS 6.x / python 2.x, should work on any modern distro/python AFAIK

nagios command defination:

```
define command {
   command_name check_xenserver_sr
   command_line $USER1$/check_sr.py $ARG1$ "$USER15$" "$USER16$" "$ARG2$" $ARG3$ $ARG4$
}
```

USER16 and USER15 are username and password in resource.cfg 
