import hashlib
import io
import json
import os
import py7zr
import time
import urllib
from dataclasses import dataclass
from tempfile import TemporaryDirectory

import requests

@dataclass
class DatabaseBuilder():
    source_bundle_url: str
    source_bundle_cruft: str
    db_id: str
    base_files_url: str
    base_files_url_extra: str
    mister_files_base:str

    def get_source_bundle(self):
        self.source_bundle_response = requests.get(self.source_bundle_url)

    @staticmethod
    def get_md5sum(filename: str, chunk_num_blocks: int = 128) -> str:
        md5 = hashlib.md5()
        with open(filename, 'rb') as fh:
            while chunk := fh.read(chunk_num_blocks * md5.block_size): 
                md5.update(chunk)
        return md5.hexdigest()

    def build_metadata(self):
        self.metadata = {
            'db_id': self.db_id,
            'timestamp': int(time.time()),
            'base_files_url': self.base_files_url,
        }

    def build_files(self):
        self.files = {}
        with TemporaryDirectory() as tmp_dir:
            f7z = py7zr.SevenZipFile(io.BytesIO(self.source_bundle_response.content))
            f7z.extractall(path=tmp_dir)
            f7z.close()
            for root, dirs, files in os.walk(tmp_dir):
                for name in files:
                    filename = os.path.join(root, name)
                    formatted_filename = os.path.join(root, name).replace(tmp_dir + os.sep, '').replace(self.source_bundle_cruft + os.sep, '')
                    self.files.update({
                        os.path.join(self.mister_files_base, formatted_filename): {
                            'hash': DatabaseBuilder.get_md5sum(filename),
                            'size': os.path.getsize(filename),
                            'url': self.base_files_url.replace('https://github.com/', 'https://raw.githubusercontent.com/') + urllib.parse.quote(self.base_files_url_extra + formatted_filename),
                            'tags': [],
                            'overwrite': False,
                            'reboot': False,
                        }
                    })

    def build_folders(self):
        self.folders = {
            'games': {},
            'games/PSX': {},
            'games/PSX/mcd': {},
        }
        with TemporaryDirectory() as tmp_dir:
            f7z = py7zr.SevenZipFile(io.BytesIO(self.source_bundle_response.content))
            f7z.extractall(path=tmp_dir)
            f7z.close()
            for root, dirs, files in os.walk(tmp_dir):
                for name in dirs:
                    if name == self.source_bundle_cruft:
                        continue
                    folder_name = os.path.join(root, name).replace(tmp_dir + os.sep, '').replace(self.source_bundle_cruft + os.sep, '')
                    self.folders.update({os.path.join('games/PSX/mcd', folder_name): {}})

    def build_tag_dictionary(self):
        pass

    def build_db_files(self):
        pass

    def build_default_options(self):
        pass

    def build_zips(self):
        pass

    def build_database(self):
        self.get_source_bundle()
        self.build_metadata()
        self.build_files()
        self.build_folders()
        self.build_tag_dictionary()
        self.build_db_files()
        self.build_default_options()
        self.build_zips()

    def compile_database(self) -> dict:
        database = self.metadata
        database.update({
            'files': self.files,
            'folders': self.folders,
        })
        return database

    def output_database(self):
        with open(f'{self.db_id}.json', 'w') as fh:
            json.dump(self.compile_database(), fh, sort_keys=True, indent=4)

    def run(self):
        self.build_database()
        self.output_database()


if __name__ == '__main__':
    database_builder = DatabaseBuilder(
        source_bundle_url='https://github.com/Pezz82/MemCard-Pro-Packs/releases/download/Playstation/Memcard.Pro.Pack.Mister.7z',
        source_bundle_cruft='0.Memory Cards',
        db_id='psx_mcd_db',
        base_files_url='https://github.com/Pezz82/MemCard-Pro-Packs/',
        base_files_url_extra='main/Individual Games/',
        mister_files_base='games/PSX/mcd/',
    )
    database_builder.run()
