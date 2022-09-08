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

for website in path.glob('*'):
    print(website.name)
    site_results = result_dir / website.name
    if site_results.exists():
        continue
    site_results.mkdir(exist_ok=True)

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
