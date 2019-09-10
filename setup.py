from setuptools import setup

setup(
    name='squarely',
    version='1.0',
    packages=['squarely'],
    include_package_data=True,
    url='https://github.com/nwg-piotr/squarely',
    license='GPL3',
    author='Piotr Miller',
    author_email='nwg.piotr@gmail.com',
    description='Puzzle game written in Python using the pyglet library',
    install_requires=['pyglet', 'requests']
)
