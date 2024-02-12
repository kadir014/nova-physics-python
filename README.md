# Python binding for [Nova Physics Engine](https://github.com/kadir014/nova-physics)

This binding aims to provide a Pythonic API while keeping everything as similar as to the original.



# Installation
The module is not on PyPI yet, you have to build it on your own using:
```
python setup.py build
```
It will automatically download the latest Nova Physics release.



# Usage
```py
import nova

# Create the space instance
space = nova.Space()

# Create a rigid body with box shape
body = nova.create_rect(
    nova.DYNAMIC, # Type of the body
    0.0, 0.0,     # Initial position
    0.0,          # Initial rotation
    1.0,          # Density
    0.1,          # Restitution
    0.35,         # Friction
    5, 5          # Width & height of the rect shape
)

# Add body to the space
space.add(body)

# Main loop
while True:
    # Advance the simulation with the timestep of 60 times a second.
    space.step(
        1 / 60, # Timestep (delta time)
        10, # Velocity iterations
        10, # Position iterations
        5,  # Constraint iterations
        1   # Substeps
    )
```



# Requirements
- [Python](https://www.python.org/downloads/) (3.9+)
- [Setuptools](https://pypi.org/project/setuptools/)



# License
[MIT](LICENSE) © Kadir Aksoy