import json
import os
import re
from dataclasses import dataclass
from functools import cached_property
from re import Pattern
from typing import AnyStr

import requests
from bs4 import BeautifulSoup


@dataclass
class Config:
    archive_url: str
    base_url: str
    search_string: str
    download_folder: str
    dir_pattern: str

    @cached_property
    def folder_pattern(self) -> Pattern[AnyStr]:
        return re.compile(self.dir_pattern)

    def is_matching_str(self, candidate: str):
        return re.search(self.search_string, candidate, re.IGNORECASE)

    @staticmethod
    def from_json(json_dct):
        return Config(json_dct['archive_url'],
                      json_dct['base_url'], json_dct['search_string'],
                      json_dct['download_folder'], json_dct['dir_pattern'])


@dataclass
class ThreadRef:
    thread_id: str
    excerpt: str
    link: str


def load_config() -> Config:
    f = open('config.json')
    result = json.loads(f.read(), object_hook=Config.from_json)
    f.close()
    return result


def main():
    config: Config = load_config()
    old_ids = existing_ids(config)
    for thread_ref in fetch_threads(config):
        if config.is_matching_str(thread_ref.excerpt):
            if thread_ref.thread_id not in old_ids:
                print(thread_ref.link)


def fetch_threads(config: Config) -> list[ThreadRef]:
    result: list[ThreadRef] = []
    soup = BeautifulSoup(load_html(config.archive_url), 'html.parser')
    tr_list = soup.find("table", attrs={"id": "arc-list"}).findChild("tbody").findChildren("tr")
    for tr_element in tr_list:
        id_element = tr_element.findNext()
        thread_id = str(id_element.text)
        excerpt_element = id_element.next_sibling
        excerpt = str(excerpt_element.text)
        link_element = excerpt_element.next_sibling
        link = link_element.next_element.next_sibling["href"]
        result.append(ThreadRef(thread_id, excerpt, config.base_url + link))
    return result


def load_html(archive_url: str) -> str:
    return requests.get(archive_url).text


def existing_ids(config: Config) -> list[str]:
    result: list[str] = []
    existing_dir_names = dir_names(config.download_folder)
    for name in existing_dir_names:
        match = config.folder_pattern.match(name)
        if match is not None:
            result.append(match.group(1))
    return result


def dir_names(download_folder: str) -> set[str]:
    res = set()
    for file_name in os.listdir(download_folder):
        res.add(file_name)
    return res


if __name__ == '__main__':
    main()
