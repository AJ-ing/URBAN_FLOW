from src.controllers.fixed_controller import FixedTimeController

c = FixedTimeController(5, 2)

for i in range(20):
    print(c.get_signal({'N':1,'S':1,'E':1,'W':1}))
    c.tick(1)

