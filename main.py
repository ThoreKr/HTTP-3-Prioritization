import argparse
import json
import logging
import os
import tempfile
import time
import traceback
from time import sleep

from browsertime.browsertime import browsertime
from setup.setup import cleanup, cleanup_processes, set_bottleneck, setup
from setup.utils import LoggingHelper

timestr = time.strftime("%Y%m%d-%Hh%Mm%Ss")

def retrieveh2prio(args, path, firefox=False):
    try:
        chromeperf_content = None
        logfile_content = None
        servers = []

        servers = setup(args.namespace, args.workdir, path, None, True, only_h2 = True)
        set_bottleneck(args.namespace, bw=10, rtt=100, bdp=1)

        selected_server = None
        for server in servers:
            additional = server.get_additionalargs()
            if additional:
                hostnames = additional["hostnames"]
                if args.website in hostnames:
                    selected_server = server
                    break

        assert selected_server is not None, "domain not found in started servers"


        bt = browsertime(args.namespace, args.website, only_h2=True, firefox=firefox)
        bt.start()
        if firefox:
            logging.info("browsertime (firefox) started")
        else:
            logging.info("browsertime (chromium) started")
        while bt.is_running():
            sleep(1)
        if not firefox:
            chromeperf_content = bt.get("chromeCDPlog-1.json.gz")
        logfile_content = selected_server.get("access.log")
        errlogfile_content = selected_server.get("error.log")

    except BaseException as e:
        for op in servers:
            op.willbekilled()
        logging.info("main received %s" % repr(e))
        traceback.print_exc()
    finally:
        for op in servers:
            op.willbekilled()
        cleanup(args.namespace)

    if logfile_content:
        return (logfile_content, errlogfile_content, chromeperf_content)

    return (None, None, None)

def main(path):
    parser = argparse.ArgumentParser()

    parser.add_argument('namespace')

    parser.add_argument('--workdir')
    parser.add_argument('--website')
    parser.add_argument('--h2prioout')
    parser.add_argument('--n')

    parser.add_argument('--eval')
    parser.add_argument('--skip')

    args = parser.parse_args()

    loghelp = LoggingHelper(timestr, args.namespace)

    if args.h2prioout:
        loghandler = logging.FileHandler(args.h2prioout + ".log")
        loghelp.addHandler(loghandler)
        out = []
        n = 30
        if args.n is not None:
            n  = int(args.n)
        for i in range(n):
            chromelog, chromeerrorlog, chromeperf = retrieveh2prio(args, path)
            firefoxlog, firefoxerrorlog, _ = retrieveh2prio(args, path, firefox=True)


            out.append({"firefoxlog": firefoxlog, "chromelog": chromelog, "chromeperf": chromeperf, "chromeerrorlog": chromeerrorlog, "firefoxerrorlog": firefoxerrorlog})

        with open(args.h2prioout,"w") as f:
            json.dump(out, f)

    elif args.eval is not None:

        configs = []
        with open(args.eval) as f:
            for line in f:
                configs.append(json.loads(line))

        general = configs[0]["general"]
        configs = configs[1:]

        outputdir = general["dir"]
        repetitions = general["repeat"]
        skip = 0
        to_skip = int(args.skip) if args.skip is not None else 0
        no = 0

        for repeat in range(repetitions):
            for configno, config in enumerate(configs):
                if skip < to_skip:
                    skip += 1
                    continue
                no += 1
                logging.info("run %d"%no)
                rundir = "%s/%s/repeat-%d/%d/" % (outputdir, timestr, repeat, configno)
                os.makedirs(rundir)
                logfile = open(rundir + "run.log","w")
                loghandler = logging.StreamHandler(logfile)
                loghelp.addHandler(loghandler)

                with open(rundir + "config.json","w") as f:
                    json.dump(config, f)

                servers = []

                cc=config["cc"]

                if not "bwup" in config:
                    config["bwup"] = config["bwdown"]

                try:
                    servers = setup(args.namespace, config["workdir"], path, allsameip=True, prioritization={"mode":config["priomode"],"file":config["priofile"]},cc=cc,only_h2=False)
                    set_bottleneck(args.namespace, config["bwdown"], config["rtt"], config["bdp"], bwup=config["bwup"], loss=config["loss"])
                    logging.info("wait for 5 seconds")
                    sleep(5)

                    timeout = 300
                    if config["bwdown"] < 2:
                        timeout = 900

                    bt = browsertime(args.namespace, config["website"], timeout=timeout)
                    bt.start()
                    logging.info("browsertime (chrome) started")
                    while bt.is_running():
                        sleep(1)

                    bt.copy_over(rundir + "browsertime")
                    for i, server in enumerate(servers):
                        server.copy_over(rundir + ("server%d" % i))

                    bt.parse("browsertime.json")
                    har = bt.parse("browsertime.har")

                    versions = [entry["request"]["httpVersion"] for entry in har["log"]["entries"]]
                    assert (set(versions) == {"h3"}), set(versions)

                except BaseException as e:
                    for op in servers:
                        op.willbekilled()
                    logging.info("main received %s" % repr(e))
                    traceback.print_exc()
                finally:
                    for op in servers:
                        op.willbekilled()
                    cleanup_processes(args.namespace)

                loghelp.removeHandler(loghandler)
                logfile.close()
    else:
        assert False


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmpdir:
        main(tmpdir)
    exit(0)
