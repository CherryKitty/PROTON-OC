from typing import Union, List
import click
from model import ProtonOC
import os
from xml.dom import minidom
from collections import Counter
import multiprocessing
import json

#todo: aggiungere parametro per salvare dati
#todo: aggiungere parametro per salvare lo stato di un tick
#todo: qui init deve avere i seguenti attributi: name, save_path, save_state (tick)

class BaseMode:
    """
    Base mode class
    """
    def __init__(self, name: Union[str, None], save_path: Union[str, bool],
                 snapshot: Union[str, None]):
        if snapshot is not None:
            self.save_path = snapshot
            self.snapshot_active = True
            self.collect = False
        else:   
            self.save_path: Union[str, bool] = save_path
            self.collect = True
            self.snapshot_active = False
        self.name: str = name

    def run(self) -> None:
        """
        Simple run function
        :return: None
        """

        self._single_run(None, self.save_path , self.name)
        click.echo(click.style("Done!", fg="red"))

    def _single_run(self, source_file: Union[str, None], save_dir: str, name: str,
                    verbose =True) -> None:
        """
        This instantiates a model, performs a parameter override (if necessary),
        runs a simulation, and saves the data.
        :param loc_xml: if it is a valid string it performs a parameter override from an xml file
        :param save_dir: directory where the results are saved
        :param name: run name
        :return: None
        """
        model = ProtonOC(collect=self.collect)
        if self.snapshot_active:
            model.init_snapshot_state(name=name, path=self.save_path)
        model.override(source_file)
        model.run(verbose=verbose)
        if self.collect:
            model.save_data(save_dir=save_dir, name=name)


class XmlMode(BaseMode):
    """
    Xml mode class
    """
    def __init__(self,
                 source_path: str,
                 save_path: str,
                 parallel: bool,
                 snapshot: Union[str, bool],
                 filetype: str = ".xml") -> None:

        super().__init__(name=None, save_path=save_path, snapshot=snapshot)
        self.files = list()
        self.parallel = parallel
        self.source_path = source_path
        self.filetype = filetype
        self.detect_file(self.filetype)
        click.echo(click.style("Saving data in: " + self.save_path, bold=True, fg="red"))
        self.filenames = self.get_file_names(self.files)

    def detect_file(self, filetype):
        if os.path.isfile(self.source_path):
            if os.path.splitext(self.source_path)[1] == filetype:
                runs = self.read_repetitions(self.source_path)
                self.setup_repetitions(self.source_path, runs)
            else:
                click.ClickException(
                    click.style("{} is not a valid {} file".format(self.source_path, filetype),
                                fg="red"))
        else:
            for filename in os.scandir(self.source_path):
                if filename.path.endswith(filetype):
                    runs = self.read_repetitions(filename.path)
                    self.setup_repetitions(filename.path, runs)

    def setup_repetitions(self, path, runs):
        for repetition in range(runs):
            self.files.append(path)
        click.echo(click.style(str(runs) + " runs -> " + os.path.basename(
            path), fg="blue"))

    def run(self) -> None:
        """
        Performs multiple runs
        :return: None
        """
        cmd = click.prompt(click.style("\nConfirm [y/n]", fg="red", blink=True, bold=True),
                           type=str)
        if cmd == "y":
            if self.parallel:
                self.run_parallel()
            else:
                self.run_sequential()
            click.echo(click.style("Done!", fg="red"))
        else:
            click.echo(click.style("\nAborted!", fg="red"))


    def read_repetitions(self, source: str) -> int:
        """
        Given an xml file path extracts and returns the number of runs.
        :param xml: str, a valid xml file path
        :return: int, the number of runs
        """
        return int(minidom.parse(source).getElementsByTagName('experiment')[0].attributes[
                       'repetitions'].value)

    def get_file_names(self, files: List[str]) -> List[str]:
        """
        Given a list of xml files extracts the filename and return a list.
        :param files: a list of valid xml file paths
        :return: List, a list of filenames
        """
        rep = Counter(files)
        names = list()
        for key in rep:
            for value in range(rep[key]):
                names.append(os.path.basename(key)[:-4] + "_run_" + str(value + 1))
        return names

    def run_parallel(self) -> None:
        """
        Based on the self.files attribute runs multiple parallel simulations and saves the results.
        :return: None
        """
        processes = list()
        for file, name in zip(self.files, self.filenames):
            p = multiprocessing.Process(target=self._single_run,
                                        args=(file,
                                              self.save_path,
                                              name,
                                              False))
            processes.append(p)
            p.start()
        for process in processes:
            process.join()

    def run_sequential(self):
        """
        Based on the self.files attribute runs multiple sequential simulations and saves the
        results
        :return: None
        """
        for file, name in zip(self.files, self.filenames):
            self._single_run(file, self.save_path, name, True)

class JsonMode(XmlMode):
    def __init__(self, source_path: str, save_path: str, 
                 parallel: bool, snapshot: Union[str, bool]) -> None:
        super().__init__(source_path=source_path, save_path=save_path, parallel=parallel,
                         filetype=".json", snapshot=snapshot)

    def read_repetitions(self, source: str) -> int:
        """
        Given an xml file path extracts and returns the number of runs.
        :param xml: str, a valid xml file path
        :return: int, the number of runs
        """
        with open(source) as json_file:
            data = json.load(json_file)
            if "repetitions" in data:
                return data["repetitions"]
            else:
                return 1

