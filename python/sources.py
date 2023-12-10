
import os
import json
import traceback
import numpy

from typing import Any
from handler import ZipParser

def array_find( array : list, value : Any ) -> int:
	try: return array.index(value)
	except: return -1

def print_unsupported( index : str, unsupported : dict ) -> None:
	if unsupported.get(index) != None:
		return
	unsupported[index] = True
	print('Unsupported Value:', index)

CRAFTING_TYPES = [
	'minecraft:crafting_shapeless',
	'minecraft:crafting_shaped',
	'minecraft:smelting',
	'minecraft:blasting',
	'minecraft:stonecutting',

	'computercraft:turtle',
	'computercraft:computer_upgrade',
	'computercraft:impostor_shapeless'
]

def handle_recipe( recipes_matrix : dict, data : dict, index : str, unsupported : dict ) -> None:
	SHAPELESS = [
		'minecraft:crafting_shapeless', 'computercraft:impostor_shapeless'
	]
	SHAPED = [
		'minecraft:crafting_shaped', 'computercraft:turtle',
		'computercraft:computer_upgrade', 'computercraft:imposter_shaped'
	]

	if array_find( SHAPELESS, data.get('type')) != -1:
		# print(data)
		resultant_name = data.get('result').get('item')
		resultant_amount = data.get('result').get('count') or 1
		data = [ index, data.get('ingredients'), resultant_amount ]
	elif array_find( SHAPED, data.get('type') ) != -1:
		# print(data)
		resultant_name = data.get('result').get('item')
		resultant_amount = data.get('result').get('count') or 1
		data = [ index, data.get('pattern'), data.get('key'), resultant_amount ]
	elif data.get('type') == 'minecraft:smelting':
		# print(data)
		resultant_name = data.get('result')
		data = [ index, data.get('ingredient'), 1 ]
	elif data.get('type') == 'minecraft:blasting':
		# print(data)
		resultant_name = data.get('result')
		data = [ index, data.get('ingredient'), 1 ]
	elif data.get('type') == 'minecraft:stonecutting':
		# print(data)
		resultant_name = data.get('result')
		resultant_amount = data.get('count') or 1
		data = [ index, data.get('ingredient').get('item'), resultant_amount ]
	else:
		# print_unsupported( data.get('type'), unsupported )
		return

	if recipes_matrix.get(resultant_name) == None:
		recipes_matrix[resultant_name] = [ data ]
	else:
		recipes_matrix[resultant_name].append( data )

class RecipeSourcesMatrix:
	tags : dict = dict()
	recipes : dict = dict()
	unsupported : dict = dict()

class MinecraftJarParser(ZipParser):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def parse_recipes( self, resultant : RecipeSourcesMatrix, files : list[str] ) -> None:
		for filepath in filter(lambda x : x.find('recipes') != -1 and x.endswith('.json'), files):
			with open( filepath, 'r' ) as file:
				jsdata : dict = json.loads( file.read() )
			if jsdata.get('type') == None:
				continue
			if array_find( CRAFTING_TYPES, jsdata.get('type') ) != -1:
				handle_recipe( resultant.recipes, jsdata, jsdata.get('type'), resultant.unsupported )
			# else:
			# 	print_unsupported( jsdata.get('type'), resultant.unsupported )

	def parse_tags( self, resultant : RecipeSourcesMatrix, files : list[str] ) -> None:
		for filepath in filter(lambda x : x.find('tags') != -1 and x.endswith('.json'), files):
			with open( filepath, 'r' ) as file:
				jsdata : dict = json.loads( file.read() )
			tag_name : str = os.path.splitext(os.path.basename(filepath))[0]
			if resultant.tags.get( tag_name ) == None:
				resultant.tags[ tag_name ] = jsdata.get('values')
			else:
				values = resultant.tags[ tag_name ]
				values.extend( jsdata.get('values') )
				resultant.tags[ tag_name ] = numpy.unique(values).tolist()

	def extract_recipe_sources( self ) -> RecipeSourcesMatrix | None:
		success, data = self.extract_files_in_paths([ 'data/(.+)/recipes', 'data/(.+)/loot_tables', 'data/(.+)/tags' ])
		if success == False: return None

		print(data.directory)
		print(len(data.files), 'total files.')

		resultant = RecipeSourcesMatrix( )

		# use to map recipe tag-groups to individual references
		self.parse_tags( resultant, data.files )

		# for each recipe file, parse it if is a whitelisted file
		self.parse_recipes( resultant, data.files )

		return resultant

def extract_sources_from_files( filepaths : list ) -> RecipeSourcesMatrix:
	recipe_sources = RecipeSourcesMatrix()
	for filepath in reversed(filepaths):
		if not os.path.exists(filepath):
			print('File does not exist at filepath, skipping:', filepath)
			continue
		try:
			sources = MinecraftJarParser(filepath).extract_recipe_sources()
			recipe_sources.recipes.update( sources.recipes )
			recipe_sources.unsupported.update( sources.unsupported )
			recipe_sources.tags.update( sources.tags )
		except Exception as exception:
			print('--------------------')
			traceback.print_exception( exception )
			print('--------------------')
	return recipe_sources

if __name__ == '__main__':

	# put important ones first
	resultant = extract_sources_from_files([
		'temp/forge-40.2.0.jar',
		'temp/1.18.2.jar',
		'temp/cc-tweaked-1.18.2-1.101.3.jar',
		'temp/AdvancedPeripherals-1.18.2-0.7.31r.jar',
		'temp/MorePeripherals_1.18.2-1.8.jar',
		'temp/toms-peripherals-1.18.2-1.1.0.jar',
	])

	print('Dumping to file.')
	os.makedirs('mc-src-info', exist_ok=True)
	with open('mc-src-info/recipes.json', 'w') as file:
		file.write(json.dumps(resultant.recipes, indent=4))
	with open('mc-src-info/tags.json', 'w') as file:
		file.write(json.dumps(resultant.tags, indent=4))
	# with open('mc-src-info/unsupported.json', 'w') as file:
	# 	file.write(json.dumps(resultant.unsupported, indent=4))
	print('Completed dumping.')
