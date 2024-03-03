from inspect import getmembers, isclass, isabstract
import factory.calculation.calculations as calculations
from factory.calculation.calculation_abs import CalculationsAbs


class CalculationFactory:
    def __init__(self, student_id, calculation, **kwargs):
        self.calculation = calculation
        self.student_id = student_id
        self.kwargs = kwargs
        self.all_calculations = {}
        self.load_calculations()

    def load_calculations(self):
        calculation_classes = getmembers(calculations, lambda m: isclass(m) and not isabstract(m))
        for name, _type in calculation_classes:
            if isclass(_type) and issubclass(_type, CalculationsAbs):
                self.all_calculations.update({name: _type})

    def create_instance(self):
        if self.calculation in self.all_calculations:
            return self.all_calculations[self.calculation](self.student_id, **self.kwargs)
        else:
            raise NotImplementedError
