import datetime
import json
import shutil
import subprocess
import time
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

path = Path('mm') / 'record'
general_config = {"general": {"repeat": 1, "dir": "output"}}
site_config_template = {
    "bwdown": 15,
    "rtt": 40,
    "bdp": 1,
    "loss": 0.0,
    "cc": "cubic",
    "priomode": "rrtree",
    "website": "www.columbia.edu",
    "workdir": "mm/record/www.columbia.edu/",
    "priofile": "mm/priorities/www.columbia.edu.csv"}

result_dir = Path('results')
result_dir.mkdir(exist_ok=True)


def check_resultfile(outdir: Path):
    for subdir in outdir.glob('*'):
        print(subdir.name)
        browsertime_path: Path = subdir / 'repeat-0' / '0' / 'browsertime'

        har = browsertime_path / 'browsertime.har'
        json = browsertime_path / 'browsertime.json'
        return har.exists() and json.exists()


def track_times(start_time: float, website: str, repeat: int):
    time_tracker = result_dir / 'times.json'
    if time_tracker.exists():
        with time_tracker.open('r') as trackfile:
            tracker: dict = json.load(trackfile)
    else:
        tracker = dict()

    tracker.setdefault(website, dict())[repeat] = time.time() - start_time

    with time_tracker.open('w') as trackfile:
        json.dump(tracker, trackfile)


for website in path.glob('*'):
    for repeat in range(30):
        start_time = time.time()
        print(f'{website.name} - {repeat}')
        site_results = result_dir / website.name / str(repeat)
        if site_results.exists():
            continue
        site_results.mkdir(exist_ok=True, parents=True)

        site_config = site_config_template.copy()

        site_config['website'] = website.name
        site_config['workdir'] = website.as_posix()

        with TemporaryDirectory() as tmp:
            dirpath = Path(tmp)
            outdir = dirpath / 'out'
            outdir.mkdir()
            general_config['general']['dir'] = outdir.as_posix()

            evalconfig = dirpath / 'evalconfig.json'
            with evalconfig.open('w') as f:
                f.write(json.dumps(general_config))
                f.write('\n')
                f.write(json.dumps(site_config))

            simulator_command = ['python3', 'main.py', f'--eval={evalconfig.as_posix()}', 'disp']

            proc = subprocess.Popen(simulator_command, stdin=subprocess.PIPE, encoding="ascii")

            while not check_resultfile(outdir):
                time.sleep(5)

            proc.kill()

            for subdir in outdir.glob('*'):
                browsertime_path = subdir / 'repeat-0' / '0' / 'browsertime'
                print(browsertime_path.as_posix())
                shutil.copytree(browsertime_path.as_posix(), site_results, dirs_exist_ok=True)

            # Ensure netns is deconstructed
            time.sleep(5)
            subprocess.run('/usr/bin/ip -all netns delete', shell=True)
            # netns = Path('/var/run/netns/')
            # for ns in ['disp-client', 'disp-ns3', 'disp-ns2', 'disp-ns1', 'disp-ns0', 'disp-servers', 'disp-browsertime']:
            #     nsp = netns / ns
            #     if nsp.exists():

        track_times(start_time, website.name, repeat)
