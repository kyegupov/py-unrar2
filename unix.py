# Copyright (c) 2003-2005 Jimmy Retzlaff, 2008 Konstantin Yegupov
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Low level interface - see UnRARDLL\UNRARDLL.TXT

import subprocess
import gc

import os, os.path
import time


class UnpackerNotInstalled(Exception): pass

rar_executable_cached = None

def call_unrar(params):
    "Calls rar/unrar command line executable, returns stdout pipe"
    global rar_executable_cached
    if rar_executable_cached is None:
        for command in ('unrar', 'rar'):
            try:
                subprocess.Popen([command], stdout=subprocess.PIPE)
                rar_executable_cached = command
                break
            except OSError:
                pass
        if rar_executable_cached is None:
            raise UnpackerNotInstalled("No suitable RAR unpacker installed")
            
    assert type(params) == list, "params must be list"
    args = [rar_executable_cached] + params
    try:
        gc.disable() # See http://bugs.python.org/issue1336
        return subprocess.Popen(args, stdout=subprocess.PIPE)
    finally:
        gc.enable()

class RarFileImplementation(object):

    def init(self, password=None):
        self.password = password

        pipe = self.call('v', []).stdout
        accum = []
        source = pipe.readlines().__iter__()
        line = ''
        while not line.startswith('Comment:'):
            line = source.next()
        while not line.startswith('Pathname/Comment'):
            accum.append(line.rstrip('\n'))
            line = source.next()
        accum[0] = accum[0][9:]
        self.comment = '\n'.join(accum[:-1])
                

    def call(self, cmd, options=[], files=[]):
        soptions = ['-'+x for x in options]
        return call_unrar([cmd]+soptions+['--',self.archiveName]+files)

    def infoiter(self):
        pipe = self.call('v', ['c-']).stdout
        accum = []
        source = pipe.readlines().__iter__()
        line = ''
        while not line.startswith('--------------'):
            line = source.next()
        line = source.next()
        i = 0
        while not line.startswith('--------------'):
            accum.append(line)
            if len(accum)==2:
                data = {}
                data['index'] = i
                data['filename'] = accum[0].strip()
                info = accum[1]
                data['size'] = int(info[:22].strip())
                attr = info[53:60]
                data['isdir'] = 'D' in attr
                data['datetime'] = time.strptime(info[37:51], '%d-%m-%y %H:%M')
                data['comment'] = None
                yield data
                accum = []
                i += 1
            line = source.next()

    def read_files(self, checker):
        res = []
        for info in self.infoiter():
            checkres = checker(info)
            if checkres==True and not info.isdir:
                pipe = self.call('p', ['inul'], [info.filename]).stdout
                res.append((info, pipe.read()))
        return res            

          
    def extract(self, checker, path, withSubpath):
        res = []
        command = 'x'
        if not withSubpath:
            command = 'e'
        if not path.endswith(os.sep):
            path += os.sep
        names = []
        for info in self.infoiter():
            checkres = checker(info)
            if type(checkres) in [str, unicode]:
                raise NotImplementedError("Condition callbacks returning strings are deprecated and only supported in Windows")
            if checkres==True and not info.isdir:
                names.append(info.filename)
                res.append(info)
        names.append(path)
        proc = self.call(command, [], names)
        proc.wait()
        return res            
            
    def destruct(self):
        pass

    
