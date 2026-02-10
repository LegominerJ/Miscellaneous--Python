"""
Infinite 2D Platformer with Multi-Directional Procedural Generation
Controls: Arrow Keys=Move, Z=Jump, X=Dash (Classic Celeste controls)
"""

import pygame
import random
import math
from enum import Enum

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (50, 120, 200)
GREEN = (50, 200, 50)
RED = (200, 50, 50)
YELLOW = (200, 200, 50)
PURPLE = (150, 50, 200)
GRAY = (100, 100, 100)

# Physics Constants
GRAVITY = 0.7
PLAYER_SPEED = 6
JUMP_STRENGTH = -15
DASH_SPEED = 20
DASH_DURATION = 10
COYOTE_TIME = 6


class PlatformType(Enum):
    NORMAL = 1
    CRUMBLING = 2
    BOUNCY = 3
    MOVING = 4


class Player:
    """Player character with physics and controls"""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 40
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.dashing = False
        self.coyote_timer = 0
        
    def update(self, keys, platforms):
        """Update player position and handle input"""
        # Horizontal movement
        if not self.dashing:
            if keys[pygame.K_LEFT]:
                self.vel_x = -PLAYER_SPEED
            elif keys[pygame.K_RIGHT]:
                self.vel_x = PLAYER_SPEED
            else:
                self.vel_x = 0
        
        # Update coyote time
        if self.on_ground:
            self.coyote_timer = COYOTE_TIME
        elif self.coyote_timer > 0:
            self.coyote_timer -= 1

        # Jumping (Z key - Celeste classic)
        if keys[pygame.K_z] and self.coyote_timer > 0 and self.vel_y >= 0:
            self.vel_y = JUMP_STRENGTH
            self.coyote_timer = 0
            self.on_ground = False
        
        # Dash mechanic (X key - Celeste classic)
        if keys[pygame.K_x] and self.dash_cooldown <= 0 and not self.dashing:
            self.dashing = True
            self.dash_timer = DASH_DURATION
            self.dash_cooldown = 60
            
            # Determine dash direction based on arrow keys
            dash_x = 0
            dash_y = 0
            
            if keys[pygame.K_LEFT]:
                dash_x = -1
            elif keys[pygame.K_RIGHT]:
                dash_x = 1
            
            if keys[pygame.K_UP]:
                dash_y = -1
            elif keys[pygame.K_DOWN]:
                dash_y = 1
            
            # Default to right if no direction pressed
            if dash_x == 0 and dash_y == 0:
                dash_x = 1
            
            # Normalize diagonal dashes
            magnitude = math.sqrt(dash_x**2 + dash_y**2)
            if magnitude > 0:
                self.vel_x = (dash_x / magnitude) * DASH_SPEED
                self.vel_y = (dash_y / magnitude) * DASH_SPEED
        
        # Handle dash
        if self.dashing:
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.dashing = False
                self.vel_x = PLAYER_SPEED if self.vel_x > 0 else -PLAYER_SPEED
        
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        
        # Apply gravity
        if not self.dashing:
            self.vel_y += GRAVITY
        
        # Apply velocity
        self.x += self.vel_x
        self.y += self.vel_y
        
        # Collision detection
        self.on_ground = False
        for platform in platforms:
            if self.check_collision(platform):
                self.handle_collision(platform)
    
    def check_collision(self, platform):
        """Check if player collides with platform"""
        return (self.x < platform.x + platform.width and
                self.x + self.width > platform.x and
                self.y < platform.y + platform.height and
                self.y + self.height > platform.y)
    
    def handle_collision(self, platform):
        """Handle collision with platform"""
        # Only collide from top
        if self.vel_y > 0 and self.y + self.height - self.vel_y <= platform.y + 5:
            self.y = platform.y - self.height
            self.vel_y = 0
            self.on_ground = True
            
            # Handle platform-specific effects
            if platform.platform_type == PlatformType.BOUNCY:
                self.vel_y = JUMP_STRENGTH * 1.5
                self.on_ground = False
            elif platform.platform_type == PlatformType.CRUMBLING:
                platform.start_crumble()
    
    def draw(self, screen, camera_x, camera_y):
        """Draw player on screen"""
        color = YELLOW if self.dashing else BLUE
        pygame.draw.rect(screen, color, 
                        (self.x - camera_x, self.y - camera_y, self.width, self.height))
        # Draw eyes
        pygame.draw.circle(screen, WHITE, 
                          (int(self.x - camera_x + 10), int(self.y - camera_y + 12)), 4)
        pygame.draw.circle(screen, WHITE, 
                          (int(self.x - camera_x + 20), int(self.y - camera_y + 12)), 4)
        pygame.draw.circle(screen, BLACK, 
                          (int(self.x - camera_x + 10), int(self.y - camera_y + 12)), 2)
        pygame.draw.circle(screen, BLACK, 
                          (int(self.x - camera_x + 20), int(self.y - camera_y + 12)), 2)


class Platform:
    """Platform class with different types and behaviors"""
    
    def __init__(self, x, y, width, platform_type=PlatformType.NORMAL):
        self.x = x
        self.y = y
        self.width = width
        self.height = 20
        self.platform_type = platform_type
        self.crumble_timer = 0
        self.active = True
        
        # Moving platform properties
        if platform_type == PlatformType.MOVING:
            self.original_y = y
            self.move_range = 100
            self.move_speed = 2
            self.move_direction = 1
    
    def update(self):
        """Update platform state"""
        if self.platform_type == PlatformType.CRUMBLING and self.crumble_timer > 0:
            self.crumble_timer -= 1
            if self.crumble_timer <= 0:
                self.active = False
        
        if self.platform_type == PlatformType.MOVING:
            self.y += self.move_speed * self.move_direction
            if abs(self.y - self.original_y) > self.move_range:
                self.move_direction *= -1
    
    def start_crumble(self):
        """Start crumbling animation"""
        if self.crumble_timer == 0:
            self.crumble_timer = 30
    
    def draw(self, screen, camera_x, camera_y):
        """Draw platform on screen"""
        if not self.active:
            return
        
        # Choose color based on type
        if self.platform_type == PlatformType.NORMAL:
            color = GREEN
        elif self.platform_type == PlatformType.CRUMBLING:
            if self.crumble_timer > 0 and self.crumble_timer % 10 < 5:
                color = RED
            else:
                color = GRAY
        elif self.platform_type == PlatformType.BOUNCY:
            color = PURPLE
        elif self.platform_type == PlatformType.MOVING:
            color = YELLOW
        
        pygame.draw.rect(screen, color, 
                        (self.x - camera_x, self.y - camera_y, self.width, self.height))
        
        # Add visual indicators
        if self.platform_type == PlatformType.BOUNCY:
            for i in range(0, int(self.width), 20):
                pygame.draw.line(screen, WHITE, 
                               (self.x - camera_x + i, self.y - camera_y + 5),
                               (self.x - camera_x + i, self.y - camera_y + 15), 2)
        elif self.platform_type == PlatformType.MOVING:
            pygame.draw.polygon(screen, BLACK, [
                (self.x - camera_x + self.width // 2, self.y - camera_y + 5),
                (self.x - camera_x + self.width // 2 - 5, self.y - camera_y + 12),
                (self.x - camera_x + self.width // 2 + 5, self.y - camera_y + 12)
            ])


class PlatformGenerator:
    """Simple, reliable linear procedural platform generation"""
    
    def __init__(self, seed=None):
        self.seed = seed if seed else random.randint(0, 1000000)
        random.seed(self.seed)
        
        self.platforms = []
        self.last_platform_x = 0
        self.last_platform_y = 400
        self.difficulty = 0
        
        # Generate initial platforms
        self.generate_starting_platform()
        for _ in range(15):
            self.generate_platform()
    
    def generate_starting_platform(self):
        """Generate safe starting platform"""
        start = Platform(0, 400, 250, PlatformType.NORMAL)
        self.platforms.append(start)
        self.last_platform_x = 0
        self.last_platform_y = 400
    
    def generate_platform(self):
        """Generate new platform - simple and reliable"""
        # Horizontal spacing
        base_spacing = 150
        spacing_variance = 50 + int(self.difficulty * 30)
        spacing = base_spacing + random.randint(-50, spacing_variance)
        spacing = max(80, spacing)
        
        # Vertical offset
        vertical_variance = 80 + int(self.difficulty * 40)
        vertical_offset = random.randint(-vertical_variance, vertical_variance)
        
        # Calculate new position
        new_x = self.last_platform_x + spacing
        new_y = self.last_platform_y + vertical_offset
        
        # Keep platforms within reasonable bounds
        new_y = max(150, min(new_y, SCREEN_HEIGHT - 100))
        
        # Platform width (decreases with difficulty)
        base_width = 150
        width_reduction = int(self.difficulty * 20)
        width = base_width - width_reduction + random.randint(-30, 30)
        width = max(60, width)
        
        # Choose platform type
        platform_type = self.choose_platform_type()
        
        # Create platform
        platform = Platform(new_x, new_y, width, platform_type)
        self.platforms.append(platform)
        
        # Update last position
        self.last_platform_x = new_x
        self.last_platform_y = new_y
        
        # Update difficulty
        self.difficulty = min(new_x / 1000, 5)
    
    def choose_platform_type(self):
        """Choose platform type based on difficulty"""
        if self.difficulty < 0.5:
            return PlatformType.NORMAL
        
        rand_val = random.random()
        
        if rand_val < 0.5:
            return PlatformType.NORMAL
        elif rand_val < 0.65 + self.difficulty * 0.05:
            return PlatformType.CRUMBLING
        elif rand_val < 0.8 + self.difficulty * 0.03:
            return PlatformType.BOUNCY
        else:
            return PlatformType.MOVING
    
    def update(self, player):
        """Update platforms and generate new ones as needed"""
        camera_x = player.x - SCREEN_WIDTH // 3
        
        # Remove platforms far behind camera
        self.platforms = [
            p for p in self.platforms 
            if p.x > camera_x - 500
        ]
        
        # Generate new platforms ahead of camera
        while self.last_platform_x < camera_x + SCREEN_WIDTH + 500:
            self.generate_platform()
        
        # Update all platforms
        for platform in self.platforms:
            platform.update()
    
    def get_active_platforms(self):
        """Get list of active platforms"""
        return [p for p in self.platforms if p.active]


class Camera:
    """Smooth scrolling camera that follows player in X and Y"""
    
    def __init__(self):
        self.x = 0
        self.y = 0
        self.target_x = 0
        self.target_y = 0
        self.smoothness = 0.1
    
    def update(self, player):
        """Update camera position to follow player"""
        # Center player horizontally (offset left a bit)
        self.target_x = player.x - SCREEN_WIDTH // 3
        self.target_x = max(0, self.target_x)
        
        # Center player vertically
        self.target_y = player.y - SCREEN_HEIGHT // 2
        
        # Smooth camera movement
        self.x += (self.target_x - self.x) * self.smoothness
        self.y += (self.target_y - self.y) * self.smoothness
    
    def get_x(self):
        return int(self.x)
    
    def get_y(self):
        return int(self.y)


class Game:
    """Main game class"""
    
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Infinite Platformer - Celeste Controls")
        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        self.reset_game()
    
    def reset_game(self):
        """Reset game state"""
        seed = random.randint(0, 1000000)
        self.player = Player(100, 300)
        self.generator = PlatformGenerator(seed)
        self.camera = Camera()
        self.score = 0
        self.game_over = False
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r and self.game_over:
                    self.reset_game()
    
    def update(self):
        """Update game state"""
        if self.game_over:
            return
        
        keys = pygame.key.get_pressed()
        
        # Update platforms
        self.generator.update(self.player)
        
        # Update player
        self.player.update(keys, self.generator.get_active_platforms())
        
        # Update camera
        self.camera.update(self.player)
        
        # Update score (distance traveled)
        self.score = max(self.score, int(self.player.x / 10))
        
        # Check if player fell off screen
        if self.player.y > self.camera.get_y() + SCREEN_HEIGHT + 100:
            self.game_over = True
    
    def draw(self):
        """Draw everything on screen"""
        # Clear screen
        self.screen.fill(BLACK)
        
        # Draw background grid
        camera_x = self.camera.get_x()
        camera_y = self.camera.get_y()
        
        grid_color = (20, 20, 40)
        for x in range(-int(camera_x % 100), SCREEN_WIDTH, 100):
            pygame.draw.line(self.screen, grid_color, (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(-int(camera_y % 100), SCREEN_HEIGHT, 100):
            pygame.draw.line(self.screen, grid_color, (0, y), (SCREEN_WIDTH, y), 1)
        
        # Draw platforms
        for platform in self.generator.get_active_platforms():
            platform.draw(self.screen, camera_x, camera_y)

        # Draw player
        self.player.draw(self.screen, camera_x, camera_y)
        
        # Draw UI
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # Dash cooldown indicator
        if self.player.dash_cooldown > 0:
            cooldown_width = (self.player.dash_cooldown / 60) * 100
            pygame.draw.rect(self.screen, RED, (10, 50, 100, 10))
            pygame.draw.rect(self.screen, GREEN, (10, 50, cooldown_width, 10))
        else:
            dash_text = self.small_font.render("DASH READY", True, GREEN)
            self.screen.blit(dash_text, (10, 50))
        
        # Controls
        controls_text = self.small_font.render("Arrow Keys=Move  Z=Jump  X=Dash", True, GRAY)
        self.screen.blit(controls_text, (10, SCREEN_HEIGHT - 30))
        
        # Game over screen
        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            
            game_over_text = self.font.render("GAME OVER", True, RED)
            score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
            restart_text = self.small_font.render("Press R to Restart", True, WHITE)
            
            self.screen.blit(game_over_text, 
                           (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 
                            SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(score_text, 
                           (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 
                            SCREEN_HEIGHT // 2))
            self.screen.blit(restart_text, 
                           (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 
                            SCREEN_HEIGHT // 2 + 50))
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()


# Run the game
if __name__ == "__main__":
    game = Game()
    game.run()