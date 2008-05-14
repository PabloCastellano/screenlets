# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

# The screenlets.sensors module contains helper-functions to aid in
# creating CPU/RAM/*-meters and in retrieving general system information.

import sys
import re
import gobject
import gettext
from datetime import datetime
import commands
import time
import os
import subprocess
import gtk
# translation stuff
gettext.textdomain('screenlets')
gettext.bindtextdomain('screenlets', '/usr/share/locale')

def _(s):
	return gettext.gettext(s)


# ------------------------------------------------------------------------------
# FUNCTIONS
# ------------------------------------------------------------------------------



###########################################
#                                         #
#                 CPU                     #
#                                         #
###########################################

# calculate cpu-usage by values from /proc/stat
# (written by Helder Fraga aka Whise
def cpu_get_load (processor_number=0):
	"""Calculates the system load."""
	try:
		f = open("/proc/stat", "r")
		tmp = f.readlines(2000)
		f.close()
	except:
		print _("Failed to open /proc/stat")
		sys.exit(1)
	if processor_number == 0 : sufix = ''
	else: sufix = str(processor_number -1)
	line = tmp[processor_number]

	if line.startswith("cpu%s"% (sufix)):
		cuse = float( line.split()[1] )
		cn = float( line.split()[2] )
		csys = float( line.split()[3])
		if sufix == '':
			load = cuse + cn
		else:
			load = cuse + csys + cn
		#load = int(load / .update_interval)
		return load
	return None

def cpu_get_cpu_name():
	try:
		f = open("/proc/cpuinfo", "r")
		tmp = f.readlines(500)
		f.close()
	except:
		print _("Failed to open /proc/cpuinfo")
		sys.exit(1)
		list = []
	for line in tmp:
		if line.startswith("model name"):
			return line.split(':')[1].strip()
	return ''

def cpu_get_cpu_list ():
	try:
		f = open("/proc/stat", "r")
		tmp = f.readlines(2000)
		f.close()
	except:
		print _("Failed to open /proc/stat")
		sys.exit(1)
	list = []
	for line in tmp:
		if line.startswith("cpu"):
			list.append(line.split(' ')[0])
			
	return list

def cpu_get_nb_cpu ():
	try:
		f = open("/proc/stat", "r")
		tmp = f.readlines(2000)
		f.close()
	except:
		print _("Failed to open /proc/stat")
		sys.exit(1)
	nb = 0
	for line in tmp:
		if line.startswith("cpu"):
			nb = nb+1
	return nb -1


###########################################
#                                         #
#                 System info             #
#                                         #
###########################################

# written by Hendrik Kaju
def sys_get_uptime_long ():
	try:
		f = open("/proc/uptime", "r")
		data1 = f.readline(100)
		f.close()
		uptime = float( data1.split()[0] )
		days = int( uptime / 60 / 60 / 24 )
		uptime = uptime - days * 60 * 60 * 24
		hours = int( uptime / 60 / 60 )
		uptime = uptime - hours * 60 * 60
		minutes = int( uptime / 60 )
		return _("%s days, %s hours and %s minutes") % (str(days), str(hours), str(minutes))
		#return str(days) + " days, " + str(hours) + " hours and " + str(minutes) + " minutes"
	except:
		print _("Failed to open /proc/uptime")
	return 'Error'

def sys_get_uptime():
	try:
		f = open("/proc/uptime", "r")
		tmp = f.readline(100)
		f.close()
		t = tmp.split()[0]
		h = int(float(t)/3600)
		m = int((float(t)-h*3600)/60)
		if m < 10:
			return str(h)+':'+'0'+str(m)
		else:
			return str(h)+':'+str(m)
	except:
		print _("Failed to open /proc/uptime")
	return 'Error'


def sys_get_username():
	res = commands.getstatusoutput('whoami')
	if res[0]==0:
		return res[1].strip()
	return ''


# written by Hendrik Kaju
def sys_get_hostname ():
	"""Get hostname"""
	try:
		f = open("/proc/sys/kernel/hostname", "r")
		hostname = f.readline(100)
		f.close()
		return hostname
	except:
		print _("Failed to open /proc/sys/kernel/hostname")
	return 'Error'

# written by Hendrik Kaju
def sys_get_average_load ():
	"""Get average load (as 3-tuple with floats)."""
	try:
		f = open("/proc/loadavg", "r")
		data = f.readline(100)
		f.close()
		load1 = str(float( data.split()[0] ))[:4]
		load2 = str(float( data.split()[1] ))[:4]
		load3 = str(float( data.split()[2] ))[:4]
		return load1+ ','+ load2 +','+ load3
	except:
		print _("Failed to open /proc/loadavg")
	return 'Error'
	
def sys_get_distrib_name():
	try:
		if os.path.exists('/etc/lsb-release') and str(commands.getoutput('cat /etc/lsb-release')).lower().find('ubuntu') != -1:
			return str(commands.getoutput('cat /etc/issue')).replace('\\n','').replace('\l','').replace('\r','').strip()

		elif os.path.exists('/etc/lsb-release'):
			return 'Debian ' + str(commands.getoutput('cat /etc/debian_version'))
		elif os.path.exists('/etc/mandriva-release'):
			return 'Mandriva ' + str(commands.getoutput("cat /etc/mandriva-release | sed -e 's/[A-Za-z ]* release //'"))
		elif os.path.exists('/etc/fedora-release'):
			return 'Fedora ' + str(commands.getoutput("cat /etc/fedora-release | sed -e 's/[A-Za-z ]* release //'"))
		elif os.path.exists('/etc/SuSE-release'):

			if str(commands.getoutput('cat /etc/SuSE-release')).lower().find('openSUSE') != -1:
				return 'openSUSE ' + str(commands.getoutput("""cat /etc/SuSE-release | grep "VERSION" | sed -e 's/VERSION = //'"""))
			else:
				return 'SUSE ' + str(commands.getoutput("""cat /etc/SuSE-release | grep "VERSION" | sed -e 's/VERSION = //'"""))
		elif os.path.exists('/etc/gentoo-release'):
			return 'Gentoo ' + str(commands.getoutput("cat /etc/gentoo-release | sed -e 's/[A-Za-z ]* release //'"))
		elif os.path.exists('/etc/slackware-version'):
			return 'Slackware ' + str(commands.getoutput("cat /etc/slackware-version | sed -e 's/Slackware //'"))
		elif os.path.exists('/etc/arch-release'):
			return 'Arch Linux'
		elif os.path.exists('/etc/redhat-release'):
			return 'Redhat ' + str(commands.getoutput("cat /etc/redhat-release | sed -e 's/[A-Za-z ]* release //'"))
		else:
			f = open("/etc/issue", "r")
			tmp = f.readlines(100)
			f.close()
			return tmp[0].replace('\\n','').replace('\l','').replace('\r','').strip()
	except:
		print _("Error getting distro name")
	return 'Error'


def sys_get_distroshort ():
	"""Get distro short name"""
	distros = commands.getoutput("lsb_release -is")
	return distros

def sys_get_desktop_enviroment():
	""" shows kde or gnome or xface"""
        if os.environ.get('KDE_FULL_SESSION') == 'true':
            desktop_environment = 'kde'
        elif os.environ.get('GNOME_DESKTOP_SESSION_ID'):
            desktop_environment = 'gnome'
        else:
            try:
		import commands
                info = commands.getoutput('xprop -root _DT_SAVE_MODE')
                if ' = "xfce4"' in info:
                    desktop_environment = 'xfce'
            except (OSError, RuntimeError):
                pass
	return desktop_environment

def sys_get_kernel_version():
	res = commands.getstatusoutput('uname -r')
	if res[0]==0:
		return res[1].strip()
	return _("Can't get kernel version")

def sys_get_kde_version():
	res = commands.getstatusoutput('kde-config --version')
	if res[0]==0:
		lst = res[1].splitlines()
		for i in lst:
			if i.startswith('KDE:'):
				return i[4:].strip()
	return _("Can't get KDE version")

def sys_get_gnome_version():
	res = commands.getstatusoutput('gnome-about --gnome-version')
	if res[0]==0:
		lst = res[1].splitlines()
		for i in lst:
			if i.startswith('Version:'):
				return i[8:].strip()
	return _("Can't get Gnome version")

# by whise
def sys_get_linux_version ():
	"""Get linux version string."""
	try:
		f = open("/proc/version", "r")
		data = f.readline(200)[:-1]
		f.close()
		return data
	except:
		return _("Failed to open /proc/version")

# by whise
# TODO: return dict and parse the output of cpuinfo (function does not much yet)
def sys_get_full_info ():	
	"""Get cpu info from /proc/cpuinfo."""
	return commands.getoutput("cat /proc/cpuinfo")

def sys_get_window_manager():
	root = gtk.gdk.get_default_root_window()
	try:
		ident = root.property_get("_NET_SUPPORTING_WM_CHECK", "WINDOW")[2]
		_WM_NAME_WIN = gtk.gdk.window_foreign_new(long(ident[0]))
	except TypeError, exc:
		_WM_NAME_WIN = ""

	name = ""
	win = _WM_NAME_WIN
	if (win != None):
		try:
			name = win.property_get("_NET_WM_NAME")[2]
		except TypeError, exc:

			return name

	return name

###########################################
#                                         #
#               Memory                    #
#                                         #
###########################################


def mem_get_freemem ():# written by Hendrik Kaju
	"""Get free memory."""
	cached = commands.getoutput("""cat /proc/meminfo | grep Cached | awk 'BEGIN {FS=":"} {print $2}' | awk '{print $1, $9}'""")
	buffers = commands.getoutput("""cat /proc/meminfo | grep Buffers | awk 'BEGIN {FS=":"} {print $2}' | awk '{print $1, $9}'""")
	free = commands.getoutput("""cat /proc/meminfo | grep MemFree | awk 'BEGIN {FS=":"} {print $2}' | awk '{print $1, $9}'""")
	return int(cached.split()[0])/1024 + int(buffers)/1024 + int(free)/1024


def mem_get_usedmem ():# written by Hendrik Kaju
	"""Get used memory."""
	total = commands.getoutput("""cat /proc/meminfo | grep MemTotal | awk 'BEGIN {FS=":"} {print $2}' | awk '{print $1, $9}'""")
	cached = commands.getoutput("""cat /proc/meminfo | grep Cached | awk 'BEGIN {FS=":"} {print $2}' | awk '{print $1, $9}'""")
	buffers = commands.getoutput("""cat /proc/meminfo | grep Buffers | awk 'BEGIN {FS=":"} {print $2}' | awk '{print $1, $9}'""")
	free = commands.getoutput("""cat /proc/meminfo | grep MemFree | awk 'BEGIN {FS=":"} {print $2}' | awk '{print $1, $9}'""")
	return int(total)/1024 - int(cached.split()[0])/1024 - \
		int(buffers)/1024 - int(free)/1024

def mem_get_usage():
	try:
		meminfo_file = open('/proc/meminfo')
		meminfo = {}
		for x in meminfo_file:
		    	try:
				(key,value,junk) = x.split(None, 2)
				key = key[:-1] 
				meminfo[key] = int(value)
			except:
				pass
		meminfo_file.close()
		return int((100*(int(meminfo['MemTotal'])-int(meminfo['Cached']) - int(meminfo['Buffers']) - int(meminfo['MemFree'])))/int(meminfo['MemTotal']))
	except:
		print(_("Can't parse /proc/meminfo"))
		return 0

def mem_get_total():
	try:
		meminfo_file = open('/proc/meminfo')
		meminfo = {}
		for x in meminfo_file:
		    	try:
				(key,value,junk) = x.split(None, 2)
				key = key[:-1] 
				meminfo[key] = int(value)
			except:
				pass
		meminfo_file.close()
		return int(meminfo['MemTotal'])/1024
	except:
		print("Can't parse /proc/meminfo")
		return 0

def mem_get_usedswap():
	try:
		meminfo_file = open('/proc/meminfo')
		meminfo = {}
		for x in meminfo_file:
			try:
				(key,value,junk) = x.split(None, 2)
				key = key[:-1]
				meminfo[key] = int(value)
			except:
				pass
		meminfo_file.close()
		if(meminfo['SwapTotal']==0):
			return 0
		return int((100*(int(meminfo['SwapTotal'])-int(meminfo['SwapCached']) - int(meminfo['SwapFree'])))/int(meminfo['SwapTotal']))
	except:
		print("Can't parse /proc/meminfo")
		return 0

def mem_get_totalswap():
	try:
		meminfo_file = open('/proc/meminfo')
		meminfo = {}
		for x in meminfo_file:
			try:
				(key,value,junk) = x.split(None, 2)
				key = key[:-1]
				meminfo[key] = int(value)
			except:
				pass
		meminfo_file.close()
		if(meminfo['SwapTotal']==0):
			return 0
		return int(meminfo['SwapTotal'])/1024
	except:
		print("Can't parse /proc/meminfo")
		return 0

###########################################
#                                         #
#               Disks                     #
#                                         #
###########################################


def disk_get_drive_info (mount_point):
	"""Returns info about the given mount point (as dict)."""
	proc = subprocess.Popen('df -h -a -P | grep ^/dev/ ', shell='true', 
		stdout=subprocess.PIPE)
	sdevs = proc.stdout.read().rsplit('\n')
	sdevs.pop()
	for stdev in sdevs:
		sdev = re.findall("(\S*)\s*", stdev)
		dev = {
			'device': sdev[0],
			'size': sdev[1],
			'used': sdev[2],
			'free': sdev[3],
			'quota': sdev[4],
			'mount': sdev[5]
		}
		if dev['mount'] == mount_point:
			return dev
	return None

def disk_get_swap ():
	"""Get a list of swap partitions."""
	try:
		f = open("/proc/swaps", "r")
		swap = f.read()
		f.close()
		swap = str(swap.split()[5:])
		swap = swap.replace("'","")
		swap = swap.replace("[","")
		swap = swap.replace("]","")
		swap = swap.replace(",","")
		return str(swap)
	except:
		print _("Failed to open /proc/swaps")
	return 'Error'

def disk_get_usage(disk_disk):
	res = commands.getoutput('df -h -a -P').splitlines()
	for i in res:
		if i.startswith('/dev/'):
			data = re.findall("(\S*)\s*", i)
			
			if (data[5] == disk_disk) or (data[0] == disk_disk):
				return data
	
def disk_get_disk_list():
	disks = []
	res = commands.getoutput('df -h -a -P').splitlines()
	for i in res:
		if i.startswith('/dev/'):
			data = re.findall("(\S*)\s*", i)
			disks.append(data[5])
	return disks


###########################################
#                                         #
#             Internet                    #
#                                         #
###########################################

def net_get_ip(): # by Whise
	"""Returns ip if it can"""
	ip = commands.getoutput("ifconfig")
	x = 0
	while True:
		ip = ip[ip.find("inet addr:"):]
		ip = ip[10:]
		ipc = ip[:ip.find(chr(32))]
		if ipc != '127.0.0.1' and ipc != None and ipc !='1': 
			
			return ipc
			

	return _('Cannot get ip')


def net_get_updown():
	try:
		f = open("/proc/net/dev", "r")
		data = f.readlines(2000)
		f.close()
		newNetUp = 0
		newNetDown = 0
		for i in data:
			if i.find(':') != -1 and i.strip().startswith('lo:') == False:
				v = i.split(':')[1].split()
				newNetUp = float( v[8] )+newNetUp
				newNetDown = float( v[0] )+newNetDown

	
		return (newNetUp/1024), (newNetDown/1024)
	except:
		print(_("Can't open /proc/net/dev"))
		return 0,0


def net_get_activity (device):
	"""This will return the total download and upload this session. As 2-tuple
	with floats)."""
	data = commands.getoutput("cat /proc/net/dev")
	data = data[data.find(device + ":") + 5:]
	return (float(data.split()[0]), float(data.split()[8]))


def net_get_connections ():
	"""This will return the number of connections."""
	data = commands.getoutput("netstat -n | grep -c tcp")
	
	return data

###########################################
#                                         #
#                 Wireless                #
#                                         #
###########################################

def wir_get_interfaces():
	try:
		interfaces = []
		f = open("/proc/net/wireless")
		cards = f.read(1024)
		f.close()
		for line in cards.splitlines():
			colon = line.find(":")
			if colon > 0:
				interfaces.append(line[:colon].strip())
		return interfaces
	except:
		print(_("Can't open /proc/net/wireless"))
		return []

def wir_get_stats (interface):
	"""Returns wireless stats as dict."""
	stats = {}
	iwcfd = os.popen("iwconfig " + interface)
	iwconfig = iwcfd.read(1024)
	iwcfd.close()
	essid = iwconfig[iwconfig.find('ESSID:"')+7:]
	stats['essid'] = essid[:essid.find('"')]
	if stats['essid'].strip()[:stats['essid'].strip().find("  ")] == "unassociated":
		return {"essid": _("Not connected"), "percentage": 0}
	else:
		bitrate = iwconfig[iwconfig.find("Bit Rate:")+9:]
		stats['bitrate'] = bitrate[:bitrate.find(" ")]
		quality = iwconfig[iwconfig.find("Link Quality")+13:]
		quality = quality[:quality.find(" ")]
		if quality.find("/") > 0:
			stats['quality'], stats['quality_max'] = quality.split("/")
		else:
			stats['quality'] = quality
		try:
			stats['percentage'] = int(float(stats['quality'])/float(stats['quality_max'])*100)
		except:
			return {"essid": _("Not connected"), "percentage": 0}
		signal = iwconfig[iwconfig.find("Signal level")+13:]
		stats['signal'] = signal[:signal.find("  ")]
		noise = iwconfig[iwconfig.find("Noise level")+12:]
		stats['noise'] = noise[:noise.find('\n')]
		return stats

###########################################
#                                         #
#                calendar                 #
#                                         #
###########################################


# by whise	
def cal_get_now ():
	"""Returns full now time and date"""	
	return str(datetime.now())


def cal_get_local_date ():
	"""returns date using local format"""	
	return str(datetime.now().strftime("%x"))

def cal_get_date ():
	"""returns date."""	
	return str(datetime.now().strftime("%d/%m/%Y"))

def cal_get_local_time ():
	"""returns time using local format"""	
	return str(datetime.now().strftime("%X"))

def cal_get_time ():
	"""returns time"""	
	return str(datetime.now().strftime("%H:%M:%S"))

def cal_get_time24 ():
	"""returns 24 hour time"""	
	return str(datetime.now().strftime("%R"))

def cal_get_time12 ():
	"""returns 12 hour time"""	
	return str(datetime.now().strftime("%r"))

def cal_get_year ():
	"""returns the years."""	
	return str(datetime.now().strftime("%Y"))

def cal_get_month ():
	"""returns the month"""	
	return str(datetime.now().strftime("%m"))

def cal_get_month_name ():
	"""returns the month name"""	
	return str(datetime.now().strftime("%B"))

def cal_get_day ():
	"""returns the day"""	
	return str(datetime.now().strftime("%d"))

def cal_get_day_monday ():
	"""returns the number of the day of the week starting from monday"""	
	return str(datetime.now().strftime("%u"))

def cal_get_day_sonday ():
	"""returns the number of the day of the week starting from sonday"""	
	return str(datetime.now().strftime("%w"))

def cal_get_day_name ():
	"""returns the day name"""	
	return str(datetime.now().strftime("%A"))

def cal_get_hour ():
	"""returns the hour"""	
	return str(datetime.now().strftime("%H"))

def cal_get_hour24 ():
	"""returns the hour"""	
	return str(datetime.now().strftime("%H"))

def cal_get_hour12 ():
	"""returns the hours"""	
	return str(datetime.now().strftime("%I"))

def cal_get_minute ():
	"""returns minutes"""	
	return str(datetime.now().strftime("%M"))

def cal_get_second ():
	"""returns seconds"""	
	return str(datetime.now().strftime("%S"))

def cal_get_ampm ():
	"""return am/pm or None if not available"""	
	return str(datetime.now().strftime("%p"))



###########################################
#                                         #
#               Battery                   #
#                                         #
###########################################


def bat_get_battery_list():
	try:
		path = "/proc/acpi/battery/"
		files = os.listdir(path)
		return files
	except:
		return[]
	
def bat_get_data(name):
	path = "/proc/acpi/battery/"+name+"/info"
	try:
		f = open(path)
		data = f.readlines()
		f.close()
		total = 0
		current = 0
		full = 0
		state = ''
		present = True
		for line in data:
			if line.startswith('present:') and line.find('yes')==-1:
				present = False
			elif line.startswith('design capacity:'):
				total = int(line.split(':')[1].strip().split(' ')[0])
			elif line.startswith('last full capacity:'):
				full = int(line.split(':')[1].strip().split(' ')[0])
		path = "/proc/acpi/battery/"+name+"/state"
		f = open(path)
		data = f.readlines()
		f.close()
		for line in data:	
			if line.startswith('present:') and line.find('yes')==-1:
				present = False
			elif line.startswith('remaining capacity:'):
				current = int(line.split(':')[1].strip().split(' ')[0])
			elif line.startswith('charging state:'):
				state = line.split(':')[1].strip().split(' ')[0]
		return total, current, full, state, present
	except:
		return 0, 0, 0, '', False

def bat_get_value(line):
	return line.split(':')[1].strip().split(' ')[0]


def bat_get_ac():
	data = commands.getoutput("acpi -V | grep AC | sed 's/.*: //'")
	return data

###########################################
#                                         #
#                 Processes               #
#                                         #
###########################################


def process_get_list():
	res = commands.getoutput('ps -eo pcpu,pmem,comm --sort pcpu').splitlines()
	l = res.__len__()
	return res,l

def process_get_top():
	res = commands.getoutput('ps axo comm,user,pcpu --sort=-pcpu | head -n 10')
	
	return res


###########################################
#                                         #
#               Custom Sensors            # thanks Mathieu Villegas for you great watermark
#                                         #
###########################################


def sensors_get_sensors_list():
	res = commands.getstatusoutput('sensors')
	output = ['Custom Sensors']	
	output.remove ('Custom Sensors')
	if res[0]==0:
		sol = res[1].replace(':\n ',': ').replace(':\n\t',': ').splitlines()
		for i in sol:
			i = i.strip()
			if (i.find('\xb0')!= -1) or (i.find('\xc2')!= -1) or (i.find('temp')!= -1) or (i.find('Temp')!= -1) or (i.find(' V ')!= -1) or (i.find(' RPM ')!= -1):
				output.append(i.lstrip())#.split(')')[0]+')')
	#now look for nvidia sensors
	res = commands.getstatusoutput(' nvidia-settings -q GPUAmbientTemp | grep :')
	if res[0] == 0:
		if res[1].strip().startswith('Attribute \'GPUAmbientTemp\''):
			sol = res[1].splitlines()[0].split('):')[1].strip()
			output.append('nvidia GPU ambiant: '+str(float(sol))+' C')
	res = commands.getstatusoutput(' nvidia-settings -q GPUCoreTemp | grep :')
	if res[0] == 0:
		if res[1].strip().startswith('Attribute \'GPUCoreTemp\''):
			sol = res[1].splitlines()[0].split('):')[1].strip()
			output.append('nvidia GPU core: '+str(float(sol))+'C')	
		
		
	#recherche des senseurs ACPI
	try:
		path = "/proc/acpi/thermal_zone/"
		files = os.listdir(path)
		for entry in files:
			try:
				f = open(path+entry+'/temperature', "r")
				tmp = f.readlines(200)
				f.close()
				val = tmp[0].replace('temperature:','').replace('C','').strip()
				output.append('acpi temperature '+entry+': '+val+'C')
			except:
				print(_("Can't open %s/temperature") % path+entry)
	except:
		print(_("Can't open folder /proc/acpi/thermal_zone/"))

	#recherche des senseurs IBM
	path = "/proc/acpi/ibm/thermal"
	try:
		f = open(path, "r")
		tmp = f.readlines(200)
		f.close()
		lst = tmp[0].split(' ')
		pos = 0
		for i in lst:
			i = i.strip()
			if i != '' and i != '-128':
				output.append('ibm temperature '+str(pos)+': '+i+'C')
			pos = pos+1
	except:
		print(_("Can't open %s") % path)
	
	path = "/proc/acpi/ibm/fan"
	try:
		f = open(path, "r")
		tmp = f.readlines(200)
		f.close()
		for i in tmp:
			if i.startswith('speed:'):
				output.append('ibm fan: '+i.split(':')[1].strip()+' RPM')
	except:
		print(_("Can't open %s") % path)
		
		#recherche des temperatures de disque
	res = commands.getstatusoutput("netcat 127.0.0.1 7634")
	if res[0] != 0:
		res = commands.getstatusoutput("nc 127.0.0.1 7634")
	if res[0] == 0:
		try:
			hddtemp_data = res[1].lstrip('|').rstrip('|')
			sol = hddtemp_data.split('||')
			for i in sol:
				if len(i)>1:
					lst = i.split('|')
					output.append("hddtemp sensor "+lst[0]+": "+lst[2]+" "+lst[3])
		except:
			print(_('Error during hddtemp drives search'))
	else:
		print(_('Hddtemp not installed'))
		return output


def sensors_get_sensor_value(sensorName):

	if sensorName.startswith('nvidia GPU ambiant'):
		res = commands.getstatusoutput(' nvidia-settings -q GPUAmbientTemp | grep :')
		if res[0] == 0:
			if res[1].strip().startswith('Attribute \'GPUAmbientTemp\''):
				#ici, je fais un str(float()) comme ca ca transforme 48. en 48.0
				return str(float(res[1].splitlines()[0].split('):')[1].strip()))+'C'
	elif sensorName.startswith('nvidia GPU core'):
		res = commands.getstatusoutput(' nvidia-settings -q GPUCoreTemp | grep :')
		if res[0] == 0:
			if res[1].strip().startswith('Attribute \'GPUCoreTemp\''):
				#ici, je fais un str(float()) comme ca ca transforme 48. en 48.0
				return str(float(res[1].splitlines()[0].split('):')[1].strip()))+'C'

	elif sensorName.startswith('acpi temperature'):
		name = sensorName.split()[2].strip()
		path = "/proc/acpi/thermal_zone/"+name+"/temperature"
		try:
			f = open(path, "r")
			tmp = f.readlines(200)
			f.close()
			val = tmp[0].replace('temperature:','').replace('C','').strip()
			
			return val+'C'
		except:
			print(_("can't read temperature in: %s") % path)
			return 'Error'

	elif sensorName.startswith('ibm temperature'):
		path = "/proc/acpi/ibm/thermal"
		try:
			name = sensorName
			f = open(path, "r")
			tmp = f.readlines(200)
			f.close()
			lst = tmp[0].split(' ')
			val = int(sensorName.split(' ')[2])
			return lst[val]+'C'
		except:
			print(_("Can't read value from %s") % path)
			return 'None'
		
	elif sensorName.startswith('ibm fan'):
		path = "/proc/acpi/ibm/fan"
		try:
			name = sensorName
			f = open(path, "r")
			tmp = f.readlines(200)
			f.close()
			for i in tmp:
				if i.startswith('speed:'):
		
					return i.split(':')[1].strip()+' RPM'
			return 'None'
		except:
			print(_("Can't read value from %s") % path)
			return 'None'

	elif sensorName.startswith('hddtemp sensor '):
		res = commands.getstatusoutput("netcat 127.0.0.1 7634")
		if res[0] != 0:
			res = commands.getstatusoutput("nc 127.0.0.1 7634")
		name = sensorName[15:]
		if res[0] == 0:
			hddtemp_data = res[1].lstrip('|').rstrip('|')
			sol = hddtemp_data.split('||')
			for i in sol:
				if len(i)>1:
					if i.startswith(name):
						lst = i.split('|')
						return lst[0]+": "+lst[2]+" "+lst[3]
		else:
			print(_('Hddtemp not installed'))
			return ''

	

		#maintenant, je recherche dans lm-sensors
	else:
		res = commands.getstatusoutput('sensors')
		if res[0] == 0:
			sol = res[1].replace(':\n ',': ').replace(':\n\t',': ').splitlines()
			for s in sol:
				s.strip()
				if s.startswith(sensorName):
					try:
						s = s.split(':')[1].strip(' ').strip('\t')
						i = 0
						while(((s[i]>='0') and (s[i]<='9')) or (s[i]=='.') or (s[i]=='+') or (s[i]=='-')):
							i = i+1
						return float(s[0:i])
					except:
						return 0









# ------------------------------------------------------------------------------
# CLASSES should not be used , calling classes from multiple screenlets instances causes erros due to goobject multiple instaces
# ------------------------------------------------------------------------------

class Sensor (gobject.GObject):
	"""A base class for deriving new Sensor-types from."""
	
	# define custom signals
	__gsignals__ = dict( \
		sensor_updated	= (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
		sensor_stopped	= (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()) )
	
	def __init__ (self, interval=1000):
		"""Create a new sensor which updates after the given interval."""
		gobject.GObject.__init__(self)
		self._timeout_id	= None
		self._interval		= interval
		# start sensor timeout
		self.set_interval(interval)
	
	# + public functions
	
	def get_interval (self):
		"""Get the update-interval time for this Sensor."""
		return self._interval
	
	def set_interval (self, ms):
		"""Set the update-interval time for this Sensor and start it."""
		if self._timeout_id:
			gobject.source_remove(self._timeout_id)
		if ms and ms > 10:
			self._interval		= ms
			self._timeout_id	= gobject.timeout_add(ms, self.__timeout)
			return True
		return False
	
	def stop (self):
		"""Immediately stop this sensor and emit the "sensor_stopped"-signal."""
		self.set_interval(0)
		self.emit('sensor_stopped')
	
	# + handlers to be overridden in subclasses
	
	def on_update (self):
		"""Override this handler in subclasses to implement your calculations
		and update the Sensor's attributes. Must return True to emit a signal
		which can then be handled within the screenlets, returning False
		causes the Sensor to be stopped.."""
		return True
	
	# + internals
	
	def __timeout (self):
		"""The timeout function. Does nothing but calling the on_update
		handler and emitting a signal if the handler returned True."""
		# call sensor's on_update-handler
		if self.on_update():
			self.emit('sensor_updated')			
			return True
		# on_update returned False? Stop
		self.stop()
		return False
	

class CPUSensor (Sensor):
	"""A very simple CPU-sensor."""
	
	def __init__ (self, interval=1000, cpu=0):
		"""Create a new CPUSensor which emits an 'sensor_updated'-signal after a
		given interval (default is 1000ms). The multi-cpu support is untested
		but theoretically works :)."""
		Sensor.__init__(self, interval)
		self._load 	= 0
		self._cpu	= cpu
	
	# + public functions
	
	def get_load (self):
		"""Return the current CPU-load."""
		return self._load
	
	# + internals
	
	def on_update (self, old_cuse=[0]):
		"""Called on each interval. Calculates the CPU-load and updates the
		internal load-value."""
		try:
			f = open("/proc/stat", "r")
			tmp = f.readlines(200)
			f.close()
		except:
			print _("CPUSensor: Failed to open /proc/stat. Sensor stopped.")
			self.stop()
		line = tmp[self._cpu + 1]
		if line[0:5] == "cpu%i " % self._cpu:
			reg = re.compile('[0-9]+')
			load_values = reg.findall(line[5:])
			# extract values from /proc/stat
			cuse = int(load_values[0])
			csys = int(load_values[2])
			load = cuse + csys - old_cuse[0]
			if load < 0: load = 0
			if load > 99: load = 99
			self._load = load
			old_cuse[0] = cuse + csys
			# return True to emit the "update_event"-signal
			return True
		return False


class MemorySensor (Sensor):
	
	def __init__ (self, interval=1000):
		"""Create a new RAMSensor which emits an 'sensor_updated'-signal after a
		given interval (default is 1000ms)."""
		Sensor.__init__(self, interval)
		self._freemem 	= 0
		self._usedmem	= 0
	
	# + public functions
	
	def get_freemem (self):
		"""Return the amount of currently free RAM."""
		return self._freemem
	
	def get_usedmem (self):
		"""Return the amount of currently used RAM."""
		return self._usedmem
	
	# + internals
	
	def on_update (self):
		"""Called on each interval. Calculates the load and updates the
		internal values."""
		self._freemem = get_freemem()
		self._usedmem = get_usedmem()
		return True
	

class NetSensor (Sensor):
	
	def __init__ (self, interval=1000, device='eth0'):
		"""Create a new NetSensor which emits an 'sensor_updated'-signal after a
		given interval (default is 1000ms)."""
		Sensor.__init__(self, interval)
		self._device = device
		self._downloaded, self._uploaded	= get_net_activity(device)
		self._last_down, self._last_up		= self._downloaded, self._uploaded
		
	# + public functions
	
	def get_upload_speed (self):
		"""Return the current upload speed in b/s."""
		return self._uploaded - self._last_up
	
	def get_download_speed (self):
		"""Return the current download speed in b/s."""
		return self._downloaded - self._last_down
	
	def get_uploaded (self):
		"""Return the overall upload amount."""
		return self._uploaded
	
	def get_downloaded (self):
		"""Return the overall download amount."""
		return self._downloaded
	
	# + internals
	
	def on_update (self):
		"""Called on each interval. Calculates the load and updates the
		internal values."""
		d, u = get_net_activity(self._device)
		self._last_up		= self._uploaded
		self._last_down		= self._downloaded
		self._downloaded	= int(d)
		self._uploaded		= int(u)
		#print get_net_activity(self._device)
		return True


# TEST:
if __name__ == '__main__':
	
	# some tests
	print get_hostname()
	print get_net_activity('eth0')
	print get_linux_version()
	print get_kernel()
	print get_cpu_info()
	
	# callbacks which get notified about updates of sensor's values
	def handle_cpusensor_updated (cs):
		print 'CPU0: %i%%' % cs.get_load()
	def handle_ramsensor_updated (rs):
		print 'USED RAM: %i MB' % rs.get_usedmem()
		print 'FREE RAM: %i MB' % rs.get_freemem()
	def handle_netsensor_updated (ns):
		#print (ns.get_upload_speed(), ns.get_download_speed())
		print 'UP/DOWN: %i/%i bytes/s' % (ns.get_upload_speed(), 
			ns.get_download_speed())
	
	# create sensors and connect callbacks to them
	cpu = CPUSensor()
	cpu.connect('sensor_updated', handle_cpusensor_updated)
	ram = MemorySensor(5000)
	ram.connect('sensor_updated', handle_ramsensor_updated)
	net = NetSensor(1500, 'eth0')
	net.connect('sensor_updated', handle_netsensor_updated)
	
	# start mainloop
	mainloop = gobject.MainLoop()
	mainloop.run()

