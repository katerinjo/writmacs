from setuptools import setup

setup(
        name='writmacs',
        version='0.1',
        description='text formatting macros',
        author='Catherine Stewart',
        license='UNLICENSE',
        packages=['writmacs'],
        include_package_data=True,
        scripts=['bin/writmacs'],
)

