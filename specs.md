Introduction:

This is a home assistant integration that reads that of a SAJ solar inverter through its provided endpoints.

The integration should follow the most recent best practices for a home assistant integration which includes:
-config flow to allow configuration through the UI
-allow reconfigure the entry, particularly since the inverter ip or username might change at some point
-use a coordinator to periodically poll data from the inverter
-generate an inverter device with its entities assigned to it


## configuration
the configuration should ask the user for the following information:
host: host or ip,
name: name for the device,
username: optional, for accessing the endpoint when it requires basic http auth,
password: optional, for accessing the endpoint when it requires basic http auth
polling time: how often to poll. defaults to 30 seconds

##The endpoint
the inverter has an endpoint in http://ip/status/status.php which returns a series of values separatedby a comma. example:
1,2535833,157394,1512,73, 1969,767,1982,750,65535,65535,0,0,65535,65535,0,0,65535,65535,0,0,65535,65535,2913,4998,2347,1236,65535,65535,65535,65535,3649,494,199062,2

values 65535 are to be interpreted as unavailable

##value mapping to sensor

These are the values indexes and their meaning I need polled and assigned to entities alogn with how they should be interpreted

0   status (online is 1, offline 0 which might happen when it's on but not converting power yet)
1   total generated energy (divide by 100 for kwh)
2   total running time (divide by 10 for hours)
3   today generated energy (divide by 100 for watts)
4   today running time (dievide by 10 for hours)

5   pv1 voltage (all voltages should be divided by 10 so 2073 is 207.3v)
6   pv1 current (all currents  should be divided by 100 so 514 is 5.14 amps)
7   pv2 voltage
8   pv2 current
9   pv3 voltage
10  pv4 current

11  pv1 strcurr1
12  pv1 strcurr2
13  pv1 strcurr3
14  pv1 strcurr4
15  pv2 strcurr1
16  pv2 strcurr2
17  pv2 strcurr3
18  pv2 strcurr4
19  pv3 strcurr1
20  pv3 strcurr2
21  pv3 strcurr3
22  pv3 strcurr4

23  grid-connected power (in watts, as is)
24  grid connected frequency (divided by 100 so 5004 is 50.02hz)
25  line1 voltage
26  line1 current
27  line2 voltage
28  line2 current
29  line3 voltage
30  line3 current

31  bus voltage (divide by 10 so 3649 is 364.9v)
32  temperature (divide by 10 494 is 49.4c)
33  co2 reduction (divide by 10 so 1000 is 100kg )
34  running state

#inverter info:

The inverter is a grid tied inverter so it might shutdown when there is no enough light for it to work, so it wont respond to requests at that time, this integration should handle a no response setting the  device / entities as unavailable.



#information of the integration
the name is "SAJ R5 integration"
domain is saj_r5
codeowner is santiagozky
my github account is github.com/santiagozky

#deploying 
you should only deploy when explicitly asked for it.
the deployment is done by copying the integration directory to my hass stage environment
ssh to host ubuntu2 and my stage hass is in /var/homeassistant.stage/custom_components
my user has a ssh key so no password is needed
you can restar home assistant after copying the files using docker compose in 
/home/santiago/services/ubuntu2/home-assistant-stage
with $ docker compose restart (no sudo needed)
