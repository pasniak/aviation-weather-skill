# <img src="https://raw.githack.com/FortAwesome/Font-Awesome/master/svgs/solid/plane-departure.svg" card_color="#22A7F0" width="50" height="50" style="vertical-align:bottom"/> Aviation Weather
Aviation weather checker

## About
Checks current weather (METAR) at a given airport

## Examples
* "METAR KJFK" (for New York's JFK)
* "airport KTTN" (for TTN in Trenton, NJ)
* "airport LFPG" (for Paris CDG)

A reply will be something along:
```
Metar for KTTN
Observed 53 minutes ago
VFR
Temperature 18.3 Celsius
Dewpoint 10.0
Wind 230
5 knots
Visibility 10 miles
sky clear
```

## Third party
This skill uses FAA's Aviation Digital Data Service: https://www.aviationweather.gov/adds/.

## Credits
pasniak

## Category
**Productivity** **Aviation**

## Tags
#Weather #airport

## Installation
Once you ssh to your PiCroft:

In mycroft-cli-client, type:
```
install https://github.com/pasniak/aviation-weather-skill
```
and follow the installation.

Alternatively, in the shell execute:
```
cd /opt/mycroft/skills
git clone https://github.com/pasniak/aviation-weather-skill
```
Wait a bit until mycroft service updates your skills.
