import sublime, sublime_plugin, os, re

from .formatter import *
from . import merge_utils

def is_js_context( view ):
	fName = view.file_name()
	syntaxPath = view.settings().get( 'syntax' )
	syntax = ""
	ext = ""

	if ( fName != None ):
		# File exists, pull syntax type from extension.
		ext = os.path.splitext( fName )[ 1 ][ 1: ]

	if ( syntaxPath != None ):
		# Pull syntax type from syntaxPath.
		syntax = os.path.splitext( syntaxPath )[ 0 ].split( '/' )[ -1 ].lower()

	return ext in [ 'js', 'json' ] or "javascript" in syntax or "json" in syntax

def is_html_context( view ):
	fName = view.file_name()
	syntaxPath = view.settings().get( 'syntax' )
	syntax = ""
	ext = ""

	if ( fName != None ):
		# File exists, pull syntax type from extension.
		ext = os.path.splitext( fName )[ 1 ][ 1: ]

	if ( syntaxPath != None ):
		# Pull syntax type from syntaxPath.
		syntax = os.path.splitext( syntaxPath )[ 0 ].split( '/' )[ -1 ].lower()

	return ext in [ 'html', 'htm' ] or "html" in syntax

def is_proper_context( view ):
	return is_js_context( view ) or is_html_context( view )

# Run on save
class PreSaveStylistListner( sublime_plugin.EventListener ):
	def on_pre_save( self, view ):
		settings = sublime.load_settings( "bella.sublime-settings" )

		if ( settings.get( "run_on_save" ) == True and is_proper_context( view ) ):
			view.run_command( "bella_format" )

# Sublime command: bella_format
class bellaFormatCommand( sublime_plugin.TextCommand ):
	def run( self, edit ):
		view = self.view
		region = sublime.Region( 0, view.size() )
		code = view.substr( region )

		# TODO: format only selected content

		# Do code formatting.
		stylist = Formatter()
		formatted_code = stylist.arrange( code, is_html_context( view ) )

		# Merge changes.
		_, err = merge_utils.merge_code( view, edit, code, formatted_code )

		if err:
			sublime.error_message( "bella: Merge failure: '%s'" % err )

	def is_visible( self ):
		return is_proper_context( self.view )

# Sublime command: bella_format_all
class bellaFormatAllCommand( sublime_plugin.TextCommand ):
	def run( self, edit ):
		self.stylist = Formatter()

		# Get project path from config.
		settings = sublime.load_settings( "bella.sublime-settings" )
		project_path = settings.get( "project_path" )

		# Get paths to all files should be formated and format them.
		for path in self.get_filepaths( project_path ):
			self.format_js_files( path )


	def get_filepaths( self, directory ):
		file_paths = []

		# Walk the tree.
		for root, directories, files in os.walk( directory ):
			for filename in files:
				# Join the two strings in order to form the full filepath.
				filepath = os.path.join( root, filename )

				# Add to the list files which should be formatted.
				if self.should_be_formatter( filepath ):
					file_paths.append( filepath )

		return file_paths

	def should_be_formatter( self, path ):
		settings = sublime.load_settings( "bella.sublime-settings" )
		ignore_list = settings.get( "ignore" )

		# Ignore files using pattern from config.
		for pattern in ignore_list:
			if path.find( pattern ) >= 0:
				return False

		# Only js files should be formatted.
		ext = os.path.splitext( path )[ 1 ][ 1: ]
		return ext in [ 'js', 'json' ]


	def format_js_files( self, path ):
		print('Formatting file: \'%s\'' % path)

		# Read.
		with open( path, 'r' ) as hSource:
			code = hSource.read()
		hSource.close()

		# Do formatting.
		formatted_code = self.stylist.arrange( code, False )

		# Write.
		with open( path, 'w' ) as hOutput:
			hOutput.write( formatted_code )
		hOutput.close()
