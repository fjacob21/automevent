class KeyboardEvent():

    def __init__(self, vendor='', device='', name='', key=''):
        self._vendor = vendor
        self._device = device
        self._name = name
        self._key = key

    @property
    def vendor(self):
        return self._vendor

    @vendor.setter
    def vendor(self, vendor):
        self._vendor = vendor

    @property
    def device(self):
        return self._device

    @device.setter
    def device(self, device):
        self._device = device

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, key):
        self._key = key

    @property
    def id(self):
        evid = '{v}.{p}.{n}.{k}'.format(v=self.vendor, p=self.device, n=self.name, k=self.key)
        return evid
