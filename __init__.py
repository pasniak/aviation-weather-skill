import requests
import re

from mycroft import MycroftSkill, intent_file_handler, intent_handler, util
from adapt.intent import IntentBuilder
from mycroft.skills.intent_service import AdaptIntent

from xml.etree import ElementTree
from dateutil import tz, parser
from datetime import timedelta



API_URL = "https://www.aviationweather.gov/"
RETRIEVE_METAR = API_URL + "adds/dataserver_current/httpparam?dataSource=metars&requestType=retrieve&format=xml&hoursBeforeNow=3&mostRecent=true&stationString={}"
RETRIEVE_TAF = API_URL + "adds/dataserver_current/httpparam?dataSource=tafs&requestType=retrieve&format=xml&hoursBeforeNow=3&mostRecent=true&stationString={}"

RABE = re.compile(r"(RA|SN)B(\d\d)E(\d\d)")
RAEB = re.compile(r"(RA|SN)E(\d\d)B(\d\d)")

class AviationWeather(MycroftSkill):
    def __init__(self):
        # state variables or setup actions
        MycroftSkill.__init__(self)

    def initialize(self):
        # skill settings are available here
        #my_setting = self.settings.get('my_setting')
        pass

    #Regex intent handler, triggered using a list of sample phrases in vocabulary.
    @intent_handler(
            AdaptIntent("MetarIntent")
            .require("Airport")
            .optionally("Name")
            )
    def handle_metar(self, message):
        airport_name = message.data.get('Name')
        if airport_name is not None:
            metar = self.most_recent(url = RETRIEVE_METAR.format(airport_name))
            self.say_metar(metar)
        else:
            self.speak('Metar Unable')

    #Regex intent handler, triggered using a list of sample phrases in vocabulary.
    @intent_handler(
            AdaptIntent("TafIntent")
            .require("Taf")
            .optionally("Name")
            )
    def handle_taf(self, message):
        self.log.info("TAF")
        airport_name = message.data.get('Name')
        if airport_name is not None:
            taf = self.most_recent(url = RETRIEVE_TAF.format(airport_name))
            self.say_taf(taf)
        else:
            self.speak('Taf Unable')

    def most_recent(self, url):
        self.log.info(url)
        response = requests.get(url, timeout=500)
        if 200 <= response.status_code < 300:
            return response.text
        else:
            self.log.warning('API returned status code: {}'.format(response.status_code))
            return None

    def say_metar(self, text):
        self.log.debug(text)
        xml = ElementTree.fromstring(text)
        for m in xml.findall('*/METAR'):
            # trick here is an element such as temp_c might be missing
            # if so, I will iterate over it and not speak it, therefore
            # I just need to code all possible entries in METAR
            raw_text = m.find('raw_text').text
            self.log.info(raw_text)
            for typ in m.iter('metar_type'):
                if (typ.text != 'METAR'):
                    self.speak(typ.text.lower())
            for station in m.iter('station_id'):
                self.speak('Metar for ' + " ".join(list(station.text)))

            for obs in m.iter('observation_time'):
                metartime = parser.parse(obs.text)
                self.say_when_ago('observed', metartime)

            for cond in m.iter('flight_category'):
                self.speak(" ".join(list(cond.text)))
            for temp in m.iter('temp_c'):
                self.speak('Temperature ' + nozeros(temp.text) + ' Celsius')
            for temp in m.iter('dewpoint_c'):
                self.speak('Dewpoint ' + nozeros(temp.text))

            self.say_wind_vis_clouds(m)

            for precip in m.iter('precip_in'):
                self.speak(precip.text + ' inches of precipitation in the last hour')

            rab = RABE.search(raw_text)
            if rab:
                precip_typ = "Rain" if (rab.group(1)=='RA') else "Snow"
                self.speak(precip_typ + " began " + rab.group(2) + ", ended " + rab.group(3) + " minutes past the hour")
            rae = RAEB.search(raw_text)
            if rae:
                precip_typ = "Rain" if (rae.group(1)=='RA') else "Snow"
                self.speak(precip_typ + " ended " + rae.group(2) + ", began " + rae.group(3) + " minutes past the hour")

    def say_wind_vis_clouds(self, m):
        for wx in m.iter('wx_string'):
            self.speak(", ".join(map(wx_decode, wx.text.split(" "))))

        for windspd in m.iter('wind_speed_kt'):
            if (windspd.text != "0"): #only if there's wind
                for winddir in m.iter('wind_dir_degrees'):
                    if (winddir.text == "0"):
                        self.speak("North wind")
                    else:
                        self.speak('Wind ' + " ".join(list(winddir.text)))
                for w in m.iter('wind_speed_kt'):
                    self.speak(w.text + ' knots')

        for wind in m.iter('wind_gust_kt'):
            self.speak('Gusting to ' + wind.text)

        for vis in m.iter('visibility_statute_mi'):
            miles = nozeros(vis.text) 
            self.speak('Visibility ' + miles + (' mile' if float(miles) <= 1 else ' miles'))
        for sky in m.iter('sky_condition'):
            self.speak(str(
                " ".join(map(sky_cover, list(sky.attrib.values())))
                )
            )

    def say_taf(self, text):
        self.log.debug(text)
        xml = ElementTree.fromstring(text)
        for t in xml.findall('*/TAF'):
            # trick here is an element such as temp_c might be missing
            # if so, I will iterate over it and not speak it, therefore
            # I just need to code all possible entries in METAR
            self.log.info(t.find('raw_text').text)

            for obs in t.iter('issue_time'):
                metartime = parser.parse(obs.text)
                self.say_when_ago('issued', metartime)

            for f in t.iter('forecast'):
                for frm in f.iter('fcst_time_from'):
                    fromtime = parser.parse(frm.text)
                for to in f.iter('fcst_time_to'):
                    totime = parser.parse(to.text)
                self.say_fromto(fromtime, totime)
                self.say_wind_vis_clouds(f)
 
    def say_when_ago(self, what, time_of_event):
        now = util.time.now_utc()
        delay = (now - time_of_event) 
        self.speak(what + ' ' + strfdelta(delay, "%H hours, %M minutes ago" if delay.seconds>60*60 else "%M minutes ago"))

    def say_when(self, what, time_of_event):
        self.speak(what + ' ' + str(time_of_event.hour)+' zulu')

    def say_fromto(self, time_of_event1, time_of_event2):
        self.speak('from ' + str(time_of_event1.hour)+' to '+str(time_of_event2.hour)+ ' zulu') # UTC sounds bad


def nozeros(s):
    return substr(s,'.0')

#returns string `s` without postfix `sub`
def substr(s,sub):
    return s[:s.find(sub)]

def sky_cover(x):
    return 'sky clear' if x=='CLR' else 'scattered clouds at' if x=='SCT' else 'few clouds at' if x=='FEW' else 'broken clouds at' if x=='BKN' else 'overcast at' if x=='OVC' else x


def wx_decode(x):
    switch = {
        'VC':'in vicinity',

        'RA':'rain',
        'DZ':'drizzle',
        'SN':'snow',
        'SG':'snow grains',
        'PL':'ice pellets',
        'IC':'ice crystals',
        'GR':'hail',
        'GS':'small hail',
        'UP':'unknown precipitation',
        'FG':'fog',
        'VA':'volcanic ash',
        'BR':'mist',
        'HZ':'haze',
        'DU':'widespread dust',
        'FU':'smoke',
        'SA':'sand',
        'PY':'spray',
        'SQ':'squall',
        'PO':'sand whirls',
        'DS':'duststorm',
        'SS':'sandstorm',
        'FC':'funnel cloud',

        'SH':'showers',
        'MI':'shallow',
        'BC':'patches',
        'PR':'partial',
        'DR':'drifting',
        'TS':'thunderstorm',
        'BL':'blowing',
        'FZ':'freezing'
    }
    modifier = 'light ' if x[0]=='-' else 'heavy ' if x[0]=='+' else ''
    return modifier + switch.get(x[-2:], "")

from string import Template

class DeltaTemplate(Template):
    delimiter = '%'

# https://stackoverflow.com/questions/8906926/formatting-timedelta-objects
def strfdelta(td, fmt):

    # Get the timedelta’s sign and absolute number of seconds.
    sign = "-" if td.days < 0 else "+"
    secs = abs(td).total_seconds()

    # Break the seconds into more readable quantities.
    days, rem = divmod(secs, 86400)  # Seconds per day: 24 * 60 * 60
    hours, rem = divmod(rem, 3600)  # Seconds per hour: 60 * 60
    mins, secs = divmod(rem, 60)

    # Format (as per above answers) and return the result string.
    t = DeltaTemplate(fmt)
    return t.substitute(
        s=sign,
        D="{:d}".format(int(days)),
        H="{:02d}".format(int(hours)),
        M="{:02d}".format(int(mins)),
        S="{:02d}".format(int(secs)),
        )



def create_skill():
    return AviationWeather()

