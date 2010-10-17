import os        
import setuptools
import shutil
import sys
import tempfile
from zc.buildout.download import Download
import zc.recipe.egg

class UWSGI:
    """
    Buildout recipe downloading, compiling and configuring python paths for uWSGI.
    """

    def __init__(self, buildout, name, options):
        self.egg = zc.recipe.egg.Egg(buildout, options['recipe'], options)
        self.name = name
        self.buildout = buildout
        options['download-cache'] = self.buildout['buildout']['download-cache']
        self.options = options

    def download_release(self):
        """
        Download uWSGI release based on 'version' option and return path to downloaded file.
        """
        #cache = self.options['download-cache']
        #download = Download(cache=cache)
        download = Download(self.buildout['buildout'])
        download_path, is_temp = download('http://projects.unbit.it/downloads/uwsgi-latest.tar.gz')
        return download_path
        
    def extract_release(self, download_path):
        """
        Extracts uWSGI package and returns path containing uwsgiconfig.py along with path to extraction root.
        """
        uwsgi_path = None
        extract_path = tempfile.mkdtemp("-uwsgi")
        setuptools.archive_util.unpack_archive(download_path, extract_path)
        for root, dirs, files in os.walk(extract_path):
            if 'uwsgiconfig.py' in files:
                uwsgi_path = root
        return uwsgi_path, extract_path
    
    def build_uwsgi(self, uwsgi_path):
        """
        Build uWSGI and returns path to executable.
        """
        # Change dir to uwsgi_path for compile.
        current_path = os.getcwd()
        os.chdir(uwsgi_path)

        # Add uwsgi_path to the Python path so we can import uwsgiconfig.
        if uwsgi_path not in sys.path:
            sys.path.append(uwsgi_path)
            sys_path_changed = True

        # Get Buildout Python paths.
        requirements, ws = self.egg.working_set(['djangorecipe'])
        paths = [dist.location for dist in ws]

        # Build uWSGI with Buildout Python paths.
        uwsgiconfig = __import__('uwsgiconfig')
        uwsgiconfig.PYLIB_PATH = ','.join(paths)
        uwsgiconfig.parse_vars()
        uwsgiconfig.build_uwsgi('uwsgi')

        # Change back to original path and remove uwsgi_path from Python path if added.
        os.chdir(current_path)
        if sys_path_changed:
            sys.path.remove(uwsgi_path)

        return os.path.join(uwsgi_path, 'uwsgi')

    def copy_uwsgi_to_bin(self, uwsgi_executable_path):
        """
        Copy uWSGI executable to bin and return the resulting path.
        """
        bin_path = os.path.join(self.buildout['buildout']['bin-directory'])
        shutil.copy(uwsgi_executable_path, bin_path)
        uwsgi_path = os.path.join(self.buildout['buildout']['bin-directory'])
        return os.path.join(bin_path, os.path.split(uwsgi_executable_path)[-1])
        
    def install(self):
        # Download uWSGI.
        download_path = self.download_release()

        #Extract uWSGI.
        uwsgi_path, extract_path = self.extract_release(download_path)
        
        # Build uWSGI.
        uwsgi_executable_path = self.build_uwsgi(uwsgi_path)

        # Copy uWSGI to bin.
        uwsgi_bin_path = self.copy_uwsgi_to_bin(uwsgi_executable_path)

        # Remove extracted uWSGI package.
        shutil.rmtree(extract_path)

        return [uwsgi_bin_path,]

    def update(self):
        return
