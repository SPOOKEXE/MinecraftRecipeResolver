
from __future__ import annotations

import traceback
import zipfile
import os
import tempfile
import time
import re

from typing import Callable
from shutil import rmtree

class ZipExtracts:

	directory : str
	files : list[str]

	def __init__( self, directory : str, files : list[str] ):
		self.directory = directory
		self.files = files

	def __del__(self) -> None:
		try: rmtree(self.directory, ignore_errors=True)
		except: pass

class ZipParser:

	filepath : str
	zipreader : zipfile.ZipFile

	def __init__(self, filepath : str):
		self.filepath = filepath
		self.zipreader = None

	def file_exists( self ) -> bool:
		return type(self.filepath) == str and os.path.exists( self.filepath )

	def open_reader( self ) -> tuple[bool, str]:
		if self.zipreader != None:
			return True, 'Reader is already open.'
		if not self.file_exists():
			return False, 'No such file exists at filepath.'
		try:
			self.zipreader = zipfile.ZipFile(self.filepath, 'r')
			return True, 'Opened a new reader.'
		except Exception as exception:
			return False, traceback.format_exception( exception )

	def close_reader( self ) -> None:
		if self.zipreader != None:
			self.zipreader.close()
			self.zipreader = None

	def extract_files_filter( self, filter : Callable[[zipfile.ZipInfo], bool] ) -> tuple[bool, ZipExtracts | str]:
		success, err = self.open_reader()
		if success == False:
			return False, f'Could not open file for reading: {err}'

		desktop_directory = os.path.expanduser("~/Desktop")
		# temporary_directory = tempfile.gettempdir()

		directory = os.path.join( desktop_directory, 'zip_parser_' + str( time.time_ns() ) )
		print(f'Extracting files from {self.filepath} file to {directory}.')
		os.makedirs(directory, exist_ok=True)
		previous_directory = os.getcwd()
		os.chdir( directory )

		filepaths : list[str] = []
		for item in self.zipreader.infolist():
			if filter(item) == False:
				continue
			# make the file directories
			file_dir, _ = os.path.split( item.filename )
			if file_dir != '': os.makedirs(file_dir, exist_ok=True)
			# extract item to the item directory
			filepath = os.path.join( directory, item.filename )
			filepaths.append(filepath)
			try:
				self.zipreader.extract(item)
				# print('Extracted:', item.filename)
			except Exception as exception:
				print('Failed to extract:', item.filename)
				print(exception)
				break

		os.chdir( previous_directory )
		self.close_reader( )

		return True, ZipExtracts( directory, filepaths )

	def extract_files_of_extension( self, extension : str ) -> tuple[bool, ZipExtracts | str]:
		return self.extract_files_filter(
			lambda item : item.filename.endswith(extension)
		)

	def extract_files_in_paths( self, paths : list[str] ) -> tuple[bool, ZipExtracts | str]:
		def in_path( item : zipfile.ZipInfo ) -> bool:
			for path in paths:
				if len(re.findall( path, item.filename )) != 0:
					return True
			return False
		return self.extract_files_filter( in_path )
