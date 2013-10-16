import datetime
import argparse 
import csv


def parse_date(datestr):
    from dateutil import parser 
    if not datestr: 
        return None 
    else: 
        return parser.parse(datestr)

class IssueState (object):
    def __init__(self):
        self.repo = None 
        self.number = None 
        self.url = None 
        self.name = None 
        self.size = None 
        self.opened = None 
        self.started = None 
        self.done = None 
        self.closed = None 
        self.committers = None 
    
    def __cmp__(self, other):
        if self.started and other.started: 
            return cmp(self.started, other.started)
        elif self.started: 
            return -1 
        elif other.started: 
            return 1 
        else:
            return cmp(self.opened, other.opened)


def main(): 
    p = argparse.ArgumentParser("review", 
                                description="Generate a CSV for review from daily trackers")

    p.add_argument("startdate", help="Starting date of sprint (first tracker date)")
    p.add_argument("trackers", nargs="+", 
                   help="Names of tracking spreadsheet CSV files ('none' skips a day)")

    p.add_argument("-o", "--outfile", help="Output CSV to file")
    
    opts = vars(p.parse_args()) 

    outfile = opts.get("outfile", "csvout.csv")
    start = parse_date(opts.get("startdate"))
    dateoff = 0 
   
    issues = {}

    print "Reading tracking spreadsheets..."

    for f in opts.get("trackers"): 
        if f == "none":
            dateoff += 1
            continue 

        rows = [] 
        today = start + datetime.timedelta(days=dateoff)

        print "%s (%s)" % (f, today)

        with open(f, "r") as csvdata: 
            reader = csv.reader(csvdata)
            rows = [r for r in reader]
    
        mentioned = [] 

        for r in rows: 
            print len(r), r
            repo, number, url, name, size, working, done, committers, labels = r[:9] 

            if issues.has_key(number):
                i = issues.get(number)
            else: 
                i = IssueState()
                i.repo = repo
                i.number = number 
                i.url = url
                i.name = name 
                i.size = size 
                i.opened = today 
                issues[number] = i
            
            if working and i.started is None:
                i.started = today 

            if done and i.done is None: 
                i.done = today 
                
            if committers and (i.committers is None or i.committers != committers): 
                i.committers = committers 

        for num, issue in issues.items(): 
            if num not in mentioned and issue.started is not None and issue.closed is None:
                issue.closed = today 

    print "Writing CSV..." 

    with open(outfile, "w+") as csvdata: 
        w = csv.writer(csvdata)
        for num in sorted(issues, key=lambda i: issues[i]):
            i = issues.get(num)
            w.writerow([i.repo, i.number, i.url, i.name, 
                        i.opened, i.started, i.done, i.closed, i.committers])

    print "Finished" 

main()
