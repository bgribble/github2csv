### github2csv -- Report on GitHub issues in CSV format

I have been using GitHub issues as part of a scrum-like development
process.  I developed this tool to help with planning, daily standup, and
sprint post-mortem review processes.   It queries the GitHub v3 API,
filters issues on specified criteria, and produces a CSV output file with
one issue per line and a selection of fields for each.

Please see the "Scrum workflow" section below for usage examples.


### Installation

Requires Python 2.7.

Requires 'githubv3.py' at least 0.7.0, which you can get at:

    https://github.com/sigmavirus24/github3.py

As of right now (18-Sep-2013), there's a purported version 0.7.0 on pypi
which doesn't work with github2csv... the API of iter_commits has changed
and will cause errors if you have a version that's too old.

To install:

    python ./setup.py install

### Usage

```
$ github2csv -h
usage: github2csv [-h] [-c CONFFILE] [-r REPO] [-u USER] [-p PASSWORD]
                  [-m MILESTONE] [-n] [-s] [-l] [-o OUTFILE] [-d] [-a] [-g]
optional arguments:
  -h, --help            show this help message and exit
  -c CONFFILE, --conffile CONFFILE
                        Config file name
  -r REPO, --repo REPO  Repository name (as 'owner/repo')
  -u USER, --user USER  GitHub username
  -p PASSWORD, --password PASSWORD
                        GitHub password
  -m MILESTONE, --milestone MILESTONE
                        GitHub milestone
  -n, --unsized         Get unsized open issues
  -s, --sized           Get sized open issues
  -l, --labels          Get labels too
  -o OUTFILE, --outfile OUTFILE
                        CSV file to write
  -d, --daily           Daily activity report
  -a, --all             Get open and closed tickets
  -g, --git-commits     Get Git commit activity
```

### Configuration file

github2csv uses ConfigParser to provide default options that can be
overridden by the command line.  Template file:

    [github2csv]
    user=[github username]
    password=[github password]
    repo=[ghowner_1/repository_1, ghowner_2/repository_2, ...]
    outfile=[filename]
    milestone=[default milestone]
    sizes=[label1: points1, label2: points2, label3: points3 ...]


### GitHub Workflow

The tool can be configured, but is also somewhat tied in to the way I use
GitHub, so let me mention a few things about that.

#### Milestones

There are generally 2 milestones that are relevant at any time.
Tickets are created as part of the "product backlog milestone".
They stay there until a sprint planning meeting moves them into a
"sprint milestone".  Reports for size voting or priority
assignment/sprint inclusion will pull from the backlog milestone.
Daily tracking and postmortem reports pull from the sprint milestone.

#### Labels

I use lots of GitHub labels.  The ones that are relevant for this tool:

   working: This is set before or during a standup to indicate that the
            issue is being actively worked.  This starts the clock for
            post-mortem sizing checks.

   done:    This is set when the developer believes the issue is complete
            and ready for acceptance and rollout.

   XS, S, M, L, XL, XXL: Our size labels.  These are assigned by the
            scrum master after a size voting process.  You can use
            different size labels, but this tool will be most useful if
            you use labels to represent the different issue sizes.

#### Commits

In my scrums, I require that a commit message includes the GitHub issue
number in GitHub markdown format ("GitHub #123: Updates to Catalan
translation").  As an alternative, you can refer to an issue in the same
way in a comment on the commit (this is usually just to correct mistakes in
the commit message without rewriting history).  If you don't do either of
these, commit reporting (-g) won't work.

### Scrum workflow

I work with a geographically distributed team so we generally collaborate
using Skype for voice/IM and shared Google Docs spreadsheets for
"artifacts".  Here are the things I use github2csv for and the command
lines I use to do it.

#### Issue sizing

See 'doc/Issue Sizing Template.ods' for the template.  I typically add a
sheet to the workbook once a week or so with newly-added issues.  I run
this report and "Import" the output file into the sheet:

  $ github2csv --unsized -m "Project Backlog Milestone"


#### Sprint planning

Once all my backlog issues are sized I paste them all into a planning
spreadsheet like 'doc/Sprint Planning Template.ods'.  This report finds all
the sized, open issues:

  $ github2csv --sized --labels -m "Project Backlog"

Import that into the sheet.

Our planning process goes like this.

We decide on an Importance by consensus on each ticket and enter it in the
sheet.  This is "Importance for this sprint" so it's not a permanent
feature of the ticket.

The sheet computes a "Priority" which puts larger tickets ahead of smaller
ones but mostly reflects the Importance.  The "Bonus" in the template sheet
also contributes to Priority (by adding points to the Importance).  We give
1 Bonus point for the "bug" label and one Bonus for the "voc" (voice of the
customer) label.  So, for example, if there are two features of the same
Size and Importance, a bug fix will be higher priority than a non-bugfix,
and a ticket that was created based on a user bug report or user feature
request will be higher than one that was not reported by a user.

Sort the sheet by computed Priority to get a first crack at the order in
which tickets get to get on board the sprint.  This is definitely just a
starting point... there is always horse-trading, resource utilization
leveling, and everything else to consider.

Putting a "1" in the "Include?" column adds the ticket's size to the Sprint
Points column.  I click on the header of Sprint Points as we are going to
see how much room we have left from our previously-agreed-upon sprint
velocity.

Once we have picked the tickets for the sprint, I visit each one and move
it to the sprint milestone.

#### Daily standup 

As the sprint starts I create a sheet like the one in
'doc/Sprint Tracking Template.ods'  The burndown chart is probably too
dumb but you get the idea.

Before the standup, I create a new sheet for the day, copy the column
headers from the previous day, and import:

 $ github2csv --daily --git-commits --milestone "Sprint milestone"

To start, I usually sort by Size, then Working, then Done.  I work from
this sheet during the standup, filling the cell backgrounds with red,
green, yellow, or other descriptive color if I have made changes during the
meeting.

After the standup I manually enter the "Open points" and "Not-done points"
for the day into the Burndown tab.  

#### Sprint post-mortem

The Review sheet in the tracking workbook is the focus of the post-mortem.
I populate it using the "review2csv" tool.  review2csv needs on its command
line EVERY SINGLE daily tracking CSV, in order, with the string "none" for
weekend days or days that you have no tracking CSV.   You give it the start
date as well.  

At the end of the sprint, we review the actual days worked against the
initial sizing, with consideration given for multiple opens and
multitasking.  We end up with a green, yellow, or red assessment for each
ticket.  Just discussion works fine with my team, but YMMV -- a Gantt-type
timeline tool would be helpful in measuring multitasking.


