from setuptools import setup, find_packages

setup(
    name='pylocres',  # Package name
    version='0.1.0',  # Initial version
    author='stas961111',
    author_email='stas96111@gmail.com',
    description='Python library for working with Unreal Engine .locres translation files.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/stas96111/pylocres',  # Replace with your repo
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)