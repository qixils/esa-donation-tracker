import urllib, json
import re
import dateutil.parser
from datetime import datetime, timedelta
from itertools import izip_longest, tee

import tracker.models as models
import tracker.viewutil as viewutil
import tracker.prizemail as prizemail
import tracker.commandutil as commandutil

BASE_URL = "https://horaro.org/"

class Column:
    def __init__(self, name, index):
        self.name = name
        self.index = index

class Columns:
    def __init__(self, p="Player(s)", g="Game", c="Category", pf="Platform", i="ID"):
        self.player = Column(p, -1)
        self.game = Column(g, -1)
        self.category = Column(c, -1)
        self.platform = Column(pf, -1)
        self.id = Column(i, -1)

    def updateColumnIndicies(self, columnMapping):
        for i, col in enumerate(columnMapping):
            if col == self.player.name:
                self.player.index = i
            if col == self.game.name:
                self.game.index = i
            if col == self.category.name:
                self.category.index = i
            if col == self.platform.name:
                self.platform.index = i
            if col == self.id.name:
                self.id.index = i


def UpdateSchedule(event, horaro_id, columns, **kwargs):
    url = ScheduleUrl(horaro_id)
    data = DownloadSchedule(url)

    #Remove any existing order to prevent duplicate orders and so we can delete all the unordered ones afterwards.
    models.SpeedRun.objects.filter(event=event.id).update(order=None)

    raw_runs = data['schedule']['items']
    base_setup_time = (data['schedule']['setup_t']) * 1000

    columns.updateColumnIndicies(data['schedule']['columns'])

    order=0
    for raw_run in raw_runs:
        order += 1
        setup_time = get_setup_time(raw_run, base_setup_time)
        get_run(event, columns, order, raw_run, setup_time)

    else:
        print("Deleting {0} runs".format(models.SpeedRun.objects.filter(event=event.id,order=None).count()))
        #Clear out any old runs that still linger, which means they are deleted from Horaro.
        models.SpeedRun.objects.filter(event=event.id,order=None).delete()

def ScheduleUrl(eventName):
    return BASE_URL + eventName + ".json?named=true"

def DownloadSchedule(url, **kwargs):
    return json.loads(urllib.urlopen(url).read())

def DownloadScheduleColumns(eventName):
    data = DownloadSchedule(ScheduleUrl(eventName))
    return data['schedule']['columns']
            
offline_id = 1

def get_run(event, columns, order, json_run, setup_time = 0):
    
    horaro_id = None
    if columns.id.index > -1:
        horaro_id = json_run['data'][columns.id.index]

    name = speedrun_name(json_run, columns)
    category = json_run['data'][columns.category.index] or "Sleep%"
    print(horaro_id, name, category, setup_time)

    run = None

    try:
        if horaro_id != None:
            #First try to find a run with the stored id if we have one.
            run = models.SpeedRun.objects.get(external_id__iexact=horaro_id)
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
        if horaro_id != None:
            #Set id if we have one.
            run.external_id = horaro_id

    if run != None:
        update_run(run, horaro_id, columns, order, json_run, setup_time)
        return run

    return None

def update_run(run, horaro_id, columns, order, json_run, setup_time):
    start_time = dateutil.parser.parse(json_run['scheduled'])
    run_duration = timedelta(seconds=json_run['length_t'])

    if horaro_id != None and run.external_id == None:
        #Set id if one is found and there was none previously.
        run.external_id = horaro_id

    run.order = order
    run.starttime = start_time
    run.endtime = start_time+run_duration

    if columns.platform.index > -1:
        run.console = json_run['data'][columns.platform.index]
    if run.console == None:
        print("DEBUG: No console found. Using N/A instead.")
        run.console = "N/A"

    run.run_time = json_run['length_t']*1000
    run.setup_time = setup_time
    
    run.save()

    if json_run['data'][columns.player.index]:
        runner_column = json_run['data'][columns.player.index]
        if runner_column[0] == '[':
            #ESA mode
            raw_runners = re.findall(r"\[([^ \[\]]*)\]\(([^ \(\)]*)\)", runner_column)

            for raw_runner in raw_runners:
                runner_name = raw_runner[0]
                runner_stream = raw_runner[1]
                runner = get_runner(runner_name, runner_stream)
                if runner != None:
                    run.runners.add(runner)
                    run.save()

def speedrun_name(json_run, columns):
    name = json_run['data'][columns.game.index]
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

def parse_duration(duration):
    num = int(duration[:-1])
    if duration.endswith('s'):
        return timedelta(seconds=num)
    elif duration.endswith('m'):
        return timedelta(minutes=num)
    elif duration.endswith('h'):
        return timedelta(hours=num)
    elif duration.endswith('d'):
        return timedelta(days=num)

def get_setup_time(previous, base_setup_time=600000):
    setup_time = base_setup_time
    if previous != None and 'options' in previous and previous['options'] != None and 'setup' in previous['options']:
        setup_time = parse_time(previous['options']['setup']).seconds * 1000
    return setup_time


time_regex = re.compile(r'((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')

def parse_time(time_str):
    parts = time_regex.match(time_str)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}
    for (name, param) in parts.iteritems():
        if param:
           time_params[name] = int(param)
    return timedelta(**time_params)
