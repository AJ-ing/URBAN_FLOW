from __future__ import annotations

import random
from typing import Any, Dict, Iterable

import pygame

SIMULATION_TIME_S = 300.0
SPAWN_INTERVAL_S = 0.4

currentGreen = 0
currentYellow = 0

speeds = {"car": 2.25, "bus": 1.8, "truck": 1.8, "bike": 2.5}

x = {
    "right": [0, 0, 0],
    "down": [755, 727, 697],
    "left": [1400, 1400, 1400],
    "up": [602, 627, 657],
}
y = {
    "right": [348, 370, 398],
    "down": [0, 0, 0],
    "left": [498, 466, 436],
    "up": [800, 800, 800],
}

vehicles: Dict[str, Dict[Any, Any]] = {
    "right": {0: [], 1: [], 2: [], "crossed": 0},
    "down": {0: [], 1: [], 2: [], "crossed": 0},
    "left": {0: [], 1: [], 2: [], "crossed": 0},
    "up": {0: [], 1: [], 2: [], "crossed": 0},
}

vehicleTypes = {0: "car", 1: "bus", 2: "truck", 3: "bike"}
directionNumbers = {0: "down", 1: "left", 2: "up", 3: "right"}
directionLabels = {0: "North", 1: "East", 2: "South", 3: "West"}
directionToIndex = {name: index for index, name in directionNumbers.items()}

stopLines = {"right": 590, "down": 330, "left": 800, "up": 535}
defaultStop = {"right": 580, "down": 320, "left": 810, "up": 545}

stoppingGap = 25
movingGap = 25

allowedVehicleTypes = {"car": True, "bus": True, "truck": True, "bike": True}
allowedVehicleTypesList = [
    index
    for index, vehicle_type in vehicleTypes.items()
    if allowedVehicleTypes[vehicle_type]
]
vehiclesTurned: Dict[str, Dict[int, list[Vehicle]]] = {
    "right": {1: [], 2: []},
    "down": {1: [], 2: []},
    "left": {1: [], 2: []},
    "up": {1: [], 2: []},
}
vehiclesNotTurned: Dict[str, Dict[int, list[Vehicle]]] = {
    "right": {1: [], 2: []},
    "down": {1: [], 2: []},
    "left": {1: [], 2: []},
    "up": {1: [], 2: []},
}
rotationAngle = 3
mid = {
    "right": {"x": 705, "y": 445},
    "down": {"x": 695, "y": 450},
    "left": {"x": 695, "y": 425},
    "up": {"x": 695, "y": 400},
}

simulation: pygame.sprite.Group = pygame.sprite.Group()


class Vehicle(pygame.sprite.Sprite):
    def __init__(self, lane, vehicleClass, direction_number, direction, will_turn):
        super().__init__()
        self.lane = lane
        self.vehicleClass = vehicleClass
        self.nominal_speed = speeds[vehicleClass]
        self.speed = 0.0
        self.direction_number = direction_number
        self.direction = direction
        self.x = x[direction][lane]
        self.y = y[direction][lane]
        self.crossed = 0
        self.willTurn = will_turn
        self.turned = 0
        self.rotateAngle = 0
        vehicles[direction][lane].append(self)
        self.index = len(vehicles[direction][lane]) - 1
        self.crossedIndex = 0
        path = "images/" + direction + "/" + vehicleClass + ".png"
        self.originalImage = pygame.image.load(path)
        self.image = pygame.image.load(path)

        if (
            len(vehicles[direction][lane]) > 1
            and vehicles[direction][lane][self.index - 1].crossed == 0
        ):
            if direction == "right":
                self.stop = (
                    vehicles[direction][lane][self.index - 1].stop
                    - vehicles[direction][lane][self.index - 1].image.get_rect().width
                    - stoppingGap
                )
            elif direction == "left":
                self.stop = (
                    vehicles[direction][lane][self.index - 1].stop
                    + vehicles[direction][lane][self.index - 1].image.get_rect().width
                    + stoppingGap
                )
            elif direction == "down":
                self.stop = (
                    vehicles[direction][lane][self.index - 1].stop
                    - vehicles[direction][lane][self.index - 1].image.get_rect().height
                    - stoppingGap
                )
            elif direction == "up":
                self.stop = (
                    vehicles[direction][lane][self.index - 1].stop
                    + vehicles[direction][lane][self.index - 1].image.get_rect().height
                    + stoppingGap
                )
        else:
            self.stop = defaultStop[direction]

        if direction == "right":
            temp = self.image.get_rect().width + stoppingGap
            x[direction][lane] -= temp
        elif direction == "left":
            temp = self.image.get_rect().width + stoppingGap
            x[direction][lane] += temp
        elif direction == "down":
            temp = self.image.get_rect().height + stoppingGap
            y[direction][lane] -= temp
        elif direction == "up":
            temp = self.image.get_rect().height + stoppingGap
            y[direction][lane] += temp
        simulation.add(self)

    def render(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def move(self):
        start_x = self.x
        start_y = self.y
        signal_open = (
            currentGreen == directionToIndex[self.direction] and currentYellow == 0
        )

        if self.direction == "right":
            if (
                self.crossed == 0
                and self.x + self.image.get_rect().width > stopLines[self.direction]
            ):
                self.crossed = 1
                vehicles[self.direction]["crossed"] += 1
                if self.willTurn == 0:
                    vehiclesNotTurned[self.direction][self.lane].append(self)
                    self.crossedIndex = (
                        len(vehiclesNotTurned[self.direction][self.lane]) - 1
                    )
            if self.willTurn == 1:
                if self.lane == 1:
                    if (
                        self.crossed == 0
                        or self.x + self.image.get_rect().width
                        < stopLines[self.direction] + 40
                    ):
                        if (
                            self.x + self.image.get_rect().width <= self.stop
                            or signal_open
                            or self.crossed == 1
                        ) and (
                            self.index == 0
                            or self.x + self.image.get_rect().width
                            < (
                                vehicles[self.direction][self.lane][self.index - 1].x
                                - movingGap
                            )
                            or vehicles[self.direction][self.lane][
                                self.index - 1
                            ].turned
                            == 1
                        ):
                            self.x += self.nominal_speed
                    else:
                        if self.turned == 0:
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(
                                self.originalImage, self.rotateAngle
                            )
                            self.x += 2.4
                            self.y -= 2.8
                            if self.rotateAngle == 90:
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = (
                                    len(vehiclesTurned[self.direction][self.lane]) - 1
                                )
                        else:
                            if self.crossedIndex == 0 or (
                                self.y
                                > (
                                    vehiclesTurned[self.direction][self.lane][
                                        self.crossedIndex - 1
                                    ].y
                                    + vehiclesTurned[self.direction][self.lane][
                                        self.crossedIndex - 1
                                    ]
                                    .image.get_rect()
                                    .height
                                    + movingGap
                                )
                            ):
                                self.y -= self.nominal_speed
                elif self.lane == 2:
                    if (
                        self.crossed == 0
                        or self.x + self.image.get_rect().width
                        < mid[self.direction]["x"]
                    ):
                        if (
                            self.x + self.image.get_rect().width <= self.stop
                            or signal_open
                            or self.crossed == 1
                        ) and (
                            self.index == 0
                            or self.x + self.image.get_rect().width
                            < (
                                vehicles[self.direction][self.lane][self.index - 1].x
                                - movingGap
                            )
                            or vehicles[self.direction][self.lane][
                                self.index - 1
                            ].turned
                            == 1
                        ):
                            self.x += self.nominal_speed
                    else:
                        if self.turned == 0:
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(
                                self.originalImage, -self.rotateAngle
                            )
                            self.x += 2
                            self.y += 1.8
                            if self.rotateAngle == 90:
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = (
                                    len(vehiclesTurned[self.direction][self.lane]) - 1
                                )
                        else:
                            if self.crossedIndex == 0 or (
                                (self.y + self.image.get_rect().height)
                                < (
                                    vehiclesTurned[self.direction][self.lane][
                                        self.crossedIndex - 1
                                    ].y
                                    - movingGap
                                )
                            ):
                                self.y += self.nominal_speed
            else:
                if self.crossed == 0:
                    if (
                        self.x + self.image.get_rect().width <= self.stop or signal_open
                    ) and (
                        self.index == 0
                        or self.x + self.image.get_rect().width
                        < (
                            vehicles[self.direction][self.lane][self.index - 1].x
                            - movingGap
                        )
                    ):
                        self.x += self.nominal_speed
                else:
                    if self.crossedIndex == 0 or (
                        self.x + self.image.get_rect().width
                        < (
                            vehiclesNotTurned[self.direction][self.lane][
                                self.crossedIndex - 1
                            ].x
                            - movingGap
                        )
                    ):
                        self.x += self.nominal_speed

        elif self.direction == "down":
            if (
                self.crossed == 0
                and self.y + self.image.get_rect().height > stopLines[self.direction]
            ):
                self.crossed = 1
                vehicles[self.direction]["crossed"] += 1
                if self.willTurn == 0:
                    vehiclesNotTurned[self.direction][self.lane].append(self)
                    self.crossedIndex = (
                        len(vehiclesNotTurned[self.direction][self.lane]) - 1
                    )
            if self.willTurn == 1:
                if self.lane == 1:
                    if (
                        self.crossed == 0
                        or self.y + self.image.get_rect().height
                        < stopLines[self.direction] + 50
                    ):
                        if (
                            self.y + self.image.get_rect().height <= self.stop
                            or signal_open
                            or self.crossed == 1
                        ) and (
                            self.index == 0
                            or self.y + self.image.get_rect().height
                            < (
                                vehicles[self.direction][self.lane][self.index - 1].y
                                - movingGap
                            )
                            or vehicles[self.direction][self.lane][
                                self.index - 1
                            ].turned
                            == 1
                        ):
                            self.y += self.nominal_speed
                    else:
                        if self.turned == 0:
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(
                                self.originalImage, self.rotateAngle
                            )
                            self.x += 1.2
                            self.y += 1.8
                            if self.rotateAngle == 90:
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = (
                                    len(vehiclesTurned[self.direction][self.lane]) - 1
                                )
                        else:
                            if self.crossedIndex == 0 or (
                                (self.x + self.image.get_rect().width)
                                < (
                                    vehiclesTurned[self.direction][self.lane][
                                        self.crossedIndex - 1
                                    ].x
                                    - movingGap
                                )
                            ):
                                self.x += self.nominal_speed
                elif self.lane == 2:
                    if (
                        self.crossed == 0
                        or self.y + self.image.get_rect().height
                        < mid[self.direction]["y"]
                    ):
                        if (
                            self.y + self.image.get_rect().height <= self.stop
                            or signal_open
                            or self.crossed == 1
                        ) and (
                            self.index == 0
                            or self.y + self.image.get_rect().height
                            < (
                                vehicles[self.direction][self.lane][self.index - 1].y
                                - movingGap
                            )
                            or vehicles[self.direction][self.lane][
                                self.index - 1
                            ].turned
                            == 1
                        ):
                            self.y += self.nominal_speed
                    else:
                        if self.turned == 0:
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(
                                self.originalImage, -self.rotateAngle
                            )
                            self.x -= 2.5
                            self.y += 2
                            if self.rotateAngle == 90:
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = (
                                    len(vehiclesTurned[self.direction][self.lane]) - 1
                                )
                        else:
                            if self.crossedIndex == 0 or (
                                self.x
                                > (
                                    vehiclesTurned[self.direction][self.lane][
                                        self.crossedIndex - 1
                                    ].x
                                    + vehiclesTurned[self.direction][self.lane][
                                        self.crossedIndex - 1
                                    ]
                                    .image.get_rect()
                                    .width
                                    + movingGap
                                )
                            ):
                                self.x -= self.nominal_speed
            else:
                if self.crossed == 0:
                    if (
                        self.y + self.image.get_rect().height <= self.stop
                        or signal_open
                    ) and (
                        self.index == 0
                        or self.y + self.image.get_rect().height
                        < (
                            vehicles[self.direction][self.lane][self.index - 1].y
                            - movingGap
                        )
                    ):
                        self.y += self.nominal_speed
                else:
                    if self.crossedIndex == 0 or (
                        self.y + self.image.get_rect().height
                        < (
                            vehiclesNotTurned[self.direction][self.lane][
                                self.crossedIndex - 1
                            ].y
                            - movingGap
                        )
                    ):
                        self.y += self.nominal_speed

        elif self.direction == "left":
            if self.crossed == 0 and self.x < stopLines[self.direction]:
                self.crossed = 1
                vehicles[self.direction]["crossed"] += 1
                if self.willTurn == 0:
                    vehiclesNotTurned[self.direction][self.lane].append(self)
                    self.crossedIndex = (
                        len(vehiclesNotTurned[self.direction][self.lane]) - 1
                    )
            if self.willTurn == 1:
                if self.lane == 1:
                    if self.crossed == 0 or self.x > stopLines[self.direction] - 70:
                        if (
                            self.x >= self.stop or signal_open or self.crossed == 1
                        ) and (
                            self.index == 0
                            or self.x
                            > (
                                vehicles[self.direction][self.lane][self.index - 1].x
                                + vehicles[self.direction][self.lane][self.index - 1]
                                .image.get_rect()
                                .width
                                + movingGap
                            )
                            or vehicles[self.direction][self.lane][
                                self.index - 1
                            ].turned
                            == 1
                        ):
                            self.x -= self.nominal_speed
                    else:
                        if self.turned == 0:
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(
                                self.originalImage, self.rotateAngle
                            )
                            self.x -= 1
                            self.y += 1.2
                            if self.rotateAngle == 90:
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = (
                                    len(vehiclesTurned[self.direction][self.lane]) - 1
                                )
                        else:
                            if self.crossedIndex == 0 or (
                                (self.y + self.image.get_rect().height)
                                < (
                                    vehiclesTurned[self.direction][self.lane][
                                        self.crossedIndex - 1
                                    ].y
                                    - movingGap
                                )
                            ):
                                self.y += self.nominal_speed
                elif self.lane == 2:
                    if self.crossed == 0 or self.x > mid[self.direction]["x"]:
                        if (
                            self.x >= self.stop or signal_open or self.crossed == 1
                        ) and (
                            self.index == 0
                            or self.x
                            > (
                                vehicles[self.direction][self.lane][self.index - 1].x
                                + vehicles[self.direction][self.lane][self.index - 1]
                                .image.get_rect()
                                .width
                                + movingGap
                            )
                            or vehicles[self.direction][self.lane][
                                self.index - 1
                            ].turned
                            == 1
                        ):
                            self.x -= self.nominal_speed
                    else:
                        if self.turned == 0:
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(
                                self.originalImage, -self.rotateAngle
                            )
                            self.x -= 1.8
                            self.y -= 2.5
                            if self.rotateAngle == 90:
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = (
                                    len(vehiclesTurned[self.direction][self.lane]) - 1
                                )
                        else:
                            if self.crossedIndex == 0 or (
                                self.y
                                > (
                                    vehiclesTurned[self.direction][self.lane][
                                        self.crossedIndex - 1
                                    ].y
                                    + vehiclesTurned[self.direction][self.lane][
                                        self.crossedIndex - 1
                                    ]
                                    .image.get_rect()
                                    .height
                                    + movingGap
                                )
                            ):
                                self.y -= self.nominal_speed
            else:
                if self.crossed == 0:
                    if (self.x >= self.stop or signal_open) and (
                        self.index == 0
                        or self.x
                        > (
                            vehicles[self.direction][self.lane][self.index - 1].x
                            + vehicles[self.direction][self.lane][self.index - 1]
                            .image.get_rect()
                            .width
                            + movingGap
                        )
                    ):
                        self.x -= self.nominal_speed
                else:
                    if self.crossedIndex == 0 or (
                        self.x
                        > (
                            vehiclesNotTurned[self.direction][self.lane][
                                self.crossedIndex - 1
                            ].x
                            + vehiclesNotTurned[self.direction][self.lane][
                                self.crossedIndex - 1
                            ]
                            .image.get_rect()
                            .width
                            + movingGap
                        )
                    ):
                        self.x -= self.nominal_speed

        elif self.direction == "up":
            if self.crossed == 0 and self.y < stopLines[self.direction]:
                self.crossed = 1
                vehicles[self.direction]["crossed"] += 1
                if self.willTurn == 0:
                    vehiclesNotTurned[self.direction][self.lane].append(self)
                    self.crossedIndex = (
                        len(vehiclesNotTurned[self.direction][self.lane]) - 1
                    )
            if self.willTurn == 1:
                if self.lane == 1:
                    if self.crossed == 0 or self.y > stopLines[self.direction] - 60:
                        if (
                            self.y >= self.stop or signal_open or self.crossed == 1
                        ) and (
                            self.index == 0
                            or self.y
                            > (
                                vehicles[self.direction][self.lane][self.index - 1].y
                                + vehicles[self.direction][self.lane][self.index - 1]
                                .image.get_rect()
                                .height
                                + movingGap
                            )
                            or vehicles[self.direction][self.lane][
                                self.index - 1
                            ].turned
                            == 1
                        ):
                            self.y -= self.nominal_speed
                    else:
                        if self.turned == 0:
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(
                                self.originalImage, self.rotateAngle
                            )
                            self.x -= 2
                            self.y -= 1.2
                            if self.rotateAngle == 90:
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = (
                                    len(vehiclesTurned[self.direction][self.lane]) - 1
                                )
                        else:
                            if self.crossedIndex == 0 or (
                                self.x
                                > (
                                    vehiclesTurned[self.direction][self.lane][
                                        self.crossedIndex - 1
                                    ].x
                                    + vehiclesTurned[self.direction][self.lane][
                                        self.crossedIndex - 1
                                    ]
                                    .image.get_rect()
                                    .width
                                    + movingGap
                                )
                            ):
                                self.x -= self.nominal_speed
                elif self.lane == 2:
                    if self.crossed == 0 or self.y > mid[self.direction]["y"]:
                        if (
                            self.y >= self.stop or signal_open or self.crossed == 1
                        ) and (
                            self.index == 0
                            or self.y
                            > (
                                vehicles[self.direction][self.lane][self.index - 1].y
                                + vehicles[self.direction][self.lane][self.index - 1]
                                .image.get_rect()
                                .height
                                + movingGap
                            )
                            or vehicles[self.direction][self.lane][
                                self.index - 1
                            ].turned
                            == 1
                        ):
                            self.y -= self.nominal_speed
                    else:
                        if self.turned == 0:
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(
                                self.originalImage, -self.rotateAngle
                            )
                            self.x += 1
                            self.y -= 1
                            if self.rotateAngle == 90:
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = (
                                    len(vehiclesTurned[self.direction][self.lane]) - 1
                                )
                        else:
                            if self.crossedIndex == 0 or (
                                self.x
                                < (
                                    vehiclesTurned[self.direction][self.lane][
                                        self.crossedIndex - 1
                                    ].x
                                    - vehiclesTurned[self.direction][self.lane][
                                        self.crossedIndex - 1
                                    ]
                                    .image.get_rect()
                                    .width
                                    - movingGap
                                )
                            ):
                                self.x += self.nominal_speed
            else:
                if self.crossed == 0:
                    if (self.y >= self.stop or signal_open) and (
                        self.index == 0
                        or self.y
                        > (
                            vehicles[self.direction][self.lane][self.index - 1].y
                            + vehicles[self.direction][self.lane][self.index - 1]
                            .image.get_rect()
                            .height
                            + movingGap
                        )
                    ):
                        self.y -= self.nominal_speed
                else:
                    if self.crossedIndex == 0 or (
                        self.y
                        > (
                            vehiclesNotTurned[self.direction][self.lane][
                                self.crossedIndex - 1
                            ].y
                            + vehiclesNotTurned[self.direction][self.lane][
                                self.crossedIndex - 1
                            ]
                            .image.get_rect()
                            .height
                            + movingGap
                        )
                    ):
                        self.y -= self.nominal_speed

        moved = self.x != start_x or self.y != start_y
        self.speed = self.nominal_speed if moved else 0.0

        # Despawn when vehicle is completely off-screen to prevent memory leaks and O(N) slowdowns
        if self.direction == "right" and self.x > 1450:
            self.kill()
        elif self.direction == "left" and self.x < -150:
            self.kill()
        elif self.direction == "down" and self.y > 850:
            self.kill()
        elif self.direction == "up" and self.y < -150:
            self.kill()


def reset_vehicles() -> None:
    """Reset simulation variables, vehicles lists, turned lists, and sprite group."""
    simulation.empty()
    for direction in vehicles:
        for lane in (0, 1, 2):
            vehicles[direction][lane].clear()
        vehicles[direction]["crossed"] = 0

        # Reset turned and not turned lists
        for lane in (1, 2):
            vehiclesTurned[direction][lane].clear()
            vehiclesNotTurned[direction][lane].clear()

    # Reset position offsets back to defaults
    global x, y, currentGreen, currentYellow
    x = {
        "right": [0, 0, 0],
        "down": [755, 727, 697],
        "left": [1400, 1400, 1400],
        "up": [602, 627, 657],
    }
    y = {
        "right": [348, 370, 398],
        "down": [0, 0, 0],
        "left": [498, 466, 436],
        "up": [800, 800, 800],
    }
    currentGreen = 0
    currentYellow = 0


def set_signal_state(current_green: int, current_yellow: int) -> None:
    global currentGreen, currentYellow
    currentGreen = current_green
    currentYellow = current_yellow


def reset_direction_stops(direction_index: int) -> None:
    direction = directionNumbers[direction_index]
    for lane in range(3):
        for vehicle in vehicles[direction][lane]:
            vehicle.stop = defaultStop[direction]


def iter_vehicles() -> Iterable[Vehicle]:
    return simulation.sprites()


def generate_vehicle() -> Vehicle:
    vehicle_type = random.choice(allowedVehicleTypesList)
    lane_number = random.randint(1, 2)
    will_turn = 1 if random.randint(0, 99) < 40 else 0
    direction_number = random.choices([0, 1, 2, 3], weights=[6, 2, 1, 1])[0]
    return Vehicle(
        lane_number,
        vehicleTypes[vehicle_type],
        direction_number,
        directionNumbers[direction_number],
        will_turn,
    )


def get_crossed_counts() -> Dict[int, int]:
    return {
        direction: vehicles[directionNumbers[direction]]["crossed"]
        for direction in directionNumbers
    }


def show_stats(time_elapsed: float) -> None:
    total_vehicles = 0
    print("Direction-wise Vehicle Counts")
    for direction in range(4):
        crossed = vehicles[directionNumbers[direction]]["crossed"]
        print(f"{directionLabels[direction]}: {crossed}")
        total_vehicles += crossed
    print(f"Total vehicles passed: {total_vehicles}")
    print(f"Total time: {time_elapsed:.1f}")
