# Python binding for [Nova Physics Engine](https://github.com/kadir014/nova-physics)

This binding aims to provide a Pythonic API while keeping everything as similar as to the original.



# Installation
```
pip install nova
```



# Usage
```py
import nova

# Create the space
space = nova.Space()

# Create a body with box shape
body = nova.Rect(
    nova.DYNAMIC,      # Type of the body
    nova.Vector2(0, 0) # Initial position of the body
    0,                 # Initial rotation of the body
    5, 5               # Width & height of the rect shape
)

# Add body to the space
space.add(body)

# Main loop
while True:
    # Advance the simulation with the timestep of 60 times a second.
    space.step(1 / 60)
```



# Requirements
- [Python](https://www.python.org/downloads/) (3.8+)
- [Nova Physics](https://github.com/kadir014/nova-physics) (Prebuilt in the PyPI release)
- [Setuptools](https://pypi.org/project/setuptools/) (Should be included by default)



# License
[MIT](LICENSE) © Kadir Aksoy