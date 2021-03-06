"""Simple rocket simulator.

We make a few simplifying assumptions about the rocket:
    * The rocket is treated as point with only thrust and gravity acting on it.
    * The rocket is perfectly stable with no horizontal forces acting on it.
    * The rocket is indestructable.
    * The rocket has infinite fuel and therefore its mass does not change as 
      it burns fuel.
    * The rocket is able to apply any percentage of thrust instantaneously and
      with perfect precision.
"""

import time 
import graphics as g
import numpy as np
import tkinter as tk

from controller import OnOffController
from controller import PIDController

TITLE = 'Rockets'
WIDTH = 800 
HEIGHT = 600

FPS = 60
SCALE = 2  # Pixels per meter.

GRAVITY = np.array((0, 9.8))  # In m/s^2.
GROUND_Y = 550  # In pixels.
TARGET_Y = 200  # In pixels.


class Rocket(object):
    """A rocket equipped with a bottom thruster."""

    def __init__(self, 
                 pos, 
                 height=21.2,
                 diameter=1.7,
                 mass=27670., 
                 max_thrust_force=410000.,
                 controller=None):
        """Initializes a new Rocket instance.

        The default arguments correspond to the SpaceX Falcon 1 rocket.
        
        Args:
            pos: The tuple of the initial (x, y) position of the rocket. The 
                position specifies the bottom center of the rocket. For example
                the rocket's tip will be at y + height. 
            height: The height of the rocket. Only affects the rocket's look
                and not the simulation.
            diameter: The diameter of the rocket. Only affects the rocket's 
                look and not the simulation.
            mass: The mass of the rocket in kilograms.
            max_thrust_force: The maximum thrust force at full burn in newtons.
            controller: The `controller.Controller` to use to drive the rocket.
        """
        self._pos = np.array(pos, dtype=np.float32)
        self._vel = np.array((0., 0.))
        self._mass = mass 
        self._thrust_max_force = np.array((0., -max_thrust_force))
        self._thrust_percent = 0
        self._controller = controller
        self._actions = range(0, 11)

        self._height = height
        self._diameter = diameter
        # TODO(eugenhotaj): These below were set arbitrarily. Maybe look up how
        # to set them better?
        self._exhaust_max_height = 12.5
        self._exhaust_width = 1
        self._exhaust_color = "orange"

    def set_thrust(self, percent):
        """Sets the rocket's thrust."""
        assert int(percent * (len(self._actions) - 1)) in self._actions
        self._thrust_percent = percent

    def _sigmoid(self, x):
        return 1 / (1 + np.exp(-x))

    def update(self, dt):
        """Resolve the forces acting on the rocket and update position."""
        if self._controller:
            control_var = self._controller.tick(self._pos[1], dt)
            thrust_percent = round(self._sigmoid(-control_var), 1)
            self.set_thrust(thrust_percent)

        acc = GRAVITY
        if self._thrust_percent:
            thrust_force = self._thrust_max_force * self._thrust_percent
            thrust_acc = thrust_force / self._mass
            acc = acc + thrust_acc 
        self._vel += acc * dt
        self._pos += self._vel * dt

        # TODO(eugenhotaj): Temporary hack for ground collision. Long term, 
        # figure out what the reacting force is and apply to rocket.
        if self._pos[1] >= GROUND_Y:
            # Do not stop the rocket if it is going up.
            self._pos[1] = GROUND_Y
            self._vel[1] = min(0, self._vel[1])
            
    def drawables(self):
        """Returns a list of GraphicsObjects necessary to draw the rocket."""
        # TODO(eugenhotaj): Remove hardcoded SCALE.
        drawables = []
        x, y = self._pos.tolist()
        radius = (self._diameter * SCALE) / 2
        height = self._height * SCALE
        body = g.Polygon(g.Point(x - radius, y), g.Point(x + radius, y), 
                         g.Point(x, y - height)) 
        drawables.append(body)

        exhaust_height = (self._exhaust_max_height * self._thrust_percent * 
                          SCALE)
        if exhaust_height:
            exhaust = g.Line(g.Point(x, y),
                             g.Point(x, y + exhaust_height))
            exhaust.setWidth(self._exhaust_width)  # Do not scale exhaust width.
            exhaust.setOutline(self._exhaust_color)
            drawables.append(exhaust) 
        return drawables


class Simulation(object):
    """Simulates the Rocket environment."""

    def __init__(self):
        self._window = g.GraphWin(TITLE, WIDTH, HEIGHT, autoflush=False)       
        controller = PIDController(setpoint=TARGET_Y, kp=1., ki=.0001, kd=2.3)
        self._rocket = Rocket(pos=(WIDTH/2, GROUND_Y), controller=controller)

    def _static_drawables(self):
        """Returns GraphicsObjects that only need to be drawn once."""
        ground = g.Line(g.Point(0, GROUND_Y), g.Point(WIDTH, GROUND_Y))
        target = g.Line(g.Point(WIDTH/2 - 50, TARGET_Y), 
                        g.Point(WIDTH/2 + 50, TARGET_Y))
        target.setOutline("red")
        return ground, target

    def _draw(self, drawables):
        for drawable in drawables:
            drawable.draw(self._window)

    def _undraw(self, drawables):
        for drawable in drawables:
            drawable.undraw()

    def run(self):
        """Runs the simulation until the user closes out."""
        self._draw(self._static_drawables())
        dynamic_drawables = []
        t0 = time.time()
        while self._window.isOpen():
            # Resolve time since last tick.
            t = time.time()
            dt = (t - t0) * SCALE
            t0 = t

            # Run simulation for 1 tick.
            self._undraw(dynamic_drawables)
            dynamic_drawables = []
            self._rocket.update(dt)
            dynamic_drawables.extend(self._rocket.drawables())
            self._draw(dynamic_drawables)
            g.update(FPS)  # Enforce FPS.

if __name__ == '__main__':
    Simulation().run()
