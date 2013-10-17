#! /usr/bin/env python

import github3
import argparse
import ConfigParser
import csv
import os
import re

sizes = {}


def define_sizes(size_config):
    if not size_config:
        size_config = "XS: 1, S: 3, M: 7, L: 15, XL: 25, XXL: 1000"

    for s_pair in size_config.split(","):
        if ':' in s_pair:
            s_label, s_val = s_pair.split(':', 1)
            s_label = unicode(s_label)
            s_val = float(s_val)
        sizes[s_label.strip()] = s_val


def label2size(labels):
    for s_label, s_val in sizes.items():
        if s_label in labels:
            return s_val

    return 0


def main():
    parser = argparse.ArgumentParser()
    config = ConfigParser.SafeConfigParser()

    parser.add_argument("-c", "--conffile", default="~/.github2csv",
                        help="Config file name")
    parser.add_argument("-r", "--repo", action="append",
                        help="Repository name (as 'owner/repo')")

    parser.add_argument("-u", "--user", help="GitHub username")
    parser.add_argument("-p", "--password", help="GitHub password")
    parser.add_argument("-m", "--milestone", default=None, help="GitHub milestone")
    parser.add_argument("-n", "--unsized", action="store_true",
                        help="Get unsized open issues")
    parser.add_argument("-s", "--sized", action="store_true",
                        help="Get sized open issues")
    parser.add_argument("-l", "--labels", action="store_true",
                        help="Get labels too")
    parser.add_argument("-o", "--outfile", default="gitoutput.csv",
                        help="CSV file to write")
    parser.add_argument("-d", "--daily", action="store_true",
                        help="Daily activity report")
    parser.add_argument("-a", "--all", action="store_true",
                        help="Get open and closed tickets")
    parser.add_argument("-g", "--git-commits", action="store_true",
                        help="Get Git commit activity")

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
            return None

    user = args.get("user") or cfile_get("user")
    password = args.get("password") or cfile_get("password")
    repos = args.get("repo") or (cfile_get("repo") or '').split(",")
    size_str = args.get("sizes") or cfile_get("sizes")
    do_unsized = args.get("unsized")
    do_sized = args.get("sized")
    do_daily = args.get("daily")
    do_labels = args.get("labels")
    do_all = args.get("all")
    do_commits = args.get("git_commits")

    milestone = args.get("milestone") or cfile_get("milestone")
    outfile = args.get("outfile") or cfile_get("outfile")
    milestone_date = None

    define_sizes(size_str)

    gh = github3.login(user, password)

    open_points = 0
    closed_points = 0
    notdone_points = 0 
    total_points = 0 
    unsized = [] 

    with open(outfile, "w+") as csvfile:
        for fullrepo in repos:
            if "/" not in fullrepo:
                print "Bad repository spec '%s' -- use 'owner/reponame' format." % fullrepo
                continue
            owner, repo = fullrepo.strip().split("/", 1)
            writer = csv.writer(csvfile, delimiter=',')
            ghrepo = gh.repository(owner, repo)

            mstones = {}
            activity = {}
            issue_count = 0

            print "Looking at milestones in:", fullrepo, owner, repo
            for m in gh.repository(owner, repo).iter_milestones():
                mstones[str(m.title)] = m.number

            if mstones.get(milestone) is None:
                print "WARNING: did not find milestone '%s' in %s, using *" % (milestone, repo)
            else:
                milestone_date = ghrepo.milestone(mstones.get(milestone)).created_at

            openissues = gh.iter_repo_issues(owner, repo,
                                            milestone=mstones.get(milestone, "*"),
                                            state="open")
            closedissues = gh.iter_repo_issues(owner, repo,
                                               milestone=mstones.get(milestone, "*"),
                                               state="closed")
            if do_all:
                allissues = [i for i in openissues] + [i for i in closedissues]
            else:
                allissues = [i for i in openissues]

            if do_commits:
                print "Processing commit activity in", repo, "since", milestone_date

                allcommits = []

                for branch in ghrepo.iter_branches():
                    branchcommits = ghrepo.iter_commits(unicode(branch.commit.sha),
                                                        None, None, -1, None,
                                                        milestone_date)
                    allcommits.extend(branchcommits)

                print "  .. Found %d total commits" % len(allcommits)

                for c in allcommits:
                    if c.commit.message:
                        issues = re.findall("#[0-9]+", c.commit.message)
                    try: 
                        for comment in ghrepo.iter_comments_on_commit(c.commit.sha):
                            issues.extend(re.findall("#[0-9]+", comment.body))
                    except Exception, e: 
                        print " ERROR fetching comments on", c.commit.sha
                        print " ", e

                    for i in issues:
                        committers = activity.setdefault(i[1:], {})
                        if str(c.committer) not in committers:
                            committers[c.committer.login] = 1
                        else: 
                            committers[c.committer.login] += 1

            for issue in allissues:
                issue_sized = False

                for l in issue.labels:
                    if l.name in sizes:
                        issue_sized = True

                i = [repo, issue.number,
                     "https://www.github.com/%s/%s/issues/%d" %
                     (owner, repo, issue.number),
                     issue.title]
                labels = [l.name for l in issue.labels]
                isize = label2size(labels) 
                i.append(isize)

                if isize == 0:
                    unsized.append((repo, issue.number))


                if do_daily:
                    total_points += isize 
                    open_points += isize 

                    i.append(1 if "working" in labels else '')
                    i.append(1 if "done" in labels else '')

                    if "working" in labels:
                        labels.remove("working")

                    if "done" in labels:
                        labels.remove("done")
                    else: 
                        notdone_points += isize 

                    if do_commits:
                        committers = activity.get(unicode(issue.number), {})
                        i.append(','.join(['%s: %s' % (n, count) 
                                           for n, count in committers.items()]))

                    i.append(','.join(labels))
                    issue_count += 1
                    writer.writerow(i)

                else:
                    if do_commits:
                        committers = activity.get(unicode(issue.number), [])
                        i.append(','.join(committers))

                    if do_labels:
                        i.append(','.join([l.name for l in issue.labels]))

                    if (do_sized and issue_sized) or (do_unsized and not issue_sized):
                        issue_count += 1
                        writer.writerow(i)

            for issue in closedissues: 
                labels = [l.name for l in issue.labels]
                isize = label2size(labels) 
                closed_points += isize 
                total_points += isize 

            print "Found %d issues in repo %s" % (issue_count, repo)


    if do_daily:
        if len(unsized):
            print "Open issues with no size set: "
            for i in unsized:
                print "%s #%s" % i

        print ("Point totals: %s open, %s not-done, %s closed, %s total" 
               % (open_points, notdone_points, closed_points, total_points))

