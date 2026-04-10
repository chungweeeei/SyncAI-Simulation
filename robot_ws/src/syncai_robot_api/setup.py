import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'syncai_robot_api'

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
        'fastapi',
        'uvicorn',
        'temporalio',
    ],
    zip_safe=True,
    maintainer='syncrobotic',
    maintainer_email='chungweeeei@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'syncai_robot_api = syncai_robot_api.main:main',
            'test_bridge_cmd = syncai_robot_api.subscribers.test_bridge_cmd:main',
        ],
    },
)
