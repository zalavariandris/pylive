import image_utils as utils


class Pipeline:
    def __init__(self, operator=None, *args, **kwargs):
        self._operators = []
        if operator is not None:
            self.append(operator, *args, **kwargs)

    def append(self, operator, *args, **kwargs):
        self._operators.append( (operator, args, kwargs) )
        return self

    def __call__(self, operator, *args, **kwds):
        return self.append(operator, *args, **kwds)
    
    def run(self):
        f, args, kwargs = self._operators[0]
        current_value = f(*args, **kwargs)
        for operator, args, kwargs in self._operators:
            args = (current_value, ) + args
            current_value = operator(*args, **kwargs)
        return current_value
    
if __name__ == "__main__":
    build_checkerboard = Pipeline()\
        .append(utils.checkerboard, size=8, squares=8)\

    pipeline = Pipeline().append(
            utils.read_image,
            path="PATH/TO/YOUR/IMAGE.jpg"
        ).append(
            utils.merge_over,
            B=build_checkerboard
        ).append(
            utils.add_grain, 
            radius=5)

    pipeline = Pipeline(
        utils.read_image,
        path="PATH/TO/YOUR/IMAGE.jpg"
    ).append(
        utils.merge_over,
        B=Pipeline(
            utils.checkerboard, size=8, squares=8
        )
    ).append(
        utils.add_grain, 
        radius=5)

    result = pipeline.run()
    print(result.shape)