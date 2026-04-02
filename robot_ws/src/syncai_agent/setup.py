import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'syncai_agent'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
    ],
    install_requires=[
        'setuptools',
        'openai',
        'structlog',
    ],
    zip_safe=True,
    maintainer='syncrobotic',
    maintainer_email='chungweeeei@gmail.com',
    description='LLM-powered AI agent ROS 2 node with ROS skills',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'syncai_agent = syncai_agent.main:main',
        ],
    },
)
