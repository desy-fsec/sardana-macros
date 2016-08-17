from sardana.macroserver.macro import imacro, Type


@imacro()
def ask_number_of_points(self):
    """
    Category: Examples

    Interactive macro that asks user for the number of points
    """
    nb_points = self.input("How many points?", data_type=Type.Integer)
    self.output("You selected %d points", nb_points)


@imacro()
def ask_for_moveable(self):
    """
    Category: Examples

    Interactive macro that asks user for a motor
    """
    moveable = self.input("Which moveable?", data_type=Type.Moveable)
    self.output("You selected %s which is at %f", moveable, moveable.getPosition())


@imacro()
def ask_for_car_brand(self):
    """
    Category: Examples

    Interactive macro that asks user for a car brand
    """
    car_brands = "Mazda", "Citroen", "Renault"
    car_brand = self.input("Which car brand?", data_type=car_brands)
    self.output("You selected %s", car_brand)


@imacro()
def ask_for_multiple_car_brands(self):
    """
    Category: Examples

    Interactive macro that asks user for several car brands
    """
    car_brands = "Mazda", "Citroen", "Renault", "Ferrari", "Porche", "Skoda"
    car_brands = self.input("Which car brand(s)?", data_type=car_brands,
                            allow_multiple=True)
    self.output("You selected %s", ", ".join(car_brands))


