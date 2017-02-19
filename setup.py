from setuptools import setup

setup(name='gist-vimrc',
      version='0.1',
      description='Package for gist-settings.vim plugin',
      url='http://github.com/yanlobkarev/gist_vimrc',
      author='indirpir',
      author_email='yan.lobkarev@gmail.com',
      license='MIT',
      packages=['gist_vimrc'],
      scripts=['bin/gist_vimrc'],
      install_requires=[
       'python-gist==0.4.7',
      ],
      zip_safe=False)
