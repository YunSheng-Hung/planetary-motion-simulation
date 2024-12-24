import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Screen Settings
WIDTH, HEIGHT = 1200, 1000
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Planetary Motion Simulation")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
BLUE = (100, 149, 237)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
ORANGE = (255, 165, 0)
LIGHT_BLUE = (173, 216, 230)
LIGHT_GREEN = (144, 238, 144)
LIGHT_GRAY = (169, 169, 169)
DARK_GRAY = (169, 169, 169)

# Physics Constants
G = 6.67430e-11 
SCALE = 100 / 1.496e11  # Scale: 100 pixels = 1 AU
TIMESTEP = 3600 * 24  # 1 day
simulation_speed = 1.0

# Camera Variables
offset_x, offset_y = 0, 0
zoom = 1.0
scroll_speed = 0.1
trail_limit = 200  # Max number of points in trail

# Others variables
paused = False 
hovered_planet = None 

TYPE_MAP = {
    1: "Star",
    2: "Planet",
    3: "Moon",
    4: "Comet",
    5: "Asteroid",
    6: "Black Hole"
}

class Planet:
    def __init__(self, x, y, radius, color, mass, name="", type_id=0):
        self.x = x
        self.y = y
        self.radius = radius
        self.physical_radius = radius / SCALE
        self.color = color
        self.mass = mass
        self.name = name
        self.type_id = type_id
        self.orbit = []
        self.x_vel = 0
        self.y_vel = 0

    def draw(self, screen):
        # Adjust for zoom and pan
        scaled_x = (self.x * SCALE * zoom + WIDTH / 2 + offset_x)
        scaled_y = (self.y * SCALE * zoom + HEIGHT / 2 + offset_y)

        # Draw orbit path
        if len(self.orbit) > 2:
            updated_points = [
                ((x * SCALE * zoom + WIDTH / 2 + offset_x), (y * SCALE * zoom + HEIGHT / 2 + offset_y))
                for x, y in self.orbit]
            pygame.draw.lines(screen, self.color, False, updated_points, 1)

        # Draw planet
        pygame.draw.circle(screen, self.color, (int(scaled_x), int(scaled_y)), int(self.radius * zoom))

        # Display
        type_name = TYPE_MAP.get(self.type_id, "Unknown")
        font = pygame.font.SysFont("Arial", 14)
        name_text = font.render(f"{self.name} / {type_name}", True, WHITE)
        screen.blit(name_text, (int(scaled_x) + 5, int(scaled_y) - 5))

    def attract(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        if distance == 0:
            return 0, 0

        force = G * self.mass * other.mass / distance ** 2
        theta = math.atan2(dy, dx)
        fx = math.cos(theta) * force
        fy = math.sin(theta) * force
        return fx, fy

    def collide(self, other):
        total_mass = self.mass + other.mass
        x_vel = (self.x_vel * self.mass + other.x_vel * other.mass) / total_mass
        y_vel = (self.y_vel * self.mass + other.y_vel * other.mass) / total_mass

        # New radius based on volume
        new_radius = ((self.physical_radius ** 3 + other.physical_radius ** 3) ** (1/3)) * SCALE

        new_type = self.type_id if self.mass > other.mass else other.type_id
        new_name = f"{self.name}+{other.name}"

        # Create new planet
        new_planet = Planet(
            (self.x + other.x) / 2, (self.y + other.y) / 2,
            new_radius, self.color, total_mass, new_name, new_type
        )
        new_planet.x_vel = x_vel
        new_planet.y_vel = y_vel

        return new_planet

    def update_position(self, planets):
        total_fx = total_fy = 0
        for planet in planets[:]:
            if self == planet:
                continue

            # Collision detection
            dx = planet.x - self.x
            dy = planet.y - self.y
            distance = math.sqrt(dx ** 2 + dy ** 2)

            if distance <= (self.physical_radius + planet.physical_radius):
                new_planet = self.collide(planet)
                planets.remove(self)
                planets.remove(planet)
                planets.append(new_planet)
                return

            fx, fy = self.attract(planet)
            total_fx += fx
            total_fy += fy

        self.x_vel += total_fx / self.mass * TIMESTEP
        self.y_vel += total_fy / self.mass * TIMESTEP

        self.x += self.x_vel * TIMESTEP
        self.y += self.y_vel * TIMESTEP
        self.orbit.append((self.x, self.y))

        if len(self.orbit) > trail_limit:
            self.orbit.pop(0)

def draw_info(screen, planet, mouse_x, mouse_y):
    """Display planet data at mouse position"""
    font = pygame.font.SysFont("Arial", 16)
    info_lines = [
        f"Name: {planet.name}",
        f"Type: {TYPE_MAP[planet.type_id]}",
        f"Radius: {planet.physical_radius:.2e} m",
        f"Mass: {planet.mass:.2e} kg",
        f"Position: ({planet.x:.2e}, {planet.y:.2e}) m",
        f"Velocity: ({planet.x_vel:.2e}, {planet.y_vel:.2e}) m/s"
    ]
    
    # Calculate background box size
    max_line_width = max([font.size(line)[0] for line in info_lines])
    box_width = max_line_width + 20 
    box_height = len(info_lines) * 20 + 10

    box_x = mouse_x + 10
    box_y = mouse_y + 10

    background_color = (0, 0, 0, 180)
    border_color = (255, 255, 255)
    border_width = 2

    pygame.draw.rect(screen, background_color, (box_x, box_y, box_width, box_height))
    pygame.draw.rect(screen, border_color, (box_x, box_y, box_width, box_height), border_width)

    for i, line in enumerate(info_lines):
        text_surface = font.render(line, True, WHITE)
        screen.blit(text_surface, (box_x + 10, box_y + 20 * i))  # 在框內顯示文字

# Mode Selection
print("Select Mode:")
print("1. Solar System Model")
print("2. Manual Setup")
mode = int(input("Enter mode (1 or 2): "))

planets = []

if mode == 1:
    #Solar System with all 8 planets
    sun = Planet(0, 0, 30, YELLOW, 1.989e30, "Sun", 1)

    mercury = Planet(0.387 * 1.496e11, 0, 3, DARK_GRAY, 3.3011e23, "Mercury", 2)
    mercury.y_vel = 47870
    venus = Planet(0.723 * 1.496e11, 0, 6, GREEN, 4.867e24, "Venus", 2)
    venus.y_vel = 35020
    earth = Planet(1 * 1.496e11, 0, 10, BLUE, 5.972e24, "Earth", 2)
    earth.y_vel = 29780
    mars = Planet(1.524 * 1.496e11, 0, 8, RED, 6.39e23, "Mars", 2)
    mars.y_vel = 24070
    jupiter = Planet(5.203 * 1.496e11, 0, 20, ORANGE, 1.898e27, "Jupiter", 2)
    jupiter.y_vel = 13070
    saturn = Planet(9.582 * 1.496e11, 0, 18, LIGHT_GRAY, 5.683e26, "Saturn", 2)
    saturn.y_vel = 9680
    uranus = Planet(19.191 * 1.496e11, 0, 14, LIGHT_BLUE, 8.681e25, "Uranus", 2)
    uranus.y_vel = 6800
    neptune = Planet(30.07 * 1.496e11, 0, 14, LIGHT_GREEN, 1.024e26, "Neptune", 2)
    neptune.y_vel = 5430

    planets = [sun, mercury, venus, earth, mars, jupiter, saturn, uranus, neptune]

elif mode == 2:
    while True:
        try:
            num_planets = int(input("Enter number of planets: "))
            if num_planets > 0:
                break
            else:
                print("Please enter a positive number of planets.")
        except ValueError:
            print("Invalid input. Please enter a valid integer.")

    for i in range(num_planets):
        print(f"Enter details for Planet {i+1}:")
        name = input("Name: ")
        type_id = int(input("Type (1: Star, 2: Planet, 3: Moon, 4: Comet, 5: Asteroid, 6: Black Hole): "))
        x = float(input("x-position (pixels): ")) / SCALE  
        y = float(input("y-position (pixels): ")) / SCALE  
        radius = int(input("Radius (pixels): "))
        mass = float(input("Mass (kg): "))
        x_vel = float(input("x-velocity (m/s): "))
        y_vel = float(input("y-velocity (m/s): "))

        color = random.choice([BLACK, WHITE, YELLOW, BLUE, RED, GREEN, ORANGE, LIGHT_BLUE, LIGHT_GREEN, LIGHT_GRAY, DARK_GRAY])
        planet = Planet(x, y, radius, color, mass, name, type_id)
        planet.x_vel = x_vel
        planet.y_vel = y_vel
        planets.append(planet)

# Simulation Loop
running = True
clock = pygame.time.Clock()
moving = False
start_pos = (0, 0)
dragging_planet = None

while running:
    clock.tick(60)
    screen.fill(BLACK)
    mouse_x, mouse_y = pygame.mouse.get_pos()
    hovered_planet = None
    paused = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                clicked_planet = None
                for planet in planets:
                    distance_to_mouse = math.sqrt((planet.x * SCALE + WIDTH / 2 + offset_x - mouse_x) ** 2 +
                                                (planet.y * SCALE + HEIGHT / 2 + offset_y - mouse_y) ** 2)
                    if distance_to_mouse <= planet.radius * zoom:
                        clicked_planet = planet
                        break

                if clicked_planet:
                    dragging_planet = clicked_planet
                    paused = True
                    start_pos = (mouse_x, mouse_y)
                else:
                    moving = True
                    start_pos = event.pos

            elif event.button == 4:
                zoom += scroll_speed
            elif event.button == 5:
                zoom = max(0.1, zoom - scroll_speed)

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging_planet = None
                paused = False
                moving = False 


        elif event.type == pygame.MOUSEMOTION and moving:
            dx, dy = event.rel
            offset_x += dx
            offset_y += dy

    if dragging_planet:
        dx = (mouse_x - start_pos[0]) / (SCALE * zoom)
        dy = (mouse_y - start_pos[1]) / (SCALE * zoom)

        dragging_planet.x += dx 
        dragging_planet.y += dy
        start_pos = (mouse_x, mouse_y)

    for planet in planets:
        scaled_x = (planet.x * SCALE * zoom + WIDTH / 2 + offset_x)
        scaled_y = (planet.y * SCALE * zoom + HEIGHT / 2 + offset_y)
        distance_to_mouse = math.sqrt((scaled_x - mouse_x) ** 2 + (scaled_y - mouse_y) ** 2)

        if distance_to_mouse <= planet.radius * zoom:
            hovered_planet = planet
            paused = True
            break
        else:
            if dragging_planet is None:
                paused = False

    for planet in planets:
        if not paused or planet == dragging_planet:
            planet.update_position(planets)

        planet.draw(screen)

    if hovered_planet:
        draw_info(screen, hovered_planet, mouse_x, mouse_y)

    pygame.display.flip()

pygame.quit()
