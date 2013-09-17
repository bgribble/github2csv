#! /usr/bin/env python

import github3 
import argparse
import ConfigParser 
import csv
import os

sizes = {} 

def define_sizes(size_config): 
    if not size_config:
        size_config = "XS: 1, S: 3, M: 7, L: 15, XL: 25, XXL: 1000"

    for s_pair in size_config.split(","):
        if ':' in s_pair:
            s_label, s_val = s_pair.split(':', 1)
            s_val = float(s_val)
        sizes[s_label.strip()] = s_val    

def label2size(labels):
    for s_label, s_val in sizes.items():
        if s_label in labels: 
            return s_val 

    return None 

def main():
    parser = argparse.ArgumentParser()
    config = ConfigParser.SafeConfigParser() 

    parser.add_argument("-c", "--conffile", default="~/.github2csv", help="Config file name")
    parser.add_argument("-r", "--repo", action="append", help="Repository name (as 'owner/repo')")

    parser.add_argument("-u", "--user", help="GitHub username")
    parser.add_argument("-p", "--password", help="GitHub password")
    parser.add_argument("-m", "--milestone", default=None, help="GitHub milestone")
    parser.add_argument("-n", "--unsized", action="store_true", help="Get unsized open issues")
    parser.add_argument("-s", "--sized", action="store_true", help="Get sized open issues")
    parser.add_argument("-l", "--labels", action="store_true", help="Get labels too")
    parser.add_argument("-o", "--outfile", default="gitoutput.csv", help="CSV file to write")
    parser.add_argument("-d", "--daily", action="store_true", help="Daily activity report")
    parser.add_argument("-a", "--all", action="store_true", help="Get open and closed tickets")

    args = vars(parser.parse_args())

    conffile = os.path.expanduser(args.get("conffile"))
    try: 
        config.read(conffile)
    except ConfigParser.Error, e:
        print "Error parsing config file", conffile 
        print e 

    def cfile_get(option): 
        try: 
            return config.get("github2csv", option)
        except Exception, e:
            print "Error getting option", option
            print e 
            return None 

    user = args.get("user") or cfile_get("user")
    password = args.get("password") or cfile_get("password")
    print ":args:", args.get("repo")
    print ":cfile:", cfile_get("repo")
    repos = args.get("repo") or (cfile_get("repo") or '').split(",")
    sizes = args.get("sizes") or cfile_get("sizes")
    do_unsized = args.get("unsized")
    do_sized = args.get("sized")
    do_daily = args.get("daily")
    do_labels = args.get("labels")
    do_all = args.get("all")
    milestone = args.get("milestone") or cfile_get("milestone")
    outfile = args.get("outfile") or cfile_get("outfile")

    define_sizes(sizes)

    gh = github3.login(user, password)

    with open(outfile, "w+") as csvfile:
        for fullrepo in repos: 
            if "/" not in fullrepo: 
                print "Bad repository spec '%s' -- use 'owner/reponame' format." % fullrepo
                continue 
            owner, repo = fullrepo.split("/", 1)
            writer = csv.writer(csvfile, delimiter=',')
           
            mstones = {}
            issue_count = 0

            for m in gh.repository("mayorclayhenry", repo).iter_milestones():
                mstones[str(m.title)] = m.number

            if mstones.get(milestone) is None:
                print "WARNING: did not find milestone '%s' in %s, using *" % (milestone, repo)

            allissues = gh.iter_repo_issues("mayorclayhenry", repo, 
                                            milestone=mstones.get(milestone, "*"), 
                                            state="open")
            if do_all:
                closedissues = gh.iter_repo_issues("mayorclayhenry", repo, 
                                                   milestone=mstones.get(milestone, "*"), 
                                                   state="closed")
                allissues = [ i for i in allissues ] + [ i for i in closedissues ]

            for issue in allissues:
                issue_sized = False 

                for l in issue.labels:
                    if l.name in (u"XS", u"S", u"M", u"L", u"XL", u"XXL"):
                        issue_sized = True 

                i = [ repo, issue.number, 
                     "https://www.github.com/mayorclayhenry/%s/issues/%d" %
                     (repo, issue.number),
                     issue.title ]
                labels = [ l.name for l in issue.labels ] 
                i.append(label2size(labels))

                if do_daily: 
                    i.append(1 if "working" in labels else '')
                    i.append(1 if "done" in labels else '')

                    if "working" in labels: 
                        labels.remove("working")
                    if "done" in labels:
                        labels.remove("done")
                    i.append(','.join(labels))
                    issue_count += 1
                    writer.writerow(i)

                else:
                    if do_labels:
                        i.append(','.join([l.name for l in issue.labels]))
                    if (do_sized and issue_sized) or (do_unsized and not issue_sized): 
                        issue_count += 1
                        writer.writerow(i) 
            print "Found %d issues in repo %s" % (issue_count, repo)

main()


