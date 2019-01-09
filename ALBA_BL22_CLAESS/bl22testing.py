from sardana.macroserver.macro import Macro


class test_pmac_encoder(Macro):
    def run(self):
        for start, end in zip(range(2400, 62400, 4000),
                              range(6400, 66400, 4000)):
            macro = 'qExafs {0} {1} 4000 0.01 True False'.format(start, end)
            self.execMacro(macro)
        for start, end in zip(range(62400, 2400, -4000),
                              range(58400, 0, -4000)):
            macro = 'qExafs {0} {1} 4000 0.01 True False'.format(start, end)
            self.execMacro(macro)

