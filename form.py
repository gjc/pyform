# vim: ts=3:sw=3


import os
import sys
import subprocess

class FormPipe:
	"""
	Implements a Form process.

	"""
	def __init__(self, formfile, formargs=None, executable="form",
			stdin=None, stdout=None, stderr=None, threads=None, prompt=None):
		"""
		Creates a new Form process.

		PARAMETERS:
			formfile   -- the name of the Form file to be run
			executable -- the name of the form executable
			formargs   -- a list of arguments in addition to the form file.
			              Note: the argument '-pipe' should not be given here.
			threads    -- the number of threads; sets the argument '-w' for
			              tform
			stdin      -- redirection of the standard input
			stdout     -- redirection of the standard error output
			stderr     -- redirection of the standard output
			              stdin, stdout and stderr are the same as in
							  subprocess.Popen
			prompt     -- the prompt for the open channel
		"""

		(r1, w1) = os.pipe()
		(r2, w2) = os.pipe()
		self._fds = [r1, w1, r2, w2]

		args = [executable]

		if not (threads is None):
			args.append('-w%d' % threads)

		args.extend(["-pipe", "%d,%d" % (r1, w2)])

		if not (formargs is None):
			args.extend(formargs)
			
		args.append(formfile)

		self._proc = subprocess.Popen(args,
				stdin=stdin, stdout=stdout, stderr=stderr)

		self._in = r2
		self._out = w1
		self._executable = executable
		self._formfile = formfile
		self._pid = os.getpid()
		
		self._formPID = self.readLine().strip('\r\n')
		self.write("%s,%d\n" % (self._formPID, self._pid))
		self._prompt = prompt

	def getpid(self):
		"""
		Returns the process id of the Form process.
		"""
		return self._formPID

	def poll(self):
		"""
		Checks if the underlying process is still running.

		RESULT
			None, unless the process terminated, the return code otherwise
		"""
		return self._proc.poll()

	def getExecutable(self):
		"""
		Returns the name of the Form binary
		"""
		return self._executable

	def getFilename(self):
		"""
		Returns the name of the file which is processed by Form.
		"""
		return self._formfile

	def write(self, str):
		"""
		Writes a string to the process through the communication pipe.
		"""
		os.write(self._out, str)
		return self

	def readLine(self):
		"""
		Reads a line from the process through the communication pipe.
		"""
		s = os.read(self._in, 1)
		result = ""
		while len(s) == 1 and s != "\n":
			result += s
			s = os.read(self._in, 1)
		result += s
		return result

	def read(self, count=1):
		return os.read(self._in, count)

	def close(self):
		"""
		Closes the pipes to the underlying process.

		This method is also called from the destructor, if necessary.
		"""
		for fd in self._fds:
			os.close(fd)
		self._fds = []

	def check_error(self):
		"""
		Check that Form has not failed
		If it does it prints a message
		"""
		while self.poll() is None:
			pass
		if self.poll() != 0:
			print "FORM failed!"

	def listen_until(self, formend):
		"""
		Read a chunk of Form code. Python knows Form 
		has finished because the string that is read in
		is equal to the string = '%s\n' % formend
		"""
		line     =''
		chunk    =''
		stopsign = "%s\n" % formend
		while line != stopsign:
			if line != '\n':
				chunk += line
			line=self.readLine()
		return chunk

	def define_preproc(self, variable, value):
		"""
		Allows one to define a proprocessor variable in the
		underlying Form code

		"""
		self.write("#define %s \"%s\"\n\n" % (variable,value))


	def prompt(self):
		"""
		Prompt (if initialized)
		"""
		if self._prompt:
			self.write("\n%s\n" % self._prompt)
		else:
			self.write("\n\n")
	def talk(self,message):
		"""
		Talk to Form using the prompt (if initialized)
		"""
		if self._prompt:
			letter = "%s\n%s\n" % (message,self._prompt)
		else:
			letter = "%s\n\n" % (message)
		self.write(letter)

	def converse(self,message):
		"""
		Talk to Form without the prompt 
		"""
		letter = "%s\n\n" % (message)
		self.write(letter)


	def __del__(self):
		self.close()

	def __str__(self):
		return "<%s %s; PID=%s>" % (
				self.getExecutable(),
				self.getFilename(),
				self.getpid()
				)

class Expr:
	"""
	Print the underlying form process

	"""
	def __init__(self, expression, definitions ):
		self._defs = definitions
		self._expression  = expression

	def __str__(self):
		return self._expression
	
	def exe(self,command):
		"""
		"""
		pipe=FormPipe("template.frm", prompt="READY", 
				formargs=['-q'])
		pipe.readLine()
		for name, type in self._defs.iteritems():
			pipe.converse('%s %s;\n' % (type,name))
		pipe.prompt()
		pipe.talk('Local exc = %s;\n' % self._expression)
		pipe.talk(command)
		outexpr = pipe.listen_until("OVER")
		pipe.check_error()
		pipe.close()
		self._expression = outexpr.rstrip('\n')
		print self
		return self._expression

if __name__ == '__main__':
	print 'Test program of python front end'
	symboldict = { 'a' : 'I', 'b' : 'I', 'c' : 'I', 'd' : 'I', 
			'Fun' : 'CF', 'sDUMMY1' : 'S'}
	# Declaring an Expr automatically declares the underlying
	# Form process
	trace=Expr('g_(1,a,b,c,d)*Fun(a,b,c,d);',symboldict)
	trace.exe('trace4,1;multiply 10;')



