from typing import *


class bilist:
    def __init__(self, iterable=()):
        self.data = list(iterable)
        self.index_map = {v: i for i, v in enumerate(self.data)}

    def append(self, item):
        self.index_map[item] = len(self.data)
        self.data.append(item)

    def remove(self, item):
        idx = self.index_map.pop(item)
        self.data.pop(idx)
        # Update indices
        for i in range(idx, len(self.data)):
            self.index_map[self.data[i]] = i

    def insert(self, index, item):
        self.data.insert(index, item)
        self.index_map[item] = index
        for i in range(index + 1, len(self.data)):
            self.index_map[self.data[i]] = i

    def pop(self, index=-1):
        item = self.data.pop(index)
        del self.index_map[item]
        for i in range(index, len(self.data)):
            self.index_map[self.data[i]] = i
        return item

    def index(self, item):
        return self.index_map[item]  # O(1) index lookup

    def __getitem__(self, index):
        return self.data[index]

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return repr(self.data)
