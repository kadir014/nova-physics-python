import nova


# Create an empty simulation space
space = nova.Space()

# Let's create a ground body with rectangle collider shape
# Since this will be the ground, make the type STATIC
ground = nova.RigidBody(
    type=nova.RigidBodyType.STATIC,
    position=nova.Vector2(0.0, 20.0),
)

# Let's assign a 10x1 unit rectangle shape
ground_shape = nova.ShapeFactory.box(10.0, 1.0)
ground.add_shape(ground_shape)

space.add_rigidbody(ground)


# Now let's create a bouncy ball that is going to fall and bounce on the ground
# Position is at origin (0, 0) by default
ball = nova.RigidBody(
    type=nova.RigidBodyType.DYNAMIC,
    material=nova.Material(restitution=0.9) # High restitution so it can bounce
)

# Let's assign a 1 unit radius circle shape
ball.add_shape(nova.ShapeFactory.circle(1.0))

space.add_rigidbody(ball)


# The scene is all set up. Now we only have to simulate it!

# This is the time step length the engine going to simulate the space in.
dt = 1.0 / 60.0

# Let's simulate for 3 seconds.
duration = 3.0

t = 0 # Current time
while t < duration:
    print(
        f"Ball is at {ball.position} with velocity {ball.linear_velocity} at time {round(t, 2)}"
    )

    # Advance the simulation
    space.step(dt)

    t += dt