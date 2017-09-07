import pandas as pd


class Transform(object):
    """object to describe transform on dataframe
    keeps track of which variables are needed for transformation
    can also normalize
    """

    def __init__(self, name, id_, x_var, rel_vars):
        self._name = name
        self._id = id_
        self._x = x_var
        # need _rel_vars to be iterable
        self.variables = rel_vars
        self._validate()

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def variables(self):
        return self._rel_vars

    @variables.setter
    def variables(self, values):
        if isinstance(values, list) or isinstance(values, tuple):
            self._rel_vars = values
        else:
            self._rel_vars = [values]

    def _validate(self):
        """function validate relevent variables"""
        return True

    def _apply(self, df):
        """apply the transformation to dataframe df"""
        raise NotImplementedError

    def _normalize(self, y):
        min_ = min(y)
        max_ = max(y)
        print(min_, max_)
        return (y - min_) / (max_ - min_)

    def __call__(self, df, normalize, smooth):
        if smooth:
            df_ = df.set_index('date').rolling(
                25, win_type='blackman', center=True).mean().reset_index().dropna()
        else:
            df_ = df.dropna()
        x, y = self._apply(df_)
        if normalize:
            # normalize the function to (y-min)/(max-min)
            y = self._normalize(y)
        assert len(x) == len(y), 'not same length'
        return x, y


class AccessTransform(Transform):
    """transform where application is accessing a single series of dataframe"""

    def _validate(self):
        return len(self._rel_vars) == 1

    def _apply(self, df):
        return df[self._x].values, df[self._rel_vars[0]].values


class DifferenceTransform(Transform):
    """transform where two fields are subtracted
    rel_vars is list of len 2 where second is subtracted
    from first
    """

    def _validate(self):
        return len(self._rel_vars) == 2

    def _apply(self, df):
        ans = df[self._rel_vars[0]] - df[self._rel_vars[1]]
        return df[self._x].values, ans.values


if __name__ == '__main__':

    a = AccessTransform('testing', 'id', 'x', ['y'])
    b = DifferenceTransform('test', 'id', 'x', ['y', 'z'])
    df = pd.DataFrame({'x': [1, 2, 3, 4, 5], 'y': [
                      5, 4, 2, 1, 5], 'z': [3, 2, 5, 6, 7]})
    print(a(df))
    print(b(df))
