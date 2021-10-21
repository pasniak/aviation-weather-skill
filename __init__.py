import requests
from mycroft import MycroftSkill, intent_file_handler, util
from xml.etree import ElementTree
from dateutil import tz, parser
from datetime import timedelta



API_URL = "https://www.aviationweather.gov/"
RETRIEVE = API_URL  +  "adds/dataserver_current/httpparam?dataSource=metars&requestType=retrieve&format=xml&hoursBeforeNow=3&mostRecent=true&stationString={}"


class AviationWeather(MycroftSkill):
    def __init__(self):
        # state variables or setup actions
        MycroftSkill.__init__(self)

    def initialize(self):
        # skill settings are available here
        #my_setting = self.settings.get('my_setting')
        self.register_entity_file('letter.entity')
        self.register_entity_file('numbers.entity')
        pass

    # Padatious intent handler, triggered using a list of sample phrases.
    @intent_file_handler('metar.intent')
    def handle_metar(self, message):
        airport_name = message.data.get('apt_name')
        airport_letter = message.data.get('letter')
        airport_num = message.data.get('numbers')
        if airport_name is not None:
            metar = self.retrieve_most_recent(airport_name)
            self.log.debug(metar)
            self.say_metar(metar)
        elif airport_letter is not None and airport_num is not None:
            airport_id = airport_letter  +  airport_num
            metar = self.retrieve_most_recent(airport_id)
            self.log.debug(metar)
            self.say_metar(metar)
        else:
            self.speak('Unable')

    def retrieve_most_recent(self, apt):
        url = RETRIEVE.format(apt)
        self.log.debug(url)
        response = requests.get(url, timeout=500)
        if 200 <= response.status_code < 300:
            return response.text
        else:
            self.log.warning('API returned status code: {}'.format(response.status_code))
            return None

    def say_metar(self, text):
        xml = ElementTree.fromstring(text)
        for m in xml.findall('*/METAR'):
            # trick here is an element such as temp_c might be missing
            # if so, I will iterate over it and not speak it, therefore
            # I just need to code all possible entries in METAR
            self.log.info(m.find('raw_text').text)
            for typ in m.iter('metar_type'):
                if (typ.text != 'METAR'):
                    self.speak(typ.text.lower())
            for station in m.iter('station_id'):
                self.speak('Metar for ' + " ".join(list(station.text)))

            for obs in m.iter('observation_time'):
                metartime = parser.parse(obs.text)
                now = util.time.now_utc()
                delay = (now - metartime) 
                self.speak('observed ' + strfdelta(delay, "%H hours, %M minutes ago" if delay.seconds>60*60 else "%M minutes ago"))

            for cond in m.iter('flight_category'):
                self.speak(" ".join(list(cond.text)))
            for temp in m.iter('temp_c'):
                self.speak('Temperature ' + temp.text + ' Celsius')
            for temp in m.iter('dewpoint_c'):
                self.speak('Dewpoint ' + temp.text)
            for wind in m.iter('wind_dir_degrees'):
                self.speak('Wind ' + " ".join(list(wind.text)))
            for wind in m.iter('wind_speed_kt'):
                self.speak(wind.text + ' knots')
            for wind in m.iter('wind_gust_kt'):
                self.speak('Gusting to ' + wind.text)
            for vis in m.iter('visibility_statute_mi'):
                self.speak('Visibility ' + substr(vis.text, '.0') + ' miles')
            for wx in m.iter('wx_string'):
                self.speak(", ".join(map(wx_decode, wx.text.split(" "))))

            for sky in m.iter('sky_condition'):
                self.speak(str(
                    " ".join(map(sky_cover, list(sky.attrib.values())))
                    )
                )

            for precip in m.iter('precip_in'):
                self.speak(precip.text + ' inches of precipitation in the last hour')



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

