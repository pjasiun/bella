import os, re

class Formatter():
	code_parts = []

	def arrange( self, content, isHtml ):
		if isHtml:
			self.code_parts = [ HtmlPart( content ) ]
		else:
			self.code_parts = [ JsPart( content ) ]

		# TODO: split html part to html and js

		for part in self.code_parts:
			part.arrange()

		return ''.join( part.code for part in self.code_parts )

class HtmlPart():
	def __init__( self, code ):
		self.code = code

	def arrange( self ):
		pass

class JsPart():
	def __init__( self, code ):
		self.code = code
		self.saved_fragments = {}

	def arrange( self ):
		code = self.code

		# Replace lines longer then 500 characters with placeholders
		code = self.ignore_long_lines( code, 500 )

		# Replace string, comments and regular expressions with placeholders
		code = self.ignore_not_code_parts( code )

		# Do formatting.
		code = self.transform( code )

		# Restore placeholders.
		code = self.restore_placeholders( code )

		# Remove whitespace from the end of the line
		code = re.sub( r'[ \t\r\f\v]+\n', r'\n', code )

		self.code = code

	def ignore_long_lines( self, code, length ):
		lines = code.split( '\n' )

		for i, line in enumerate( lines ):
			if len( line ) > length:
				lines[ i ] = self.generate_placehoder( line, 'l' )

		return '\n'.join( lines )

	def ignore_not_code_parts( self, code ):
		index = 0

		# Scan file looking for beggings of strings (', ") comment or regexps (/).
		while index < len( code ):
			# Strings using '
			if code[ index ] == '\'':
				end = self.find_end_possition( code[ index: ], r'([^\\]\')', True )
				code = self.replace_by_placehoder( code, index, index + end, 's' )

			# Strings using '
			if code[ index ] == '`':
				end = self.find_end_possition( code[ index: ], r'([^\\]`)', True )
				code = self.replace_by_placehoder( code, index, index + end, 's' )

			# Strings using "
			if code[ index ] == '\"':
				end = self.find_end_possition( code[ index: ], r'([^\\]\")', True )
				code = self.replace_by_placehoder( code, index, index + end, 's' )

			# Comment, regexp or just division, we need to check it.
			if code[ index ] == '/':
				# Block comment.
				if code[ index + 1 ] == '*':
					end = self.find_end_possition( code[ index: ], r'(\*\/)', False )
					code = self.replace_by_placehoder( code, index, index + end, 'c' )

				# Line comment.
				elif code[ index + 1 ] == '/':
					end = self.find_end_possition( code[ index: ], False, True )
					code = self.replace_by_placehoder( code, index, index + end, 'c' )

				# Regexp.
				elif self.is_regexp_begginig( code, index ):
					end = self.find_end_possition( code[ index: ], r'([^\\]\/)', True )
					code = self.replace_by_placehoder( code, index, index + end, 'r' )

			index += 1

		return code

	# Check if it is begging of the regular expression. Move cursor to the back, skip all
	# white spaces and comments (they are already replace but placehoder) and check if
	# the first valid character before / is ":", ",", "=" or "(". We do not need to check if
	# current character is "/" because we checked it already in ignore_not_code_parts.
	def is_regexp_begginig( self, code, index ):
		while index > 0:
			index -= 1

			# This could be a placehoder so it could be comment.
			if code[ index ] == '|':
				try:
					token = re.finditer( r'\|BellaToken\d+.\|$', code[ : index + 1 ] ).__next__()
					if code[ token.end() - 2 ] != 'c':
						# If it is not a comment this is not regexp.
						return False
					else:
						# Move index to the back of the length of placeholder.
						index -= len( code[ token.start() : token.end() ] )

				except StopIteration:
					# If it is just '|', not a placeholder it is not regxep.
					return False

			# If it is not a whitespace check if it is ":", ",", "=" or "(".
			# If so this is the begging of the regexp, otherwise it is not.
			if code[ index ].isspace() == False:
				return ':,=(['.find( code[ index ] ) >= 0

		return False

	# Find where is the end of comment, string or regexp.
	# This function returns minimum position of:
	# - the end of the regex (if regex is defined),
	# - end of the line (if endline is True),
	# - end of the document.
	def find_end_possition(self, code, regex, endline):
		doc_end_pos = len( code )
		regex_pos = doc_end_pos
		endline_pos = doc_end_pos

		# Get the position of the end of regexp.
		if regex:
			try:
				regex_pos = re.finditer( regex, code ).__next__().end()
			except StopIteration:
				pass

		# Get the position of the end of line.
		if endline:
		 endline_pos = code.find( '\n' )

		if endline_pos < 0:
			endline_pos = doc_end_pos

		# Find minimum.
		return min( regex_pos, endline_pos, doc_end_pos )

	# Replace part of the code between start and end with placeholder and save replaces content.
	def replace_by_placehoder( self, code, start, end, type ):
		return ''.join( ( code[ :start ], self.generate_placehoder( code[ start:end ], type ), code[ end:len( code ) ] ) )

	# Save content and create placeholder.
	def generate_placehoder( self, code_to_replace, type ):
		id = len( self.saved_fragments )
		self.saved_fragments[ id ] = code_to_replace
		return '|BellaToken%i%s|'% ( id, type )

	# Restore placeholder with content do it recurrently because one placeholder can contains other.
	def restore_placeholders( self, code ):
		while len( self.saved_fragments ) > 0:
			index = 0
			result = ''

			for mo in re.finditer( r'\|BellaToken\d+.\|', code ):
				if index != mo.start():
					result += code[ index:mo.start() ]
				id = int( code[ mo.start() + 11 :mo.end() - 2 ] ) # 11 = '|BellaToken'
				result += self.saved_fragments.pop( id )
				index = mo.end()

			if index < len( code ):
				result += code[ index:len( code ) ]

			code = result

		return code

	# Do code formatting.
	def transform( self, code ):
		# Handle spaces around( and )
		code = re.sub( r'([0-9a-zA-Z_$]) \(', r'\1(', code ) #)'
		code = re.sub( r'\((\S)', r'( \1', code ) #)'
		code = re.sub( r'(\S)\)', r'\1 )', code )
		code = re.sub( r'\( \)', r'()', code )
		code = re.sub( r'\)\)', r') )', code )
		code = re.sub( r'\(\(', r'( (', code ) #))'

		# Handle spaces around [ and ]
		code = re.sub( r'\[(\S)', r'[ \1', code ) # ]'
		code = re.sub( r'(\S)\]', r'\1 ]', code )
		code = re.sub( r'\[ \]', r'[]', code )
		code = re.sub( r'\]\]', r'] ]', code )
		code = re.sub( r'\[\[', r'[ [', code ) # ]]'

		# Handle spaces around { and }
		code = re.sub( r'(\S)\{', r'\1 {', code )
		code = re.sub( r'\{(\S)', r'{ \1', code )
		code = re.sub( r'(\S)\}', r'\1 }', code )
		code = re.sub( r'\{ \}', r'{}', code )
		code = re.sub( r'\}\}', r'} }', code )
		code = re.sub( r'\{\{', r'{ {', code )

		# Add spaced after keywords
		code = re.sub( r'(if|for|while|with|return|switch|catch)\(', r'\1 (', code ) #'

		# Handle a ternary operator, ex. x:0?1; -> x : 0 ? 1;
		# TODO: true ? { a: 1 } : b
		code = re.sub( r'\n([^\n]*?[^ ])( )?\?( )?([^ \n][^{]?[^ ]) ?: ?', r'\n\1 ? \4 : ', code )

		# Add spaces after comas, ex. 'a','b' -> 'a', 'b'
		code = re.sub( r',(\S)', r', \1', code )

		# Add spaces after colons, ex. 'a':'b' -> 'a': 'b'
		code = re.sub( r':(\S.*?:?)', r': \1', code )

		# TODO: empty line before }

		# TODO: change type of brackets for extended to egyptian

		# TODO: remove ',' before "}" (ex. }, } ->  } })

		# Remove spaces after !
		code = re.sub( r'! ', r'!', code )

		return code
