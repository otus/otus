class MetricList:
    def __init__(self, modules, initn):
        self.metrics = []
        for module in modules:
            self.metrics.append([initn] * module.size())

    def copyZero(self):
        newmet = []
        for i in range(0, len(self.metrics)):
            newmet.append([0] * len(self.metrics[i]))
        return newmet

    def add(self, met):
        for i in range(0, len(self.metrics)):
            for j in range(0, len(self.metrics[i])):
                self.metrics[i][j] += met.get(i, j)

    def calcRate(self, meta, metb, intv):
        for i in range(0, len(self.metrics)):
            for j in range(0, len(self.metrics[i])):
                self.metrics[i][j] = float(metb.get(i,j) - meta.get(i, j)) / intv

    def setZero(self):
        for i in range(0, len(self.metrics)):
            for j in range(0, len(self.metrics[i])):
                self.metrics[i][j] = 0

    def getRow(self, i):
        return self.metrics[i]

    def set(self, i, j, x):
        self.metrics[i][j] = x

    def get(self, i, j):
        return self.metrics[i][j]
