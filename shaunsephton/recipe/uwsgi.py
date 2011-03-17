import os        
import setuptools
import shutil
import sys
import tempfile
from zc.buildout.download import Download
import zc
import zc.recipe.egg

class UWSGI:
    """
    Buildout recipe downloading, compiling and configuring python paths for uWSGI.
    """

    def __init__(self, buildout, name, options):
        self.egg = zc.recipe.egg.Egg(buildout, options['recipe'], options)
        self.name = name
        self.buildout = buildout
        
        if 'extra-paths' in options:
            options['pythonpath'] = options['extra-paths']
        else:
            options.setdefault('extra-paths', options.get('pythonpath', ''))

        # Collect configuration params from options.
        self.conf = {}

        # socket: path (or name) of UNIX/TCP socket to bind to
        self.conf['socket'] = options['socket']

        # harakiri: set harakiri timeout to <sec> seconds
        self.conf['harakiri'] = options.get('harakiri', None)
        # master: enable master process manager
        self.conf['master'] = options.get('master', None)
        # max-requests: maximum number of requests for each worker
        self.conf['max-requests'] = options.get('max-requests', None)
        # module: name of python config module
        self.conf['module'] = options.get('module', None)
        # processes: spawn <n> uwsgi worker processes
        self.conf['processes'] = options.get('processes', None)
        
        self.options = options

    def download_release(self):
        """
        Download uWSGI release based on 'version' option and return path to downloaded file.
        """
        cache = tempfile.mkdtemp('download-cache')
        download = Download(cache=cache)
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

        # Build uWSGI.
        uwsgiconfig = __import__('uwsgiconfig')
        uwsgiconfig = __import__('uwsgiconfig')
        bconf = 'default.ini'
        try:
            bconf = sys.argv[2]
            if not bconf.endswith('.ini'):
                bconf += '.ini'
        except:
            pass
        if not '/' in bconf:
            bconf = 'buildconf/%s' % bconf
        uwsgiconfig.build_uwsgi(uwsgiconfig.uConf(bconf))

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
       
    def get_extra_paths(self):
        """
        Returns extra paths to include for uWSGI.
        TODO: Figure out a more buildouty way to do this.
        """
        parts_path = self.buildout['buildout']['parts-directory']
        parts_paths = [os.path.join(parts_path, part) for part in os.listdir(parts_path)]
        extra_paths = [self.buildout['buildout']['directory'],] + parts_paths

        # Add libraries found by a site .pth files to our extra-paths.
        if 'pth-files' in self.options:
            import site
            for pth_file in self.options['pth-files'].splitlines():
                pth_libs = site.addsitedir(pth_file, set())
                if not pth_libs:
                    self.log.warning(
                        "No site *.pth libraries found for pth_file=%s" % (
                         pth_file,))
                else:
                    self.log.info("Adding *.pth libraries=%s" % pth_libs)
                    self.options['extra-paths'] += '\n' + '\n'.join(pth_libs)

        # Add local extra-paths.
        pythonpath = [p.replace('/', os.path.sep) for p in
                      self.options['extra-paths'].splitlines() if p.strip()]

        extra_paths.extend(pythonpath)
        
        # Add global extra-paths
        buildout_extra_paths = self.buildout['buildout'].get('extra-paths', None)
        if buildout_extra_paths:
            pythonpath = [p.replace('/', os.path.sep) for p in buildout_extra_paths.splitlines() if p.strip()]
            extra_paths.extend(pythonpath)

        return extra_paths
    
    def create_conf_xml(self):
        """
        Create xml file file with which to run uwsgi.
        """
        path = os.path.join(self.buildout['buildout']['directory'], 'uwsgi')
        try:
            os.mkdir(path)
        except OSError:
            pass
       
        xml_path = os.path.join(path, '%s.xml' % self.name)
        
        conf = ""
        for key, value in self.conf.items():
            if value == 'True':
                conf += "<%s/>\n" % key
            elif value and value != 'False':
                conf += "<%s>%s</%s>\n" % (key, value, key)
                
                
        requirements, ws = self.egg.working_set()
        paths = zc.buildout.easy_install._get_path(ws, self.get_extra_paths())
        for path in paths:
            conf += "<pythonpath>%s</pythonpath>\n" % path
        
        f = open(xml_path, 'w')
        f.write("<uwsgi>\n%s</uwsgi>" % conf)
        f.close()

    def install(self):
        if not os.path.exists(os.path.join(self.buildout['buildout']['bin-directory'], 'uwsgi')):
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

        # Create uWSGI conf xml.
        self.create_conf_xml()

        return []

    def update(self):
        return
