import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'syncai_entity_manager'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
         glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='syncrobotic',
    maintainer_email='andy_tseng@syncrobotic.com',
    description='Entity manager for spawning and deleting Gazebo entities via REST API',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'entity_manager_node = syncai_entity_manager.main:main',
        ],
    },
)
