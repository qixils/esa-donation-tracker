import urllib
import json
import re
import dateutil.parser
from datetime import datetime, timedelta
# from itertools import izip_longest, tee

import tracker.models as models
# import tracker.viewutil as viewutil
# import tracker.prizemail as prizemail
# import tracker.commandutil as commandutil

BASE_URL = "https://oengus.io/api/"

class OengusOpener(urllib.URLopener):
    def __init__(self):
        self.version = 'Mozilla/5.0 (Macintosh; U; PPC Mac OS X Mach-O; sv-SE; rv:1.8b5) Gecko/20051006 Firefox/1.4.1'
        urllib.URLopener.__init__(self)


def UpdateSchedule(event, oengus_id, **kwargs):
    url = ScheduleUrl(oengus_id)
    print("DEBUG: Downloading schedule from " + url)
    data = DownloadSchedule(url)

    #Remove any existing order to prevent duplicate orders and so we can delete all the unordered ones afterwards.
    models.SpeedRun.objects.filter(event=event.id).update(order=None)

    raw_runs = data['lines']

    order=0
    for raw_run in raw_runs:
        order += 1
        setup_time = get_setup_time(raw_run, 0)
        get_run(event, order, raw_run, setup_time)

    else:
        print("Deleting {0} runs".format(models.SpeedRun.objects.filter(event=event.id,order=None).count()))
        #Clear out any old runs that still linger, which means they are deleted from Horaro.
        models.SpeedRun.objects.filter(event=event.id,order=None).delete()

def ScheduleUrl(eventName):
    return BASE_URL + "marathons/" + eventName + "/schedule/"

def DownloadSchedule(url, **kwargs):
    opener = OengusOpener()
    data = opener.open(url).read()
    return json.loads(data)

def DownloadScheduleColumns(eventName):
    data = DownloadSchedule(ScheduleUrl(eventName))
    return data['schedule']['columns']
            
offline_id = 1

def get_run(event, order, json_run, setup_time = 0):
    
    oengus_id = None
    oengus_id = str(json_run['id'])

    name = speedrun_name(json_run)
    category = json_run['categoryName'] or "Sleep%"
    print(oengus_id, name, category, setup_time)

    run = None

    try:
        if oengus_id != None:
            #First try to find a run with the stored id if we have one.
            run = models.SpeedRun.objects.get(external_id__iexact=oengus_id)
        else: 
            # If it does not exist, try looking for one with exact same name, category and event (tables keys).
            run = models.SpeedRun.objects.get(name__iexact=name, category__iexact=category, event=event)
    except models.SpeedRun.DoesNotExist:
        # Run does not exist at all. Create a new one.
        run = models.SpeedRun(
            name = name,
            category = category,
            event = event,
        )
        if oengus_id != None:
            #Set id if we have one.
            run.external_id = oengus_id

    if run != None:
        update_run(run, oengus_id, order, json_run, setup_time, event)
        return run

    return None

def update_run(run, oengus_id, order, json_run, setup_time, event=None):
    #FIX THESE TWO vvvvvvvv
    start_time = dateutil.parser.parse(json_run['date'])
    run_duration = timedelta(seconds=parse_time(json_run['estimate']).seconds*1000)

    if oengus_id != None and run.external_id == None:
        #Set id if one is found and there was none previously.
        run.external_id = oengus_id
    if (run.external_id != None):
        run.name = speedrun_name(json_run)
        run.category = json_run['categoryName'] or "Sleep%"
        if (event != None):
            run.event = event

    run.order = order
    run.starttime = start_time
    run.endtime = start_time+run_duration

    run.console = json_run['console']
    if run.console == None:
        print("DEBUG: No console found. Using N/A instead.")
        run.console = "N/A"

    run.run_time = run_duration.total_seconds()
    run.setup_time = setup_time
    
    run.save()

    if json_run['runners']:
        runners = json_run['runners']
        for runner in runners:
            runner_name = runner['username']
            runner_stream = findRunnerStream(runner)
            runner = get_runner(runner_name, runner_stream)
            if runner != None:
                run.runners.add(runner)
                run.save()

def speedrun_name(json_run):
    name = json_run['gameName']
    if name[0] == '[':
        name_match = re.match(r"^\[(.*)\]\((.*)\)?", name, flags=re.U or re.S)
        if name_match:
            name = name_match.group(1)

    if name == "OFFLINE":
        global offline_id
        name = "OFFLINE {0}".format(offline_id)
        offline_id += 1

    name = name[:64] #Truncate becuase DB limitation
    return name

def get_runner(name, stream):
    try:
        return models.Runner.objects.get(name=name)

    except models.Runner.DoesNotExist: 
        runner = models.Runner(
            name = name,
            stream = stream,
            donor = get_donor(name)
        )
        runner.save()

        return runner
    return None

def get_donor(name):
    try: 
        return models.Donor.objects.get(alias=name)
    except models.Donor.DoesNotExist:
        return None

def findRunnerStream(runner):
    for connection in runner['connections']:
        if connection['platform'] == 'TWITCH':
            return "twitch.tv/"+connection['username']
    return ''

def get_setup_time(previous, base_setup_time=600000):
    setup_time = base_setup_time
    if previous != None and 'setupTime' in previous:
        setup_time = parse_time(previous['setupTime']).seconds * 1000
    return setup_time


time_regex = re.compile(r'PT((?P<hours>\d+?)H)?((?P<minutes>\d+?)M)?((?P<seconds>\d+?)S)?')

def parse_time(time_str):
    parts = time_regex.match(time_str)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}
    for (name, param) in parts.iteritems():
        if param:
           time_params[name] = int(param)
    #print("DEBUG: {0} hours {1} minutes {2} seconds parsed from {3}".format(parts["hours"], parts["minutes"], parts["seconds"], time_str))
    return timedelta(**time_params)
