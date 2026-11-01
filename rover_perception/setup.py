from setuptools import find_packages, setup

package_name = 'rover_perception'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Kritagya Sharma',
    maintainer_email='kritagya2005@gmail.com',
    description='ROS 2 YOLO/OpenCV rover perception pipeline.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'webcam_detector = rover_perception.webcam_detector:main',
        ],
    },
)
